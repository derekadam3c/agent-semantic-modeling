# Power BI Semantic Modeling & Deployment Agent

<p align="center">
  <strong>Autonomous AI agent for designing, validating, and deploying Power BI semantic models to Microsoft Fabric</strong>
</p>

## Overview

The **Power BI Semantic Modeling Agent** is an autonomous, tool-enabled agent designed for Azure AI Foundry. It accepts dataset schemas from various sources (CSV, SQL, Fabric Lakehouse/Warehouse, Tableau metadata) and autonomously:

- **Designs** industry-standard semantic models (facts, dimensions, relationships, measures, hierarchies)
- **Validates** models against best practices and detects anti-patterns
- **Optimizes** for Microsoft Fabric and Direct Lake performance
- **Deploys** completed models to Fabric workspaces via Power BI/Fabric APIs

## Features

### 🎯 Agent Capabilities

- **Multi-format Input Support**: CSV, SQL INFORMATION_SCHEMA, Lakehouse/Warehouse schemas, Tableau TWB metadata
- **Intelligent Schema Analysis**: Automatically detects fact/dimension tables, grain, natural keys, and cardinality
- **Semantic Model Generation**: Creates TMSL/TMDL artifacts with tables, relationships, measures, and hierarchies
- **Anti-pattern Detection**: Identifies circular relationships, high-cardinality issues, and performance problems
- **Fabric Optimization**: Direct Lake compatibility checks and optimization recommendations
- **Automated Deployment**: Deploys to Fabric workspaces with configurable approval gates

### 🔒 Governance & Security

- **Human-in-the-loop** approval gates for production deployments
- **Managed Identity** authentication for Azure resources
- **Data classification** respect and sensitive field handling
- **Audit trails** for all agent actions
- **Rollback capabilities** for failed deployments

### 📊 8-Step Workflow

1. **Intake**: Accept dataset schema + metadata
2. **Discovery**: Infer facts/dimensions, grain, measures, keys
3. **Design**: Generate semantic model draft
4. **Validate**: Run anti-pattern checks and performance heuristics
5. **Optimize**: Suggest star schema reorganizations
6. **Dry-run**: Produce TMSL/TMDL and pre-deploy validation
7. **Deploy**: Deploy to Fabric workspace via APIs
8. **Confirm**: Return success status or diagnostics

## Quick Start

### Prerequisites

- Python 3.11+
- Azure subscription with:
  - Azure AI Foundry project
  - Microsoft Fabric workspace
  - Appropriate permissions (Contributor, Fabric Admin)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd sm-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Copy environment template
cp .env.example .env
# Edit .env with your Azure and Fabric credentials
```

### Configuration

Update `.env` with your values:

```bash
# Azure AI Foundry
FOUNDRY_ENDPOINT=https://your-foundry-endpoint
FOUNDRY_SUBSCRIPTION_ID=your-subscription-id
FOUNDRY_RESOURCE_GROUP=your-resource-group
FOUNDRY_PROJECT_NAME=your-project-name

# Microsoft Fabric
FABRIC_TENANT_ID=your-tenant-id
FABRIC_DEFAULT_WORKSPACE_ID=your-workspace-id

# Authentication
USE_MANAGED_IDENTITY=false  # true in Azure environments

# Deployment
REQUIRE_APPROVAL_FOR_PRODUCTION=true
DRY_RUN_ENABLED=true
```

### Running Tests

```bash
# Run unit tests
pytest tests/unit/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run integration tests (requires Azure credentials)
pytest tests/integration/ -v -m integration
```

### Local Development with Docker

```bash
# Build and run with Docker Compose
docker-compose up

# Run tests in container
docker-compose run agent pytest tests/
```

## Infrastructure Deployment

### Terraform Setup

```bash
cd terraform

# Initialize Terraform
terraform init

# Plan deployment for dev environment
terraform plan -var-file="environments/dev.tfvars"

# Apply infrastructure
terraform apply -var-file="environments/dev.tfvars"
```

### What Gets Deployed

- Azure Resource Group
- Managed Identity for agent authentication
- Azure Key Vault for secrets
- Log Analytics + Application Insights for monitoring
- (Fabric workspace and capacity configured separately)

## Project Structure

```
sm-agent/
├── src/                          # Source code
│   ├── agent/                    # Core agent implementation
│   ├── schema_parsers/           # Input format parsers (CSV, SQL, Lakehouse, Tableau)
│   ├── modeling/                 # Semantic modeling logic
│   ├── validation/               # Anti-pattern detection & performance analysis
│   ├── fabric/                   # Fabric API clients
│   ├── artifacts/                # TMSL/TMDL generators
│   └── core/                     # Config, logging, utilities
├── tests/                        # Test suite
│   ├── unit/                     # Unit tests
│   ├── integration/              # Integration tests
│   └── data/                     # Test data
├── terraform/                    # Infrastructure as Code
│   ├── environments/             # Environment-specific configs
│   └── *.tf                      # Terraform modules
├── .github/                      # GitHub workflows & prompts
│   ├── workflows/                # CI/CD pipelines
│   └── prompts/                  # Doit workflow prompts
├── .doit/                        # Doit framework configuration
│   ├── memory/                   # Constitution, tech stack, roadmap
│   └── templates/                # Feature templates
├── pyproject.toml                # Python project config
├── requirements.txt              # Production dependencies
├── requirements-dev.txt          # Development dependencies
├── Dockerfile                    # Container definition
└── docker-compose.yml            # Local development setup
```

## Development Workflow

This project uses the **Doit workflow** for structured development:

```bash
# 1. Create feature specification
/doit.specit [feature description]

# 2. Generate implementation plan
/doit.planit

# 3. Create task breakdown
/doit.taskit

# 4. Implement tasks
/doit.implementit

# 5. Run tests
/doit.testit

# 6. Review code
/doit.reviewit

# 7. Complete and create PR
/doit.checkin
```

## Configuration

### Agent Configuration

Agent behavior is controlled via [src/core/config.py](src/core/config.py):

- **Foundry settings**: Project, subscription, resource group
- **Fabric settings**: Tenant ID, default workspace
- **Deployment policies**: Approval gates, dry-run mode
- **Logging**: Log level and formatting

### Governance

See [.doit/memory/constitution.md](.doit/memory/constitution.md) for project principles and governance:

- Autonomy & Tooling (NON-NEGOTIABLE)
- Fabric-First Semantic Modeling Practices
- Data Governance & Security
- Observability, Testing & Diagnostics
- Idempotence, Versioning & Reproducibility

## CI/CD

### GitHub Actions Workflows

- **[ci-cd.yml](.github/workflows/ci-cd.yml)**: Lint, test, build Docker image
- **[deploy.yml](.github/workflows/deploy.yml)**: Deploy infrastructure and agent to Foundry
- **[terraform-validate.yml](.github/workflows/terraform-validate.yml)**: Validate Terraform configs

### Deployment Environments

- **Development**: Auto-deploy on push to `develop`
- **Staging**: Manual workflow dispatch with approval
- **Production**: Manual workflow dispatch with required approval gates

## Success Criteria

- **Design Accuracy**: 90%+ correct fact/dimension and grain identification
- **Deployment Reliability**: 95%+ automated deployment success for dev/staging
- **Performance Guidance**: Measurable query time or memory improvements
- **Observability**: Every run produces validation and deployment reports

## Contributing

1. Fork the repository
2. Create a feature branch (`/doit.specit` your feature)
3. Follow the Doit workflow for implementation
4. Ensure tests pass (`pytest tests/`)
5. Submit a pull request

## License

[MIT License](LICENSE)

## Support

For issues, questions, or contributions:

- **Issues**: GitHub issue tracker
- **Documentation**: [docs/](docs/)
- **Constitution**: [.doit/memory/constitution.md](.doit/memory/constitution.md)

---

**Built with**: Python 3.11+ | Azure AI Foundry | Microsoft Fabric | Terraform
