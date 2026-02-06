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
  }
  
  backend "azurerm" {
    # Backend configuration provided via backend config file or CLI
  }
}

provider "azurerm" {
  features {}
}

provider "azuread" {}
