# Architecture

This page describes the internal architecture of the Logits AI platform.

You don't need to understand these implementation details to use the platform, and you should expect
that the details could change without notice.
However, since most of these components run inside your environment, we believe in being as
transparent as possible about how they work.

## Logits Production

These are the systems that run in our own production environment.

### Accounts Dashboard

The [Accounts Dashboard](https://accounts.logits.ai) is where you manage your relationship with
Logits AI, such as signing up for an account, configuring billing, and sharing access with other
members of your organization.

Aside from that, you will use the in-cluster [Console](#console) for all other interaction with the
product. Since the product console runs inside your cluster, it can give you a full view of your own
proprietary data such as fine-tuning datasets.

### Ops API

The Ops API (`https://ops.logits.ai`) is the service that the in-cluster components connect to
in order to receive instructions on what component versions they should be running
(as new releases slowly roll out across customer clusters), and to send redacted logs and metrics.

## In-Cluster Components

These are the key parts of the Logits AI stack that run in the customer's Kubernetes cluster.

### Gateway

The Gateway is the only component that's directly installed by our [Helm chart](../helm/gateway),
as as such it is the only component that we cannot upgrade remotely.
The Gateway will only ever be upgraded when you choose to perform a Helm upgrade.

This is important because the Gateway runs under a Service Account with associated
[RBAC permissions](../helm/gateway/templates/gateway-rbac.yaml) that you grant as part of installing
the chart. Notably, you are not granting us any permissions to modify RBAC resources, so we cannot
acquire any new permissions except by asking you to install a newer Helm chart version.

As its name implies, the Gateway acts as the primary access point between your environment and our
remote operations tooling.

It serves two main functions:

1. It deploys the [Controller](#controller) after asking the [Ops API](#ops-api) what version it
   should run.
1. It serves as a central auditing point for any calls to the Kubernetes API in your cluster,
   as well as for calls to the Ops API from any Logits component (including from the Gateway itself).

The Gateway is the only component that runs under the Service Account to which you granted RBAC
permissions, so all other components can only take authenticated actions via the Gateway,
which will include those actions in its audit log.

In this way, the Gateway defines the trust boundary of what our software could possibly do inside
your environment. Since you control upgrades of the Gateway, you know that this trust boundary
cannot move even as we remotely upgrade other parts of our stack.

### Controller

The Controller deploys and manages the rest of the Logits AI stack by synchronizing Kubernetes state
with various sources of configuration (e.g. from the Console or the API).
It is similar to the controllers that make up a Kubernetes Operator, except that it is not
configured through CRDs.

### Collector

The Collector streams redacted logs from other components and sends them in compressed batches to
the Ops API. All the logs we collect are also visible to you as normal Kubernetes Pod logs, but note
that your Pod logs may contain full, unredacted values that we cannot see.

The Collector also scrapes Prometheus metrics from all our in-cluster components on the
ContainerPort named `metrics` and sends them in compressed batches to the Ops API.

You are welcome to scrape these metrics as well to have your own view into our stack,
but you shouldn't feel that you need to as we are monitoring it remotely.
Also be aware that the set of metrics we expose may change over time without notice as these are not
part of our public API surface.

### Console

The in-cluster Console is the primary web UI for the product. This is where you will configure
things like which models to enable and set autoscaling limits.

### API Server

The API Server exposes the primary public API surface of the Logits AI platform.
This is the service that your application will call to request things like Chat Completions.
The API Server will then route requests by the `model` parameter and load-balance those requests
across the available LLM Servers for that model.

### LLM Servers

Each instance of the LLM Server takes ownership of a single GPU and serves a given model or set of
models (in the case of fractional GPU sharing).

We currently use [vLLM](https://github.com/vllm-project/vllm) as the underlying inference engine,
but this is an implementation detail that may change over time or across different model families.
Like a SaaS, we take it upon ourselves to evaluate and integrate with the best available tools to
achieve the goals of our high-level API.

### Entity DB

The Entity DB is a thin REST API wrapper around a SQLite file stored on a PersistentVolumeClaim.
It allows the Controller, Console, and API Server to collaborate on configuring desired state and
communicating observed states in the cluster.

It is conceptually similar to the way a Kubernetes Operator would use CRDs, except that these
records are not part of our public API surface and we need the ability to update their schemas
without asking for cluster-level permissions.

### Ingress Proxy

The Ingress Proxy is a reverse proxy that sits in front of the Console, API Server, and Entity DB
to provide a single entrypoint that can be exposed over a port-forward, VPN, or internal
load-balancer. In the future, you will have the option to enforce authentication at the
Ingress Proxy so that it will be safe to expose on an external load-balancer if desired.
