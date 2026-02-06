# Terraform configuration for Power BI Semantic Modeling Agent
# Deploys agent to Azure AI Foundry with managed identity and supporting resources

terraform {
  required_version = ">= 1.5.0"
  
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    azuread = {
      source  = "hashicorp/azuread"
      version = "~> 2.0"
    }
    azapi = {
      source  = "azure/azapi"
      version = "~> 1.0"
    }
  }
  
  # Remote state configuration (uncomment and configure for team environments)
  # backend "azurerm" {
  #   resource_group_name  = "terraform-state-rg"
  #   storage_account_name = "tfstateXXXXX"
  #   container_name       = "tfstate"
  #   key                  = "pbi-semantic-agent.tfstate"
  # }
}

provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
    
    key_vault {
      purge_soft_delete_on_destroy    = true
      recover_soft_deleted_key_vaults = true
    }
  }
}

provider "azuread" {}
provider "azapi" {}

# Data sources
data "azurerm_client_config" "current" {}

# Local variables for resource naming and tagging
locals {
  resource_prefix = "${var.agent_name}-${var.environment}"
  
  # Azure region short codes
  region_short = {
    "eastus"          = "eus"
    "eastus2"         = "eus2"
    "westus"          = "wus"
    "westus2" = "wus2"
    "centralus"       = "cus"
    "westeurope"      = "weu"
    "northeurope"     = "neu"
  }
  
  location_short = lookup(local.region_short, var.location, "eus")
  
  # Common tags
  common_tags = merge(
    {
      Environment = var.environment
      Application = "PowerBI-Semantic-Agent"
      Terraform   = "true"
      Version     = var.agent_version
      CostCenter  = var.cost_center
    },
    var.additional_tags
  )
}
