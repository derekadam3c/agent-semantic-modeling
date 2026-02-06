# Terraform Infrastructure

This directory contains Terraform configurations for deploying the Power BI Semantic Modeling Agent infrastructure.

## Structure

- `main.tf` - Provider configuration and backend setup
- `variables.tf` - Input variable definitions
- `outputs.tf` - Output value definitions
- `resources.tf` - Azure resource definitions
- `environments/` - Environment-specific variable files

## Resources Created

- Azure Resource Group
- Managed Identity (for agent authentication)
- Key Vault (for secrets management)
- Log Analytics Workspace (for monitoring)
- Application Insights (for telemetry)

## Usage

### Initialize Terraform

```bash
cd terraform
terraform init
```

### Plan Deployment

```bash
# Development
terraform plan -var-file="environments/dev.tfvars"

# Staging
terraform plan -var-file="environments/staging.tfvars"

# Production
terraform plan -var-file="environments/prod.tfvars"
```

### Apply Deployment

```bash
# Development
terraform apply -var-file="environments/dev.tfvars"

# Staging
terraform apply -var-file="environments/staging.tfvars"

# Production (requires approval)
terraform apply -var-file="environments/prod.tfvars"
```

### Destroy Resources

```bash
terraform destroy -var-file="environments/dev.tfvars"
```

## Backend Configuration

Configure the Terraform backend for remote state storage:

```bash
terraform init \
  -backend-config="resource_group_name=rg-terraform-state" \
  -backend-config="storage_account_name=sttfstate" \
  -backend-config="container_name=tfstate" \
  -backend-config="key=pbi-agent-${ENVIRONMENT}.tfstate"
```

## Required Permissions

- Contributor on target subscription
- User Access Administrator (for role assignments)
- Fabric Workspace Admin (for workspace operations)
