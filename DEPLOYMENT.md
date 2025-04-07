# Low-Code Assistant Deployment Guide

This document outlines how to deploy the Low-Code Assistant using Docker and Kubernetes.

## Docker Containerization

The application has been containerized using Docker to ensure consistent development and deployment environments.

### Building the Docker Image

```bash
docker build -t low-code-assistant:latest .
```

### Running the Docker Container Locally

```bash
docker run -p 8501:8501 -e OPENAI_API_KEY=your_api_key_here low-code-assistant:latest
```

Access the application at http://localhost:8501

## Kubernetes Deployment

The application is designed to run in Kubernetes clusters using the manifests provided in the `k8s` directory.

### Components

1. **Namespace** - Isolates the application resources
2. **Deployment** - Manages the application Pods with scaling and update strategies
3. **Service** - Exposes the application within the cluster
4. **Ingress** - Routes external traffic to the service
5. **ConfigMap** - Stores non-sensitive configuration parameters
6. **Secret** - Securely stores sensitive information like API keys

### Manual Deployment

1. Create the namespace:
   ```bash
   kubectl apply -f k8s/namespace.yaml
   ```

2. Apply the ConfigMap:
   ```bash
   kubectl apply -f k8s/configmap.yaml
   ```

3. Create the Secret with your API key (replace YOUR_API_KEY with your actual API key):
   ```bash
   kubectl create secret generic low-code-assistant-secrets \
     --namespace=low-code-assistant \
     --from-literal=OPENAI_API_KEY=YOUR_API_KEY
   ```

4. Deploy the application:
   ```bash
   # Modify the k8s/deployment.yaml file to use your image
   kubectl apply -f k8s/deployment.yaml
   ```

5. Create the Service:
   ```bash
   kubectl apply -f k8s/service.yaml
   ```

6. Apply the Ingress (update the host if necessary):
   ```bash
   kubectl apply -f k8s/ingress.yaml
   ```

### CI/CD Pipeline

The repository includes a `.gitlab-ci.yml` file that defines a complete CI/CD pipeline:

1. **Test Stage** - Runs automated tests
2. **Build Stage** - Builds and tags Docker images, then pushes them to a registry
3. **Deploy Stage** - Deploys the application to Kubernetes

#### Requirements for CI/CD

- A GitLab repository with CI/CD enabled
- A Kubernetes cluster configured in GitLab
- The following CI/CD variables set in GitLab:
  - `KUBE_CONTEXT`: Kubernetes context name
  - `OPENAI_API_KEY_BASE64`: Base64-encoded OpenAI API key

## Scaling and High Availability

The Kubernetes deployment is configured for high availability:

- Multiple replicas (2 by default)
- Rolling update strategy (zero downtime deployments)
- Resource limits and requests
- Readiness and liveness probes
- Horizontal Pod Autoscaler (can be added as needed)

## Security Considerations

- The Docker container runs as a non-root user (UID 1000)
- Sensitive data is stored in Kubernetes secrets
- TLS is configured through the Ingress
- Resource limits prevent denial-of-service scenarios

## Monitoring

The deployment is configured with Prometheus annotations for metrics scraping. Add additional monitoring as needed:

- Prometheus for metrics collection
- Grafana for visualization
- EFK stack (Elasticsearch, Fluentd, Kibana) for logging

## Production Readiness Checklist

- [ ] Configure persistent storage for templates if needed
- [ ] Set up proper DNS for your Ingress host
- [ ] Configure TLS certificates (using cert-manager)
- [ ] Implement proper secrets management (Vault, AWS Secrets Manager, etc.)
- [ ] Set up monitoring and alerting
- [ ] Configure backup and restore procedures
- [ ] Implement proper logging strategy
