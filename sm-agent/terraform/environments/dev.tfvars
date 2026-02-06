# Development Environment Configuration
# Use this with: terraform apply -var-file=environments/dev.tfvars

# Azure AI Foundry
foundry_project_id       = "00000000-0000-0000-0000-000000000000"  # TODO: Replace with actual Foundry project ID
foundry_subscription_id  = "6c8e23df-4aec-4ed5-bec5-79853ea6c6c6"  # Data Lab subscription
foundry_resource_group   = "rg-foundry-dev"

# Agent Configuration
agent_name               = "pbi-semantic-agent"
agent_version            = "1.0.0"
container_image_tag      = "dev-latest"

# Azure Environment
environment              = "dev"
location                 = "eastus"
resource_group_name      = "rg-pbi-agent-dev"

# Container Registry
acr_name                 = ""  # Leave empty to create new ACR
acr_sku                  = "Standard"

# Microsoft Fabric Workspaces  
fabric_workspace_ids     = [
  # "11111111-1111-1111-1111-111111111111",  # TODO: Add Fabric workspace IDs
]

# Application Insights
app_insights_name            = ""
app_insights_retention_days  = 30

# Tagging
cost_center              = "Engineering"
additional_tags = {
  Team        = "Data Platform"
  Purpose     = "Development"
}
