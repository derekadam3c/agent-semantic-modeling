# Staging Environment
project_name         = "pbi-semantic-agent"
environment          = "staging"
location             = "eastus"
resource_group_name  = "rg-pbi-agent-staging"

fabric_workspace_name    = "staging-semantic-models"
ai_foundry_project_name  = "pbi-agent-staging"

enable_managed_identity  = true
require_approval_gates   = true

tags = {
  Team        = "Data Engineering"
  CostCenter  = "Engineering"
  Environment = "Staging"
}
