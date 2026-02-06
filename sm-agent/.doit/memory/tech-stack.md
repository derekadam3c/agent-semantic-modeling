# Power BI Semantic Modeling Agent Tech Stack

> **See also**: [Constitution](constitution.md) for project principles and governance.

## Tech Stack

### Languages

**Python 3.11+** (primary agent implementation)  
**DAX/M** (semantic model expressions - generated as output)  
**HCL** (Terraform configuration for infrastructure)

### Frameworks

**Azure AI Foundry SDK** (agent orchestration and deployment)  
**Microsoft Fabric SDK** (workspace and semantic model operations)  
**Power BI REST APIs** (TMSL/TMDL deployment, dataset management)  
**pytest** (testing framework)

### Libraries

**azure-ai-projects** (Azure AI Foundry agent integration)  
**azure-identity** (managed identity and service principal auth)  
**pydantic** (schema validation and data modeling)  
**pyyaml** / **json** (TMSL/TMDL artifact serialization)  
**semantic-link** (Fabric semantic model SDK)  
**requests** / **httpx** (Power BI REST API client)  
**rich** (CLI output and diagnostics formatting)

## Infrastructure

### Hosting

**Azure AI Foundry** (registered agent deployment)  
**Azure Container Apps** (optional - for agent runtime if needed)  
**Microsoft Fabric Workspaces** (deployment target for semantic models)

### Cloud Provider

**Azure** (primary)  
- Azure AI Foundry for agent orchestration
- Microsoft Fabric for Power BI semantic models
- Azure Key Vault for secrets management
- Azure Monitor for observability

### Database

**None** (stateless agent - semantic models deployed to Fabric workspaces)  
**Optional**: Azure Cosmos DB for audit trail and deployment history if required

## Deployment

### CI/CD Pipeline

**GitHub Actions** (primary)  
- Agent code deployment to Azure AI Foundry
- Terraform infrastructure provisioning
- Semantic model validation and testing

### Deployment Strategy

**Agent Registration** to Azure AI Foundry (versioned agent deployments)  
**Terraform** for infrastructure as code (Fabric workspace provisioning, permissions)  
**Approval Gates** for production semantic model deployments (human-in-the-loop)

### Environments

**Development** (local testing with Fabric emulator/dev workspace)  
**Staging** (dedicated Fabric staging workspace for validation)  
**Production** (production Fabric workspaces with approval gates)
