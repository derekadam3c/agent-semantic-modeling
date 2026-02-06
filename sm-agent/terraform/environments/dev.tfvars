# Development Environment
project_name         = "pbi-semantic-agent"
environment          = "dev"
location             = "eastus"
resource_group_name  = "rg-pbi-agent-dev"

fabric_workspace_name    = "dev-semantic-models"
ai_foundry_project_name  = "pbi-agent-dev"

enable_managed_identity  = true
require_approval_gates   = false

tags = {
  Team        = "Data Engineering"
  CostCenter  = "Engineering"
  Environment = "Development"
}
