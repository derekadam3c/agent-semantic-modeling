# Azure resources for Power BI Semantic Modeling Agent

# Data sources
data "azurerm_client_config" "current" {}

# Resource Group
resource "azurerm_resource_group" "main" {
  name     = coalesce(var.resource_group_name, var.foundry_resource_group)
  location = var.location
  
  tags = merge(local.common_tags, {
    Purpose = "Power BI Semantic Modeling Agent Infrastructure"
  })
}

# Managed Identity for Agent
resource "azurerm_user_assigned_identity" "agent" {
  name                = "${local.resource_prefix}-identity"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  
  tags = local.common_tags
}

# Azure Container Registry
resource "azurerm_container_registry" "agent" {
  count               = var.acr_name != "" ? 1 : 0
  name                = replace(coalesce(var.acr_name, "${local.resource_prefix}acr${local.location_short}"), "-", "")
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = var.acr_sku
  admin_enabled       = false
  
  tags = local.common_tags
}

# Role Assignment: ACR Pull for Managed Identity
resource "azurerm_role_assignment" "acr_pull" {
  count                = var.acr_name != "" ? 1 : 0
  scope                = azurerm_container_registry.agent[0].id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_user_assigned_identity.agent.principal_id
}

# Role Assignments: Fabric Workspace Access (placeholder for Fabric RBAC)
# NOTE: Fabric RBAC may require custom azapi resources or provider when generally available
resource "azurerm_role_assignment" "fabric_workspace" {
  for_each             = toset(var.fabric_workspace_ids)
  scope                = "/subscriptions/${var.foundry_subscription_id}/resourceGroups/${var.foundry_resource_group}/providers/Microsoft.Fabric/workspaces/${each.value}"
  role_definition_name = "Contributor"
  principal_id         = azurerm_user_assigned_identity.agent.principal_id
  
  skip_service_principal_aad_check = true
}

# Key Vault for Secrets (optional, for future use)
resource "azurerm_key_vault" "main" {
  name                       = "${substr(local.resource_prefix, 0, 20)}-kv"
  location                   = azurerm_resource_group.main.location
  resource_group_name        = azurerm_resource_group.main.name
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  sku_name                   = "standard"
  soft_delete_retention_days = 7
  purge_protection_enabled   = var.environment == "prod"
  
  # Grant access to managed identity
  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = azurerm_user_assigned_identity.agent.principal_id
    
    secret_permissions = [
      "Get",
      "List"
    ]
  }
  
  tags = local.common_tags
}

# Log Analytics Workspace for Monitoring
resource "azurerm_log_analytics_workspace" "main" {
  name                = "${local.resource_prefix}-logs"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = var.app_insights_retention_days
  
  tags = local.common_tags
}

# Application Insights for Telemetry
resource "azurerm_application_insights" "main" {
  name                = coalesce(var.app_insights_name, "${local.resource_prefix}-appins")
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  workspace_id        = azurerm_log_analytics_workspace.main.id
  application_type    = "web"
  
  tags = local.common_tags
}

# NOTE: Foundry agent registration would be added here using azapi provider
# when Foundry Terraform resources become generally available
