# Terraform outputs for Power BI Semantic Modeling Agent

#============================================================================
# Managed Identity Outputs
# =============================================================================

output "managed_identity_client_id" {
  description = "Client ID of the managed identity (use for AZURE_CLIENT_ID)"
  value       = azurerm_user_assigned_identity.agent.client_id
  sensitive   = false
}

output "managed_identity_principal_id" {
  description = "Principal ID of the managed identity (for RBAC assignments)"
  value       = azurerm_user_assigned_identity.agent.principal_id
  sensitive   = false
}

output "managed_identity_id" {
  description = "Resource ID of the managed identity"
  value       = azurerm_user_assigned_identity.agent.id
  sensitive   = false
}

# =============================================================================
# Container Registry Outputs
# =============================================================================

output "container_registry_login_server" {
  description = "Login server URL for Azure Container Registry"
  value       = length(azurerm_container_registry.agent) > 0 ? azurerm_container_registry.agent[0].login_server : null
  sensitive   = false
}

output "container_registry_name" {
  description = "Name of the Azure Container Registry"
  value       = length(azurerm_container_registry.agent) > 0 ? azurerm_container_registry.agent[0].name : null
  sensitive   = false
}

# =============================================================================
# Application Insights Outputs
# =============================================================================

output "app_insights_connection_string" {
  description = "Application Insights connection string (use for APP_INSIGHTS_CONNECTION_STRING)"
  value       = azurerm_application_insights.main.connection_string
  sensitive   = true
}

output "app_insights_instrumentation_key" {
  description = "Application Insights instrumentation key (legacy)"
  value       = azurerm_application_insights.main.instrumentation_key
  sensitive   = true
}

output "app_insights_name" {
  description = "Name of the Application Insights instance"
  value       = azurerm_application_insights.main.name
  sensitive   = false
}

# =============================================================================
# Resource Group Outputs
# =============================================================================

output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.main.name
  sensitive   = false
}

output "resource_group_id" {
  description = "ID of the resource group"
  value       = azurerm_resource_group.main.id
  sensitive   = false
}

output "resource_group_location" {
  description = "Location of the resource group"
  value       = azurerm_resource_group.main.location
  sensitive   = false
}

# =============================================================================
# Agent Configuration Outputs
# =============================================================================

output "agent_version" {
  description = "Deployed agent version"
  value       = var.agent_version
  sensitive   = false
}

output "agent_environment" {
  description = "Deployment environment"
  value       = var.environment
  sensitive   = false
}

# NOTE: Agent endpoint URL and status would be exported here
# once Foundry agent registration resource is implemented
