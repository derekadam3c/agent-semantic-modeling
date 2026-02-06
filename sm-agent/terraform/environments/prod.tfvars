# Production Environment Configuration
# Use this with: terraform apply -var-file=environments/prod.tfvars
# REQUIRES: Manual approval in deployment pipeline

# Azure AI Foundry
foundry_project_id       = "00000000-0000-0000-0000-000000000000"  # TODO: Replace with actual Foundry project ID
foundry_subscription_id  = "00000000-0000-0000-0000-000000000000"  # TODO: Replace with Azure subscription ID
foundry_resource_group   = "rg-foundry-prod"

# Agent Configuration
agent_name               = "pbi-semantic-agent"
agent_version            = "1.0.0"
container_image_tag      = "v1.0.0"  # Use semantic versioning for prod

# Azure Environment
environment              = "prod"
location                 = "eastus"
resource_group_name      = "rg-pbi-agent-prod"

# Container Registry
acr_name                 = ""  # Leave empty to create new ACR
acr_sku                  = "Premium"  # Premium for production geo-replication

# Microsoft Fabric Workspaces
fabric_workspace_ids     = [
  # "33333333-3333-3333-3333-333333333333",  # TODO: Add Fabric workspace IDs
]

# Application Insights
app_insights_name            = ""
app_insights_retention_days  = 90

# Tagging
cost_center              = "Revenue"
additional_tags = {
  Team        = "Data Platform"
  Purpose     = "Production"
  Criticality = "High"
}
