# Quickstart: Deploy Semantic Modeling Agent to Azure AI Foundry

This guide walks you through deploying the Power BI Semantic Modeling Agent to Azure AI Foundry in under 15 minutes.

## Prerequisites

Before starting, ensure you have:

- **Azure Subscription** with appropriate permissions:
  - Contributor role on resource group
  - Permission to create managed identities
  - Permission to create role assignments
- **Azure CLI** installed and authenticated (`az login`)
- **Docker** installed and running (for local container builds)
- **Git** installed
- **Terraform** v1.5+ installed (for infrastructure provisioning)
- **Existing Azure AI Foundry Project** (or create one following [these instructions](https://learn.microsoft.com/azure/ai-studio/how-to/create-projects))
- **Fabric Workspace** in dev, staging, or prod environment
- **Azure Container Registry** (or create one in the steps below)

## Step 1: Clone the Repository

```bash
git clone https://github.com/your-org/sm-agent.git
cd sm-agent
git checkout 001-foundry-agent-registration
```

## Step 2: Configure Environment Variables

Create an environment-specific configuration file:

```bash
cp terraform/environments/dev.tfvars.example terraform/environments/dev.tfvars
```

Edit `terraform/environments/dev.tfvars` and fill in your values:

```hcl
# Azure AI Foundry Configuration
foundry_project_id      = "your-foundry-project-guid"
foundry_subscription_id = "your-azure-subscription-guid"
foundry_resource_group  = "rg-foundry-dev"

# Container Registry
acr_name                = "yourregistryname"  # Must be globally unique
acr_resource_group      = "rg-acr-shared"

# Fabric Workspace Access
fabric_workspace_ids    = [
  "workspace-id-1",  # Dev workspace
  "workspace-id-2"   # Additional workspaces if needed
]

# Agent Configuration
agent_name              = "semantic-modeling-agent"
agent_version           = "1.0.0"
environment             = "dev"

# Observability
app_insights_name       = "appi-foundry-dev"
log_analytics_workspace = "log-foundry-dev"
```

## Step 3: Provision Infrastructure with Terraform

Initialize and apply Terraform configuration:

```bash
cd terraform

# Initialize Terraform
terraform init

# Review planned changes
terraform plan -var-file="environments/dev.tfvars"

# Apply configuration (confirm with 'yes' when prompted)
terraform apply -var-file="environments/dev.tfvars"
```

**Expected outputs**:
- Azure Container Registry created (or existing one used)
- Managed Identity created for agent
- Role assignments granted to Fabric workspaces
- Application Insights resource created
- Foundry agent registration placeholder created

**Note down the output values** (you'll need them in the next steps):
```
managed_identity_client_id = "..."
container_registry_login_server = "yourregistry.azurecr.io"
agent_endpoint_url = "https://..."
```

## Step 4: Build and Push Container Image

Build the agent container and push to Azure Container Registry:

```bash
# Return to repository root
cd ..

# Login to Azure Container Registry
az acr login --name yourregistryname

# Build container image (multi-stage build)
docker build -t semantic-modeling-agent:1.0.0 .

# Tag for ACR
docker tag semantic-modeling-agent:1.0.0 yourregistry.azurecr.io/semantic-modeling-agent:1.0.0

# Push to registry
docker push yourregistry.azurecr.io/semantic-modeling-agent:1.0.0
```

**Build time**: ~3-5 minutes for first build (layer caching speeds up subsequent builds)

## Step 5: Register Agent in Foundry

Update the agent registration with the container image URI:

```bash
# Update Terraform with container image URI
terraform apply \
  -var-file="environments/dev.tfvars" \
  -var="container_image_uri=yourregistry.azurecr.io/semantic-modeling-agent:1.0.0"
```

Terraform will:
1. Update the Foundry agent registration with the container image
2. Configure health check endpoint (`/health`)
3. Configure invocation endpoint (`/invoke`)
4. Wait for agent to become `active` (health checks passing)

**Expected output**:
```
agent_status = "active"
agent_id = "..."
health_check_url = "https://.../health"
```

## Step 6: Verify Agent Health

Test the agent health endpoint:

```bash
# Get agent endpoint from Terraform output
AGENT_ENDPOINT=$(terraform output -raw agent_endpoint_url)

# Call health endpoint
curl $AGENT_ENDPOINT/health
```

**Expected response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "checks": {
    "application": "healthy",
    "fabric_connectivity": "healthy",
    "memory_usage_mb": 256,
    "uptime_seconds": 120
  },
  "timestamp": "2026-02-05T12:34:56Z"
}
```

## Step 7: Invoke Agent (Test Execution)

Create a test invocation request:

```bash
# Create test request JSON
cat > test-request.json <<EOF
{
  "schema_source": {
    "type": "csv_url",
    "url": "https://raw.githubusercontent.com/your-org/test-data/main/sales-sample.csv",
    "sample_rows": 100
  },
  "workspace_id": "your-dev-workspace-id",
  "deployment_mode": "dry_run",
  "options": {
    "detect_measures": true,
    "detect_hierarchies": true,
    "target_optimization": "direct_lake"
  }
}
EOF

# Invoke agent via Foundry (replace with actual Foundry invocation method)
curl -X POST $AGENT_ENDPOINT/invoke \
  -H "Content-Type: application/json" \
  -d @test-request.json
```

**Expected response** (within 1-2 minutes):
```json
{
  "invocation_id": "f1e2d3c4-b5a6-7890-1234-567890abcdef",
  "status": "succeeded",
  "duration_ms": 45000,
  "artifacts": {
    "tmsl_url": "https://storage.../artifacts/model-123.tmsl",
    "tmdl_url": "https://storage.../artifacts/model-123.tmdl",
    "validation_report_url": "https://storage.../reports/validation-123.json"
  },
  "diagnostics": {
    "warnings": [],
    "anti_patterns": []
  }
}
```

## Step 8: View Logs in Application Insights

1. Navigate to Azure Portal → Application Insights resource (from Terraform output)
2. Go to **Transaction search** or **Logs**
3. Query for agent execution logs:

```kusto
traces
| where customDimensions.invocation_id == "f1e2d3c4-b5a6-7890-1234-567890abcdef"
| project timestamp, severityLevel, message, operation_Name
| order by timestamp asc
```

You should see detailed logs for the entire invocation lifecycle.

---

## Next Steps

Now that your agent is deployed and verified, you can:

### Deploy to Staging/Production

1. Create `staging.tfvars` or `prod.tfvars` with environment-specific values
2. Follow steps 3-7 using the new environment file
3. **Production deployment**: Ensure approval gates are configured in CI/CD pipeline (GitHub Actions)

### Set Up Continuous Deployment

Configure GitHub Actions for automated deployments:

```bash
# Enable GitHub Actions workflow
git checkout -b setup-cicd
cp .github/workflows/deploy-agent.yml.example .github/workflows/deploy-agent.yml

# Configure GitHub secrets (in repository settings):
# - AZURE_CREDENTIALS (service principal JSON)
# - ACR_NAME (container registry name)
# - FOUNDRY_PROJECT_ID (Foundry project GUID)

git add .github/workflows/deploy-agent.yml
git commit -m "feat: enable CI/CD for agent deployment"
git push origin setup-cicd
```

### Invoke Agent from Foundry UI

1. Log in to [Azure AI Foundry](https://ai.azure.com)
2. Navigate to your project → **Agents**
3. Select **semantic-modeling-agent**
4. Click **Test** and provide a sample CSV URL or Lakehouse reference
5. Review generated artifacts and validation report

### Monitor Agent Performance

Set up alerts for key metrics:

```bash
# Create alert rule for health check failures
az monitor metrics alert create \
  --name "agent-health-check-failed" \
  --resource-group rg-foundry-dev \
  --scopes "/subscriptions/.../resourceGroups/rg-foundry-dev/providers/Microsoft.Insights/components/appi-foundry-dev" \
  --condition "customMetrics/health_check_failures > 3" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --action-group-id "/subscriptions/.../actionGroups/ops-team"
```

---

## Troubleshooting

### Agent shows "inactive" status

**Cause**: Health checks are failing.

**Resolution**:
1. Check Application Insights logs for errors
2. Verify Fabric workspace access (managed identity has correct role)
3. Review container logs: `docker logs <container-id>`
4. Ensure network connectivity to Fabric API endpoints

### Permission errors during invocation

**Cause**: Managed identity lacks permissions on Fabric workspace.

**Resolution**:
```bash
# Grant Fabric Workspace Admin role
az role assignment create \
  --assignee <managed-identity-principal-id> \
  --role "Fabric Workspace Admin" \
  --scope "/subscriptions/.../resourceGroups/.../providers/Microsoft.Fabric/workspaces/..."
```

### Container build fails

**Cause**: Missing dependencies or network issues.

**Resolution**:
1. Ensure Docker daemon is running
2. Check `requirements.txt` for version conflicts
3. Clear Docker cache: `docker builder prune --all`
4. Rebuild with `--no-cache` flag

### Agent invocation times out

**Cause**: Large schema or complex modeling logic exceeding 3-minute limit.

**Resolution**:
1. Reduce `sample_rows` in request (default: 100)
2. Check for expensive operations in logs
3. Consider increasing timeout in Foundry configuration (if supported)

---

## Configuration Reference

### Environment Variables in Container

The container accepts the following environment variables (set via Terraform):

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `AZURE_CLIENT_ID` | Managed identity client ID | Yes | (from Terraform) |
| `FOUNDRY_PROJECT_ID` | Foundry project GUID | Yes | (from Terraform) |
| `APP_INSIGHTS_CONNECTION_STRING` | Application Insights connection string | Yes | (from Terraform) |
| `LOG_LEVEL` | Logging verbosity (`DEBUG`, `INFO`, `ERROR`) | No | `INFO` |
| `HEALTH_CHECK_TIMEOUT` | Health check timeout in seconds | No | `5` |
| `INVOCATION_TIMEOUT` | Max invocation duration in seconds | No | `180` |

### Terraform Outputs

After successful `terraform apply`, the following outputs are available:

```bash
terraform output managed_identity_client_id
terraform output container_registry_login_server
terraform output agent_id
terraform output agent_endpoint_url
terraform output app_insights_connection_string
```

---

## Additional Resources

- [Azure AI Foundry Documentation](https://learn.microsoft.com/azure/ai-studio/)
- [Power BI REST API Reference](https://learn.microsoft.com/rest/api/power-bi/)
- [Microsoft Fabric Workspace Management](https://learn.microsoft.com/fabric/admin/fabric-admin-portal)
- [OpenAPI Contract](./contracts/agent-api.yaml) - Full API specification
- [Data Model](./data-model.md) - Entity definitions and relationships
- [Research](./research.md) - Technology decisions and alternatives

---

## Support

For issues or questions:

- **Internal team**: Slack #semantic-modeling-agent
- **Bug reports**: GitHub Issues
- **Feature requests**: GitHub Discussions
