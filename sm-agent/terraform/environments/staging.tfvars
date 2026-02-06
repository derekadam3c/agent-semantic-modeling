# Staging Environment Configuration
# Use this with: terraform apply -var-file=environments/staging.tfvars

# Azure AI Foundry
foundry_project_id       = "00000000-0000-0000-0000-000000000000"  # TODO: Replace with actual Foundry project ID
foundry_subscription_id  = "00000000-0000-0000-0000-000000000000"  # TODO: Replace with Azure subscription ID
foundry_resource_group   = "rg-foundry-staging"

# Agent Configuration
agent_name               = "pbi-semantic-agent"
agent_version            = "1.0.0"
container_image_tag      = "staging-latest"

# Azure Environment
environment              = "staging"
location                 = "eastus"
resource_group_name      = "rg-pbi-agent-staging"

# Container Registry
acr_name                 = ""  # Leave empty to create new ACR
acr_sku                  = "Standard"

# Microsoft Fabric Workspaces
fabric_workspace_ids     = [
  # "22222222-2222-2222-2222-222222222222",  # TODO: Add Fabric workspace IDs
]

# Application Insights
app_insights_name            = ""
app_insights_retention_days  = 60

# Tagging
cost_center              = "Engineering"
additional_tags = {
  Team        = "Data Platform"
  Purpose     = "Staging"
}
