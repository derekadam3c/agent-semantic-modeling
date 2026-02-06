variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "pbi-semantic-agent"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "location" {
  description = "Azure region for resources"
  type        = string
  default     = "eastus"
}

variable "resource_group_name" {
  description = "Name of the Azure resource group"
  type        = string
}

variable "fabric_workspace_name" {
  description = "Microsoft Fabric workspace name"
  type        = string
}

variable "fabric_capacity_id" {
  description = "Microsoft Fabric capacity ID (if applicable)"
  type        = string
  default     = null
}

variable "ai_foundry_project_name" {
  description = "Azure AI Foundry project name"
  type        = string
}

variable "enable_managed_identity" {
  description = "Enable managed identity for agent"
  type        = bool
  default     = true
}

variable "require_approval_gates" {
  description = "Require approval gates for production deployments"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
