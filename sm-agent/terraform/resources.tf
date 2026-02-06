# Resource Group
resource "azurerm_resource_group" "main" {
  name     = var.resource_group_name
  location = var.location
  
  tags = merge(var.tags, {
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "Terraform"
  })
}

# Managed Identity for Agent
resource "azurerm_user_assigned_identity" "agent" {
  count               = var.enable_managed_identity ? 1 : 0
  name                = "${var.project_name}-${var.environment}-identity"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  
  tags = azurerm_resource_group.main.tags
}

# Key Vault for Secrets
resource "azurerm_key_vault" "main" {
  name                       = "${var.project_name}-${var.environment}-kv"
  location                   = azurerm_resource_group.main.location
  resource_group_name        = azurerm_resource_group.main.name
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  sku_name                   = "standard"
  soft_delete_retention_days = 7
  purge_protection_enabled   = var.environment == "prod"
  
  # Grant access to managed identity
  dynamic "access_policy" {
    for_each = var.enable_managed_identity ? [1] : []
    content {
      tenant_id = data.azurerm_client_config.current.tenant_id
      object_id = azurerm_user_assigned_identity.agent[0].principal_id
      
      secret_permissions = [
        "Get",
        "List"
      ]
    }
  }
  
  tags = azurerm_resource_group.main.tags
}

# Log Analytics Workspace for Monitoring
resource "azurerm_log_analytics_workspace" "main" {
  name                = "${var.project_name}-${var.environment}-logs"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = var.environment == "prod" ? 90 : 30
  
  tags = azurerm_resource_group.main.tags
}

# Application Insights
resource "azurerm_application_insights" "main" {
  name                = "${var.project_name}-${var.environment}-insights"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  workspace_id        = azurerm_log_analytics_workspace.main.id
  application_type    = "other"
  
  tags = azurerm_resource_group.main.tags
}

# Data sources
data "azurerm_client_config" "current" {}
