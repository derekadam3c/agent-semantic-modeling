# Production Environment
project_name         = "pbi-semantic-agent"
environment          = "prod"
location             = "eastus"
resource_group_name  = "rg-pbi-agent-prod"

fabric_workspace_name    = "prod-semantic-models"
ai_foundry_project_name  = "pbi-agent-prod"

enable_managed_identity  = true
require_approval_gates   = true

tags = {
  Team        = "Data Engineering"
  CostCenter  = "Engineering"
  Environment = "Production"
}
