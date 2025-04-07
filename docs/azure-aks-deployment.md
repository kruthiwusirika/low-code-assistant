# Azure AKS Deployment Guide for Low-Code Assistant

This guide explains how to deploy the Low-Code Assistant to Azure Kubernetes Service (AKS).

## Prerequisites

- Azure CLI installed and configured
- kubectl installed
- Helm 3 installed
- Docker installed
- Azure subscription with sufficient permissions

## Step 1: Set Up Azure Resources and Variables

```bash
# Set variables
export RESOURCE_GROUP="low-code-assistant-rg"
export LOCATION="eastus"
export AKS_CLUSTER="low-code-assistant-aks"
export ACR_NAME="lowcodeassistantacr"  # Must be globally unique
export NAMESPACE="low-code-assistant"

# Login to Azure
az login

# Create a resource group
az group create --name $RESOURCE_GROUP --location $LOCATION
```

## Step 2: Create Azure Container Registry (ACR)

```bash
# Create ACR
az acr create \
  --resource-group $RESOURCE_GROUP \
  --name $ACR_NAME \
  --sku Standard \
  --admin-enabled true

# Get ACR login credentials
export ACR_USERNAME=$(az acr credential show -n $ACR_NAME --query username -o tsv)
export ACR_PASSWORD=$(az acr credential show -n $ACR_NAME --query passwords[0].value -o tsv)
```

## Step 3: Create AKS Cluster

```bash
# Create AKS cluster with 2 nodes
az aks create \
  --resource-group $RESOURCE_GROUP \
  --name $AKS_CLUSTER \
  --node-count 2 \
  --enable-cluster-autoscaler \
  --min-count 1 \
  --max-count 5 \
  --node-vm-size Standard_DS2_v2 \
  --network-plugin azure \
  --generate-ssh-keys \
  --attach-acr $ACR_NAME \
  --enable-addons monitoring \
  --enable-msi-auth-for-monitoring true

# Get AKS credentials
az aks get-credentials --resource-group $RESOURCE_GROUP --name $AKS_CLUSTER

# Verify connection
kubectl get nodes
```

## Step 4: Build and Push Docker Image to ACR

```bash
# Login to ACR
az acr login --name $ACR_NAME

# Build and tag the image
export ACR_LOGINSERVER=$(az acr show --name $ACR_NAME --query loginServer --output tsv)
docker build -t ${ACR_LOGINSERVER}/low-code-assistant:latest .

# Push to ACR
docker push ${ACR_LOGINSERVER}/low-code-assistant:latest
```

## Step 5: Install Required Components

### Install NGINX Ingress Controller

```bash
# Add the ingress-nginx repository
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update

# Create namespace for ingress
kubectl create namespace ingress-nginx

# Install the ingress controller
helm install nginx-ingress ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --set controller.replicaCount=2 \
  --set controller.nodeSelector."kubernetes\.io/os"=linux \
  --set defaultBackend.nodeSelector."kubernetes\.io/os"=linux
```

### Install Cert-Manager for TLS certificates

```bash
# Add the Jetstack Helm repository
helm repo add jetstack https://charts.jetstack.io
helm repo update

# Install cert-manager
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --set installCRDs=true

# Create a ClusterIssuer for Let's Encrypt
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

## Step 6: Install Monitoring and Logging Solutions

Azure Monitor for containers is automatically enabled when you create the AKS cluster with the monitoring add-on. Let's enhance it with Prometheus and Grafana:

```bash
# Add the Prometheus community Helm repo
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install Prometheus stack
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set grafana.adminPassword=admin-password-change-me
```

## Step 7: Set up Azure Key Vault for Secrets Management

```bash
# Create Azure Key Vault
export KEYVAULT_NAME="low-code-assistant-kv"
az keyvault create \
  --name $KEYVAULT_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --enable-rbac-authorization true

# Add OpenAI API key to Key Vault
az keyvault secret set \
  --vault-name $KEYVAULT_NAME \
  --name "openai-api-key" \
  --value "your-openai-api-key"

# Set up AKS with Key Vault using CSI driver
az aks enable-addons \
  --addons azure-keyvault-secrets-provider \
  --name $AKS_CLUSTER \
  --resource-group $RESOURCE_GROUP

# Get AKS identity
export IDENTITY_CLIENT_ID=$(az aks show -g $RESOURCE_GROUP -n $AKS_CLUSTER --query "addonProfiles.azureKeyvaultSecretsProvider.identity.clientId" -o tsv)

# Grant the identity access to Key Vault secrets
az role assignment create \
  --role "Key Vault Secrets User" \
  --assignee $IDENTITY_CLIENT_ID \
  --scope $(az keyvault show --name $KEYVAULT_NAME --query id -o tsv)

# Create a SecretProviderClass for Key Vault integration
cat <<EOF | kubectl apply -f -
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata:
  name: azure-kvs-provider
  namespace: $NAMESPACE
spec:
  provider: azure
  parameters:
    usePodIdentity: "false"
    useVMManagedIdentity: "true"
    userAssignedIdentityID: $IDENTITY_CLIENT_ID
    keyvaultName: $KEYVAULT_NAME
    cloudName: ""
    objects: |
      array:
        - |
          objectName: openai-api-key
          objectType: secret
          objectVersion: ""
    tenantId: $(az account show --query tenantId -o tsv)
EOF
```

## Step 8: Deploy Low-Code Assistant using Helm

```bash
# Create a values file for your deployment
cat <<EOF > aks-values.yaml
image:
  repository: ${ACR_LOGINSERVER}/low-code-assistant
  tag: latest
  pullPolicy: Always

serviceAccount:
  create: true
  name: low-code-assistant
  annotations:
    azure.workload.identity/client-id: $IDENTITY_CLIENT_ID

ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
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
  storageClass: "managed-premium"  # Azure managed premium storage
  size: 10Gi

resources:
  limits:
    cpu: 1
    memory: 2Gi
  requests:
    cpu: 500m
    memory: 1Gi

environment: production

# We'll use Azure Key Vault integration instead of this value
openaiApiKey: ""

# Additional volume mounts for KeyVault secrets
extraVolumeMounts:
  - name: azure-keyvault
    mountPath: "/mnt/secrets-store"
    readOnly: true

extraVolumes:
  - name: azure-keyvault
    csi:
      driver: secrets-store.csi.k8s.io
      readOnly: true
      volumeAttributes:
        secretProviderClass: "azure-kvs-provider"

# Set environment variables from mounted secrets
extraEnv:
  - name: OPENAI_API_KEY
    valueFrom:
      secretKeyRef:
        name: openai-api-key
        key: openai-api-key
EOF

# Install the Helm chart
helm install low-code-assistant ./helm/low-code-assistant \
  --namespace $NAMESPACE \
  --create-namespace \
  --values aks-values.yaml
```

## Step 9: Set up Traffic Management and DNS

```bash
# Get the public IP address of the Ingress controller
export INGRESS_IP=$(kubectl get service nginx-ingress-ingress-nginx-controller -n ingress-nginx -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Configure your DNS provider to point your domain to this IP address
echo "Configure your DNS: low-code-assistant.example.com -> $INGRESS_IP"
```

## Step 10: Configure Azure Database for MySQL Flexible Server (Optional)

If you prefer to use a managed database service instead of SQLite:

```bash
# Create an Azure Database for MySQL Flexible Server
export MYSQL_SERVER_NAME="low-code-assistant-db"
export MYSQL_ADMIN_USER="dbadmin"
export MYSQL_ADMIN_PASSWORD="ComplexPassword123!"

az mysql flexible-server create \
  --resource-group $RESOURCE_GROUP \
  --name $MYSQL_SERVER_NAME \
  --location $LOCATION \
  --admin-user $MYSQL_ADMIN_USER \
  --admin-password $MYSQL_ADMIN_PASSWORD \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --storage-size 32 \
  --version 8.0.21

# Create a database
az mysql flexible-server db create \
  --resource-group $RESOURCE_GROUP \
  --server-name $MYSQL_SERVER_NAME \
  --database-name low_code_assistant

# Configure firewall rule to allow AKS subnet
export AKS_SUBNET_ID=$(az aks show --resource-group $RESOURCE_GROUP --name $AKS_CLUSTER --query "agentPoolProfiles[0].vnetSubnetId" -o tsv)
export SUBNET_ADDRESS_PREFIX=$(az network vnet subnet show --ids $AKS_SUBNET_ID --query addressPrefix -o tsv)

az mysql flexible-server firewall-rule create \
  --resource-group $RESOURCE_GROUP \
  --name $MYSQL_SERVER_NAME \
  --rule-name "allow-aks-subnet" \
  --start-ip-address ${SUBNET_ADDRESS_PREFIX%%/*} \
  --end-ip-address ${SUBNET_ADDRESS_PREFIX%%/*}
```

## Step 11: Set up Backup and Disaster Recovery

```bash
# Enable Azure Backup for AKS
az feature register --namespace Microsoft.ContainerService --name AKSAzureBackup
az provider register -n Microsoft.ContainerService

# Create Azure Backup vault
export BACKUP_VAULT_NAME="low-code-assistant-backup"
az backup vault create \
  --name $BACKUP_VAULT_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION

# Backup policy
az backup policy create \
  --name aks-backup-policy \
  --vault-name $BACKUP_VAULT_NAME \
  --resource-group $RESOURCE_GROUP \
  --policy '{"backupManagementType":"AzureStorage","schedulePolicy":{"schedulePolicyType":"SimpleSchedulePolicy","scheduleRunFrequency":"Daily","scheduleRunTimes":["2022-01-01T00:00:00Z"],"scheduleRunDays":null},"retentionPolicy":{"retentionPolicyType":"LongTermRetentionPolicy","dailySchedule":{"retentionTimes":["2022-01-01T00:00:00Z"],"retentionDuration":{"count":30,"durationType":"Days"}}}}'
```

## Additional Considerations for Production

1. **Network Security**:
   - Implement a private AKS cluster for enhanced security
   - Use Azure Network Security Groups to control traffic
   - Consider Azure Firewall for advanced network protection

   ```bash
   # Create a private AKS cluster
   az aks create \
     --resource-group $RESOURCE_GROUP \
     --name $AKS_CLUSTER \
     --load-balancer-sku standard \
     --enable-private-cluster \
     --network-plugin azure \
     --vnet-subnet-id $SUBNET_ID \
     --docker-bridge-address 172.17.0.1/16 \
     --dns-service-ip 10.2.0.10 \
     --service-cidr 10.2.0.0/16
   ```

2. **Azure AD Integration**:
   - Integrate AKS with Azure AD for authentication
   - Implement RBAC for fine-grained access control
   - Use Azure AD Pod Identity for managed identities

3. **Security Center**:
   - Enable Azure Security Center for continuous security assessment
   - Implement Azure Policy for Kubernetes
   - Use Azure Defender for Kubernetes

4. **Scaling**:
   - Configure horizontal pod autoscaler for workloads
   - Use node pools for different workload types
   - Implement Azure traffic manager for global load balancing

5. **Azure Front Door**:
   - Implement Azure Front Door for CDN and WAF capabilities
   - Configure WAF policies to protect against web threats
   - Use Azure DDoS Protection Standard for DDoS mitigation

6. **Compliance and Governance**:
   - Implement Azure Policy for Kubernetes for governance
   - Set up Azure Monitor for compliance reporting
   - Use Azure Blueprints for governance templates

7. **Cost Management**:
   - Use Azure Cost Management to monitor and optimize costs
   - Implement autoscaling to optimize resource utilization
   - Consider using Spot VMs for non-critical workloads

## Troubleshooting

If you encounter issues, check:
1. Pods status: `kubectl get pods -n $NAMESPACE`
2. Logs: `kubectl logs -n $NAMESPACE deployment/low-code-assistant`
3. Azure Monitor: Check logs and metrics in Azure Portal
4. Events: `kubectl get events -n $NAMESPACE`
5. Service and ingress status: `kubectl get svc,ing -n $NAMESPACE`
