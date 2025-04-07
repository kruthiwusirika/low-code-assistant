# Google Cloud GKE Deployment Guide for Low-Code Assistant

This guide explains how to deploy the Low-Code Assistant to Google Kubernetes Engine (GKE).

## Prerequisites

- Google Cloud SDK (gcloud) installed and configured
- kubectl installed
- Helm 3 installed
- Docker installed
- Access to a Google Cloud project with the necessary permissions

## Step 1: Set Up GCP Project and Enable APIs

```bash
# Set project ID
export PROJECT_ID="your-gcp-project-id"
export REGION="us-central1"
export ZONE="us-central1-a"

# Configure gcloud
gcloud config set project $PROJECT_ID
gcloud config set compute/region $REGION
gcloud config set compute/zone $ZONE

# Enable required APIs
gcloud services enable container.googleapis.com artifactregistry.googleapis.com secretmanager.googleapis.com
```

## Step 2: Create GKE Cluster

```bash
# Create a GKE cluster with recommended settings for production
gcloud container clusters create low-code-assistant \
  --machine-type=e2-standard-2 \
  --num-nodes=2 \
  --disk-size=50 \
  --cluster-version=latest \
  --region=$REGION \
  --release-channel=regular \
  --enable-autorepair \
  --enable-autoupgrade \
  --enable-autoscaling \
  --min-nodes=1 \
  --max-nodes=5 \
  --enable-ip-alias \
  --enable-network-policy \
  --workload-pool=$PROJECT_ID.svc.id.goog
```

## Step 3: Configure kubectl

```bash
# Get credentials for the cluster
gcloud container clusters get-credentials low-code-assistant --region=$REGION

# Verify connection
kubectl get nodes
```

## Step 4: Set up Artifact Registry and Push Docker Image

```bash
# Create Artifact Registry repository
gcloud artifacts repositories create low-code-assistant \
  --repository-format=docker \
  --location=$REGION \
  --description="Low-Code Assistant container images"

# Configure Docker to use Artifact Registry
gcloud auth configure-docker $REGION-docker.pkg.dev

# Build and push Docker image
export REPOSITORY_PATH="$REGION-docker.pkg.dev/$PROJECT_ID/low-code-assistant/low-code-assistant"
docker build -t $REPOSITORY_PATH:latest .
docker push $REPOSITORY_PATH:latest
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

## Step 7: Set up Logging with Google Cloud Operations (formerly Stackdriver)

GKE clusters automatically integrate with Google Cloud Operations for logging and monitoring. To enhance this:

```bash
# Install Google Cloud Operations for GKE
gcloud container clusters update low-code-assistant \
  --region=$REGION \
  --enable-stackdriver-kubernetes \
  --enable-dataplane-v2
```

## Step 8: Deploy Low-Code Assistant using Helm

```bash
# Create a values file for your deployment
cat <<EOF > gke-values.yaml
image:
  repository: $REPOSITORY_PATH
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
  storageClass: "standard"  # GCP standard storage class
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

# Secure API key (placeholder)
openaiApiKey: ""
EOF

# Install the Helm chart
helm install low-code-assistant ./helm/low-code-assistant \
  --namespace low-code-assistant \
  --create-namespace \
  --values gke-values.yaml
```

## Step 9: Use Google Cloud Secret Manager for API Keys

```bash
# Create a secret in Google Cloud Secret Manager
echo -n "your-openai-api-key" | gcloud secrets create openai-api-key --data-file=-

# Create a Kubernetes service account for accessing Secret Manager
kubectl create serviceaccount low-code-assistant-sa --namespace low-code-assistant

# Create a Workload Identity binding
gcloud iam service-accounts create low-code-assistant-gsa

# Bind the service account to the GCP service account
gcloud iam service-accounts add-iam-policy-binding \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:$PROJECT_ID.svc.id.goog[low-code-assistant/low-code-assistant-sa]" \
  low-code-assistant-gsa@$PROJECT_ID.iam.gserviceaccount.com

# Grant access to Secret Manager
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:low-code-assistant-gsa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Annotate the Kubernetes service account
kubectl annotate serviceaccount low-code-assistant-sa \
  --namespace low-code-assistant \
  iam.gke.io/gcp-service-account=low-code-assistant-gsa@$PROJECT_ID.iam.gserviceaccount.com
```

## Step 10: Install External Secrets Operator for Secret Management

```bash
# Install External Secrets Operator
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets external-secrets/external-secrets \
  --namespace external-secrets \
  --create-namespace

# Create SecretStore resource
cat <<EOF | kubectl apply -f -
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: gcp-secretmanager
  namespace: low-code-assistant
spec:
  provider:
    gcpsm:
      projectID: $PROJECT_ID
      auth:
        workloadIdentity:
          serviceAccountRef:
            name: low-code-assistant-sa
            namespace: low-code-assistant
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
    name: gcp-secretmanager
    kind: SecretStore
  target:
    name: low-code-assistant-secrets
    creationPolicy: Owner
  data:
  - secretKey: OPENAI_API_KEY
    remoteRef:
      key: openai-api-key
EOF
```

## Step 11: Set up Backup and Disaster Recovery

```bash
# Install Velero for backup and restore
helm repo add vmware-tanzu https://vmware-tanzu.github.io/helm-charts
helm install velero vmware-tanzu/velero \
  --namespace velero \
  --create-namespace \
  --set-file credentials.secretContents.cloud=./gcp-credentials.json \
  --set configuration.provider=gcp \
  --set backupsEnabled=true \
  --set snapshotsEnabled=true \
  --set deployRestic=true \
  --set configuration.backupStorageLocation.name=gcp \
  --set configuration.backupStorageLocation.bucket=low-code-assistant-backups \
  --set configuration.backupStorageLocation.config.region=$REGION \
  --set configuration.volumeSnapshotLocation.name=gcp \
  --set configuration.volumeSnapshotLocation.config.region=$REGION \
  --set initContainers[0].name=velero-plugin-for-gcp \
  --set initContainers[0].image=velero/velero-plugin-for-gcp:v1.5.0 \
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

## Step 12: Set up External IP and DNS

```bash
# Get the external IP of the load balancer
export EXTERNAL_IP=$(kubectl get svc nginx-ingress-ingress-nginx-controller -n ingress-nginx -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Configure your DNS provider to point low-code-assistant.example.com to the EXTERNAL_IP
echo "Configure your DNS: low-code-assistant.example.com -> $EXTERNAL_IP"
```

## Additional Considerations for Production

1. **Private GKE Cluster**: For enhanced security, consider using a private GKE cluster.
   ```bash
   gcloud container clusters create low-code-assistant \
     --private-cluster \
     --enable-master-authorized-networks \
     --master-authorized-networks=[YOUR_CIDR_RANGES]
   ```

2. **Cloud Armor**: Set up Google Cloud Armor to protect your application from DDoS attacks and other web threats.

3. **Binary Authorization**: Enable Binary Authorization to ensure only trusted container images are deployed.
   ```bash
   gcloud container clusters update low-code-assistant \
     --enable-binauthz
   ```

4. **VPC Service Controls**: Implement VPC Service Controls to protect your GCP resources.

5. **Security Command Center**: Enable Google Security Command Center for continuous security monitoring.

6. **Regional Clusters**: For high availability, use a regional cluster rather than a zonal one.

7. **Cloud CDN**: Consider using Google Cloud CDN in front of your application for faster content delivery.

## Troubleshooting

If you encounter issues, check:
1. Pods status: `kubectl get pods -n low-code-assistant`
2. Logs: `kubectl logs -n low-code-assistant deployment/low-code-assistant`
3. GCP Logs Explorer: Check for any errors in Cloud Logging.
4. Events: `kubectl get events -n low-code-assistant`
5. Service and ingress status: `kubectl get svc,ing -n low-code-assistant`
