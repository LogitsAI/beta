# GPUs on Kubernetes

## Amazon EKS

For Llama 2 7B on EKS, we recommend a minimum instance type of
[g5.2xlarge](https://aws.amazon.com/ec2/instance-types/g5/), which has an NVIDIA A10G.

If you haven't used G5 instances before, you may need to request a
[quota](https://docs.aws.amazon.com/general/latest/gr/aws_service_limits.html) increase for the
`Running On-Demand G and VT instances` item under Service Quotas > Amazon EC2 in the AWS console.
You will need a quota of `8` vCPUs to run a single `g5.2xlarge` instance.

Next, add a node group to your EKS cluster with this instance type.
We recommend using [eksctl](https://eksctl.io/) since it has built-in support for
[configuring the cluster to use GPUs](https://eksctl.io/usage/gpu-support/).

Here is an example `cluster.yaml` that could be used with `eksctl create cluster -f cluster.yaml`:

```yaml
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig

metadata:
  name: dev
  region: us-east-1

nodeGroups:

- name: default-1
  instanceType: t3.medium
  desiredCapacity: 1
  volumeSize: 100

- name: gpu-1
  instanceType: g5.2xlarge
  desiredCapacity: 1
  volumeSize: 100
```

You can then create a `KUBECONFIG` entry for this cluster with:

```sh
aws eks update-kubeconfig --name dev --region us-east-1
```

Note that you will also need to have an EBS driver to provision the PersistentVolumeClaim requested
by our in-cluster components.
A fresh EKS cluster does not come with this driver, which you can install with:

```sh
eksctl utils associate-iam-oidc-provider --region=us-east-1 --cluster=dev --approve

eksctl create iamserviceaccount \
    --name ebs-csi-controller-sa \
    --namespace kube-system \
    --cluster dev \
    --role-name AmazonEKS_EBS_CSI_DriverRole \
    --role-only \
    --attach-policy-arn arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy \
    --approve

eksctl create addon --name aws-ebs-csi-driver \
    --cluster dev \
    --service-account-role-arn $(aws iam get-role --role-name AmazonEKS_EBS_CSI_DriverRole | jq -r '.Role.Arn') \
    --force
```

## Google Kubernetes Engine

For Llama 2 7B on GKE, we recommend a minimum machine type of
[g2-standard-8](https://cloud.google.com/compute/docs/accelerator-optimized-machines#g2-vms),
which has an NVIDIA L4.

Note that the L4 GPU is only available in [certain zones](https://cloud.google.com/compute/docs/gpus/gpu-regions-zones).
You also may need to [request quota](https://cloud.google.com/kubernetes-engine/docs/how-to/gpus#request_quota)
for the metric `compute.googleapis.com/nvidia_l4_gpus` in the region of your choice if you don't
already have at least `1`.

You can [add a GPU node pool](https://cloud.google.com/kubernetes-engine/docs/how-to/gpus#gcloud)
with a machine type of `g2-standard-8` through the Console, CLI, or Terraform.

Be aware that it's important to specify the `--accelerator` flag for the CLI, or to specify the
`guest_accelerator` section in Terraform. Without these options, GKE will appear to successfully
provision the node pool, but the GPUs will not be advertised within Kubernetes.

Finally, unless you're using a very recent version of GKE (v1.27+), you will need to deploy a
DaemonSet to [install NVIDIA drivers](https://cloud.google.com/kubernetes-engine/docs/how-to/gpus#installing_drivers)
on each GPU Node.

Make sure you install the `*-latest.yaml` version of the DaemonSet since the NVIDIA L4 requires the
newer drivers:

```sh
kubectl apply -f https://raw.githubusercontent.com/GoogleCloudPlatform/container-engine-accelerators/master/nvidia-driver-installer/cos/daemonset-preloaded-latest.yaml
```
