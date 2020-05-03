# Kube2Allow

Little helper to guess required linux capabilities for pods in your Kubernetes cluster.

## Install

```sh
kubectl apply -f ds.yaml
```

## Usage

Once installed, the application will create configmaps for each containers in the cluster, named 
`k2a-${POD_NAME}-${CONTAINER_NAME}` in the pod namespace.

```sh
# Get all configmaps
kubectl get cm --all-namespaces -l 'k8s-app=kube2allow'

# Delete generated configmaps
kubectl delete cm --all-namespaces -l 'k8s-app=kube2allow'

# Uninstall kube2allow
kubectl delete -f ds.yaml
```

### Generate syscall <-> capabilities mapping

The mapping is extracted from referenced capabilities in the `man 2` page.
You can generate `app/caps_mapping.json` with this command:

```sh
make app/caps_mapping.json
```

You can either rebuild the image to embed this file, or mount it as a volume on `/caps_mapping.json` in the container.

## Caveats

- This application guesses the capabilities by trapping system calls, but there is no direct mapping
 between syscall and required caps. Thus, it is done by parsing the `man` page, but this can lead to 
 a broader set of capabilities than the process really requires.

- syscalls are detected at runtime, but it can happen that a container only requires capabilities during 
 initialization. In order to ensure all capabilities have been scraped, you can restart the pods once 
 `kube2allow` is installed.
