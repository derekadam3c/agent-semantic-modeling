# Input variables for Power BI Semantic Modeling Agent deployment

# =============================================================================
# Azure AI Foundry Configuration
# =============================================================================

variable "foundry_project_id" {
  description = "Azure AI Foundry project ID where the agent will be registered"
  type        = string
  
  validation {
    condition     = can(regex("^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", var.foundry_project_id))
    error_message = "foundry_project_id must be a valid UUID"
  }
}

variable "foundry_subscription_id" {
  description = "Azure subscription ID where Foundry project is deployed"
  type        = string
}

variable "foundry_resource_group" {
  description = "Azure resource group containing the Foundry project"
  type        = string
}

# =============================================================================
# Agent Configuration
# =============================================================================

variable "agent_name" {
  description = "Name of the agent (used in resource naming)"
  type        = string
  default     = "pbi-semantic-agent"
}

variable "agent_version" {
  description = "Semantic version of the agent being deployed"
  type        = string
  default     = "1.0.0"
}

variable "container_image_tag" {
  description = "Container image tag to deploy"
  type        = string
  default     = "latest"
}

# =============================================================================
# Azure Environment Configuration
# =============================================================================

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be dev, staging, or prod"
  }
}

variable "location" {
  description = "Azure region for resource deployment"
  type        = string
  default     = "eastus"
}

variable "resource_group_name" {
  description = "Name of resource group to create (leave empty to use foundry_resource_group)"
  type        = string
  default     = ""
}

# =============================================================================
# Container Registry Configuration
# =============================================================================

variable "acr_name" {
  description = "Azure Container Registry name (leave empty for auto-generation)"
  type        = string
  default     = ""
}

variable "acr_sku" {
  description = "Azure Container Registry SKU (Basic, Standard, Premium)"
  type        = string
  default     = "Standard"
}

# =============================================================================
# Microsoft Fabric Configuration
# =============================================================================

variable "fabric_workspace_ids" {
  description = "List of Fabric workspace IDs where agent needs deployment permissions"
  type        = list(string)
  default     = []
}

# =============================================================================
# Application Insights Configuration
# =============================================================================

variable "app_insights_name" {
  description = "Name for Application Insights instance (leave empty to auto-generate)"
  type        = string
  default     = ""
}

variable "app_insights_retention_days" {
  description = "Number of days to retain Application Insights data"
  type        = number
  default     = 90
}

# =============================================================================
# Tagging & Organization
# =============================================================================

variable "cost_center" {
  description = "Cost center tag for billing attribution"
  type        = string
  default     = "Engineering"
}

variable "additional_tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}
