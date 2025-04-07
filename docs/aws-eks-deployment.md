# AWS EKS Deployment Guide for Low-Code Assistant

This guide explains how to deploy the Low-Code Assistant to Amazon Elastic Kubernetes Service (EKS).

## Prerequisites

- AWS CLI installed and configured with appropriate permissions
- kubectl installed
- Helm 3 installed
- eksctl installed (for cluster creation)
- Docker installed (for building images)
- AWS ECR repository for storing your Docker images

## Step 1: Create EKS Cluster

```bash
# Create an EKS cluster with node group
eksctl create cluster \
  --name low-code-assistant \
  --version 1.26 \
  --region us-west-2 \
  --nodegroup-name standard-nodes \
  --node-type t3.medium \
  --nodes 2 \
  --nodes-min 1 \
  --nodes-max 4 \
  --with-oidc \
  --managed
```

## Step 2: Configure kubectl

```bash
# Update kubeconfig to connect to the new cluster
aws eks update-kubeconfig --name low-code-assistant --region us-west-2
```

## Step 3: Set up ECR Repository

```bash
# Create ECR repository for your Docker images
aws ecr create-repository --repository-name low-code-assistant

# Get the repository URI
export ECR_REPOSITORY=$(aws ecr describe-repositories --repository-names low-code-assistant --query 'repositories[0].repositoryUri' --output text)
```

## Step 4: Build and Push Docker Image to ECR

```bash
# Log in to ECR
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin $ECR_REPOSITORY

# Build the Docker image
docker build -t $ECR_REPOSITORY:latest .

# Push the image to ECR
docker push $ECR_REPOSITORY:latest
```

## Step 5: Install Required Components

### Install NGINX Ingress Controller

```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
helm install nginx-ingress ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace \
  --set controller.publishService.enabled=true
```

### Install cert-manager for SSL certificates

```bash
helm repo add jetstack https://charts.jetstack.io
helm repo update
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --set installCRDs=true
```

### Create a ClusterIssuer for Let's Encrypt

```bash
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

## Step 6: Install Monitoring Stack (Prometheus & Grafana)

```bash
# Add Prometheus Helm repository
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install Prometheus Stack (includes Grafana)
helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set grafana.enabled=true \
  --set grafana.adminPassword=admin-password-change-me
```

## Step 7: Install EFK Stack for Logging

```bash
# Add Elastic Helm repository
helm repo add elastic https://helm.elastic.co
helm repo update

# Install Elasticsearch
helm install elasticsearch elastic/elasticsearch \
  --namespace logging \
  --create-namespace \
  --set replicas=2 \
  --set minimumMasterNodes=1

# Install Kibana
helm install kibana elastic/kibana \
  --namespace logging

# Install Fluentd
helm repo add fluent https://fluent.github.io/helm-charts
helm install fluentd fluent/fluentd \
  --namespace logging \
  --set elasticsearch.host=elasticsearch-master
```

## Step 8: Deploy Low-Code Assistant using Helm

```bash
# Create a values file for your deployment
cat <<EOF > eks-values.yaml
image:
  repository: $ECR_REPOSITORY
  tag: latest
  pullPolicy: Always

ingress:
  enabled: true
  hosts:
    - host: low-code-assistant.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: low-code-assistant-tls
      hosts:
        - low-code-assistant.example.com

persistence:
  enabled: true
  storageClass: "gp2"  # AWS EBS storage class
  size: 10Gi

# Configure additional settings for production
resources:
  limits:
    cpu: 1
    memory: 2Gi
  requests:
    cpu: 500m
    memory: 1Gi

# Set environment-specific settings
environment: production

# Secure API key using AWS Secrets Manager (preferred approach)
# Here using placeholder for demonstration
openaiApiKey: "your-base64-encoded-api-key"
EOF

# Install the Helm chart
helm install low-code-assistant ./helm/low-code-assistant \
  --namespace low-code-assistant \
  --create-namespace \
  --values eks-values.yaml
```

## Step 9: Set up AWS Load Balancer for Ingress

```bash
# Get the Load Balancer address
export LB_ADDRESS=$(kubectl get svc nginx-ingress-ingress-nginx-controller -n ingress-nginx -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

# Configure your DNS provider to point low-code-assistant.example.com to the LB_ADDRESS
echo "Configure your DNS: low-code-assistant.example.com -> $LB_ADDRESS"
```

## Step 10: Configure AWS IAM for EKS Service Account (IRSA)

```bash
# Create an IAM policy for S3 access (if needed for backups)
aws iam create-policy \
  --policy-name LowCodeAssistantS3Policy \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ],
        "Resource": [
          "arn:aws:s3:::low-code-assistant-backups/*",
          "arn:aws:s3:::low-code-assistant-backups"
        ]
      }
    ]
  }'

# Create an IAM role and associate it with the service account
eksctl create iamserviceaccount \
  --name low-code-assistant \
  --namespace low-code-assistant \
  --cluster low-code-assistant \
  --attach-policy-arn arn:aws:iam::AWS_ACCOUNT_ID:policy/LowCodeAssistantS3Policy \
  --approve
```

## Step 11: Set up External Secrets Operator for API Key Management

```bash
# Install External Secrets Operator
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets external-secrets/external-secrets \
  --namespace external-secrets \
  --create-namespace

# Create AWS Secret Manager secret for OpenAI API Key
aws secretsmanager create-secret \
  --name low-code-assistant/openai-api-key \
  --secret-string '{"OPENAI_API_KEY":"your-actual-api-key"}'

# Create SecretStore resource
cat <<EOF | kubectl apply -f -
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: aws-secretsmanager
  namespace: low-code-assistant
spec:
  provider:
    aws:
      service: SecretsManager
      region: us-west-2
      auth:
        jwt:
          serviceAccountRef:
            name: low-code-assistant
EOF

# Create ExternalSecret resource
cat <<EOF | kubectl apply -f -
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: openai-api-key
  namespace: low-code-assistant
spec:
  refreshInterval: "15m"
  secretStoreRef:
    name: aws-secretsmanager
    kind: SecretStore
  target:
    name: low-code-assistant-secrets
    creationPolicy: Owner
  data:
  - secretKey: OPENAI_API_KEY
    remoteRef:
      key: low-code-assistant/openai-api-key
      property: OPENAI_API_KEY
EOF
```

## Step 12: Set up Backup Solution with Velero

```bash
# Install Velero for backup and restore
helm repo add vmware-tanzu https://vmware-tanzu.github.io/helm-charts
helm install velero vmware-tanzu/velero \
  --namespace velero \
  --create-namespace \
  --set configuration.provider=aws \
  --set-file credentials.secretContents.cloud=./credentials-velero \
  --set configuration.backupStorageLocation.name=aws \
  --set configuration.backupStorageLocation.bucket=low-code-assistant-backups \
  --set configuration.backupStorageLocation.config.region=us-west-2 \
  --set configuration.volumeSnapshotLocation.name=aws \
  --set configuration.volumeSnapshotLocation.config.region=us-west-2 \
  --set initContainers[0].name=velero-plugin-for-aws \
  --set initContainers[0].image=velero/velero-plugin-for-aws:v1.5.0 \
  --set initContainers[0].volumeMounts[0].mountPath=/target \
  --set initContainers[0].volumeMounts[0].name=plugins

# Create a backup schedule
kubectl create -f - <<EOF
apiVersion: velero.io/v1
kind: Schedule
metadata:
  name: low-code-assistant-daily-backup
  namespace: velero
spec:
  schedule: "0 1 * * *"
  template:
    includedNamespaces:
    - low-code-assistant
    ttl: 720h
EOF
```

## Additional Considerations for Production

1. **Configure AWS WAF** with your Application Load Balancer to protect against common web vulnerabilities.
2. **Set up AWS CloudWatch** for additional logging and monitoring.
3. **Implement AWS GuardDuty** for threat detection.
4. **Use AWS Secret Manager** for all sensitive information.
5. **Set up private VPC** for your EKS cluster to restrict public access.
6. **Implement regular security scanning** for your container images.
7. **Consider AWS's Multi-AZ** deployment for high availability.

## Troubleshooting

If you encounter issues, check:
1. Pods status: `kubectl get pods -n low-code-assistant`
2. Logs: `kubectl logs -n low-code-assistant deployment/low-code-assistant`
3. Events: `kubectl get events -n low-code-assistant`
4. Service and ingress status: `kubectl get svc,ing -n low-code-assistant`
