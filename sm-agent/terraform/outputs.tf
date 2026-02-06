output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.main.name
}

output "resource_group_id" {
  description = "ID of the resource group"
  value       = azurerm_resource_group.main.id
}

output "key_vault_name" {
  description = "Name of the Key Vault"
  value       = azurerm_key_vault.main.name
}

output "key_vault_uri" {
  description = "URI of the Key Vault"
  value       = azurerm_key_vault.main.vault_uri
}

output "managed_identity_principal_id" {
  description = "Principal ID of the managed identity"
  value       = var.enable_managed_identity ? azurerm_user_assigned_identity.agent[0].principal_id : null
}

output "managed_identity_client_id" {
  description = "Client ID of the managed identity"
  value       = var.enable_managed_identity ? azurerm_user_assigned_identity.agent[0].client_id : null
}
