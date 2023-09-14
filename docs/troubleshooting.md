# Troubleshooting

## Installation

### Stuck waiting for registration

If the registration doesn't finish within a few minutes of installation,
check whether the `logits-controller` has been deployed:

```sh
kubectl -n logits get pods
```

If the controller Pod is running, check its logs to see if it's having trouble communicating with
the Ops API:

```sh
kubectl -n logits logs logits-controller-...
```

If there is no controller Pod, and only a `logits-gateway` Pod, then check the gateway Pod's logs
to see why it was unable to deploy the controller.

```sh
kubectl -n logits logs logits-gateway-...
```

## Model Deployment

### Stuck pending

If the model you enabled is stuck in a `Pending` state, check whether the Pod was able to schedule.

```sh
kubectl -n logits get pods -l logits.ai/language-model
```

If the Pod is Running but not Ready, check its logs:

```sh
kubectl -n logits logs logits-model-...
```

If the Pod is also stuck `Pending`, check for events from the Kubernetes scheduler:

```sh
kubectl -n logits describe pod logits-model-...
```

If you see a message like `1 Insufficient nvidia.com/gpu`, it could be that the GPU Node is not
advertising its GPU, which could be because driver installation failed.

Find the Node that should have a GPU and check that it has a resource `nvidia.com/gpu: 1` listed
under `Allocatable`:

```sh
kubectl describe node ...
```
