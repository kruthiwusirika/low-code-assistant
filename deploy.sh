#!/bin/bash
set -e

# Default values
REGISTRY_URL=${REGISTRY_URL:-"localhost:5000"}
IMAGE_TAG=${IMAGE_TAG:-"latest"}
NAMESPACE="low-code-assistant"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --registry)
      REGISTRY_URL="$2"
      shift 2
      ;;
    --tag)
      IMAGE_TAG="$2"
      shift 2
      ;;
    --namespace)
      NAMESPACE="$2"
      shift 2
      ;;
    --help)
      echo "Usage: $0 [--registry REGISTRY_URL] [--tag IMAGE_TAG] [--namespace NAMESPACE] [build|push|deploy|all]"
      exit 0
      ;;
    *)
      ACTION="$1"
      shift
      ;;
  esac
done

# Default action is 'all'
ACTION=${ACTION:-"all"}

build_image() {
  echo "Building Docker image: ${REGISTRY_URL}/low-code-assistant:${IMAGE_TAG}"
  docker build -t ${REGISTRY_URL}/low-code-assistant:${IMAGE_TAG} .
}

push_image() {
  echo "Pushing Docker image to registry: ${REGISTRY_URL}/low-code-assistant:${IMAGE_TAG}"
  docker push ${REGISTRY_URL}/low-code-assistant:${IMAGE_TAG}
}

deploy_to_k8s() {
  echo "Deploying to Kubernetes in namespace: ${NAMESPACE}"
  
  # Create temporary directory for processed manifests
  TMP_DIR=$(mktemp -d)
  trap "rm -rf $TMP_DIR" EXIT
  
  # Process Kubernetes manifests with the correct values
  for file in k8s/*.yaml; do
    sed "s|\${REGISTRY_URL}|${REGISTRY_URL}|g; s|\${IMAGE_TAG}|${IMAGE_TAG}|g; s|\${NAMESPACE}|${NAMESPACE}|g" "$file" > "$TMP_DIR/$(basename "$file")"
  done
  
  # Apply the manifests in the correct order
  kubectl apply -f "$TMP_DIR/namespace.yaml"
  kubectl apply -f "$TMP_DIR/configmap.yaml"
  kubectl apply -f "$TMP_DIR/secret.yaml" 2>/dev/null || echo "Secret not found, skipping"
  kubectl apply -f "$TMP_DIR/deployment.yaml"
  kubectl apply -f "$TMP_DIR/service.yaml"
  kubectl apply -f "$TMP_DIR/ingress.yaml"
  
  echo "Deployment completed successfully!"
  echo "The application should be available at: https://low-code-assistant.example.com"
  echo "(You may need to update DNS or your hosts file to point to your cluster)"
}

# Execute requested actions
case $ACTION in
  build)
    build_image
    ;;
  push)
    push_image
    ;;
  deploy)
    deploy_to_k8s
    ;;
  all)
    build_image
    push_image
    deploy_to_k8s
    ;;
  *)
    echo "Unknown action: $ACTION"
    echo "Valid actions are: build, push, deploy, all"
    exit 1
    ;;
esac
