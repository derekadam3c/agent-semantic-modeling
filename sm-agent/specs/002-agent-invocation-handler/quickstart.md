# Quickstart: Agent Invocation Handler

**Feature**: Agent Invocation Handler  
**Audience**: Developers integrating with the Fabric Semantic Modeling Agent  
**Prerequisites**: Basic HTTP/REST API knowledge, access to agent endpoint

## Overview

The Agent Invocation Handler is the HTTP endpoint (`POST /invoke`) that receives semantic modeling requests from Azure AI Foundry or direct HTTP clients. This guide demonstrates how to invoke the agent with different schema source types and interpret responses.

## Endpoint Details

**URL**: `https://pbi-semantic-agent.{environment}.azurecontainerapps.io/invoke`  
**Method**: `POST`  
**Content-Type**: `application/json`  
**Authentication**: Azure Managed Identity (when calling from Foundry) or API key (future enhancement)

## Basic Usage

### Example 1: CSV URL Schema Source (Dry Run)

Generate a semantic model from a publicly accessible CSV file without deploying to Fabric.

**Request**:
```bash
curl -X POST "https://pbi-semantic-agent.prod.azurecontainerapps.io/invoke" \
  -H "Content-Type: application/json" \
  -H "X-Correlation-ID: $(uuidgen)" \
  -d '{
    "schema_source": {
      "type": "csv_url",
      "url": "https://raw.githubusercontent.com/microsoft/powerbi-desktop-samples/main/Sample%20Reports/Supplier%20Quality%20Analysis%20Sample.csv",
      "sample_rows": 100
    },
    "workspace_id": "00000000-0000-0000-0000-000000000000",
    "deployment_mode": "dry_run",
    "options": {
      "detect_measures": true,
      "detect_hierarchies": true,
      "target_optimization": "direct_lake"
    }
  }'
```

**Response (HTTP 200)**:
```json
{
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "http_status_code": 200,
  "status": "success",
  "tmsl_output": {
    "model": {
      "name": "SupplierQualityAnalysis",
      "tables": [
        {
          "name": "FactDefects",
          "columns": [
            {"name": "DefectID", "dataType": "int64"},
            {"name": "Quantity", "dataType": "int64"},
            {"name": "DefectType", "dataType": "string"}
          ]
        }
      ],
      "relationships": [
        {
          "name": "FK_Defects_Supplier",
          "fromTable": "FactDefects",
          "fromColumn": "SupplierID",
          "toTable": "DimSupplier",
          "toColumn": "SupplierID"
        }
      ],
      "measures": [
        {
          "name": "Total Defects",
          "expression": "SUM(FactDefects[Quantity])"
        }
      ]
    }
  },
  "validation_results": [
    {
      "severity": "info",
      "category": "performance",
      "message": "Model contains 5 tables, 12 relationships, 8 measures",
      "recommendation": "Consider adding calculation groups for time intelligence"
    }
  ],
  "deployment_status": null,
  "execution_summary": {
    "total_duration_ms": 28430,
    "steps_executed": 8,
    "steps_succeeded": 8,
    "steps_failed": 0
  },
  "generated_at": "2026-02-06T14:23:45.123Z"
}
```

---

### Example 2: SQL Schema JSON Source (Validate Only)

Submit SQL schema metadata for validation without deployment.

**Request**:
```bash
curl -X POST "https://pbi-semantic-agent.prod.azurecontainerapps.io/invoke" \
  -H "Content-Type: application/json" \
  -d '{
    "schema_source": {
      "type": "sql_json",
      "tables": [
        {
          "name": "Orders",
          "columns": [
            {"name": "OrderID", "data_type": "int", "nullable": false},
            {"name": "CustomerID", "data_type": "int", "nullable": false},
            {"name": "OrderDate", "data_type": "datetime", "nullable": false},
            {"name": "TotalAmount", "data_type": "decimal", "nullable": false}
          ]
        },
        {
          "name": "Customers",
          "columns": [
            {"name": "CustomerID", "data_type": "int", "nullable": false},
            {"name": "CustomerName", "data_type": "varchar", "nullable": false},
            {"name": "Country", "data_type": "varchar", "nullable": true}
          ]
        }
      ],
      "foreign_keys": [
        {
          "table": "Orders",
          "column": "CustomerID",
          "referenced_table": "Customers",
          "referenced_column": "CustomerID"
        }
      ]
    },
    "workspace_id": "a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d",
    "deployment_mode": "validate_only",
    "options": {
      "detect_measures": true
    }
  }'
```

**Response (HTTP 200)**:
```json
{
  "correlation_id": "660f9511-f3ac-52e5-b827-557766551111",
  "http_status_code": 200,
  "status": "success",
  "tmsl_output": { "model": {...} },
  "validation_results": [
    {
      "severity": "warning",
      "category": "anti_pattern",
      "message": "Customers table has CustomerName as potential high-cardinality dimension",
      "affected_objects": ["Customers"],
      "recommendation": "Consider creating separate lookup table for customer names"
    }
  ],
  "execution_summary": {
    "total_duration_ms": 15200,
    "steps_executed": 7,
    "steps_succeeded": 7
  }
}
```

---

### Example 3: Fabric Lakehouse Connection (Auto Deploy)

Connect to Microsoft Fabric Lakehouse and deploy the generated model automatically.

**Request**:
```bash
curl -X POST "https://pbi-semantic-agent.prod.azurecontainerapps.io/invoke" \
  -H "Content-Type: application/json" \
  -H "X-Correlation-ID: 770fa622-g4bd-63f6-c938-668877662222" \
  -d '{
    "schema_source": {
      "type": "lakehouse_connection",
      "workspace_id": "a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d",
      "item_id": "f6g7h8i9-j0k1-4l5m-6n7o-8p9q0r1s2t3u",
      "table_filter": ["Sales*", "Dim*"]
    },
    "workspace_id": "a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d",
    "deployment_mode": "auto_deploy",
    "options": {
      "detect_measures": true,
      "detect_hierarchies": true,
      "target_optimization": "direct_lake"
    }
  }'
```

**Response (HTTP 200)**:
```json
{
  "correlation_id": "770fa622-g4bd-63f6-c938-668877662222",
  "http_status_code": 200,
  "status": "success",
  "tmsl_output": { "model": {...} },
  "validation_results": [],
  "deployment_status": {
    "deployment_id": "deploy-20260206-142345",
    "status": "succeeded",
    "workspace_id": "a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d",
    "model_name": "LakehouseSales",
    "deployment_type": "full",
    "started_at": "2026-02-06T14:23:45Z",
    "completed_at": "2026-02-06T14:24:12Z"
  },
  "execution_summary": {
    "total_duration_ms": 42500,
    "steps_executed": 8,
    "steps_succeeded": 8
  }
}
```

---

## Error Handling

### Validation Error (HTTP 400)

**Scenario**: Missing required field in request

**Request**:
```bash
curl -X POST "https://pbi-semantic-agent.prod.azurecontainerapps.io/invoke" \
  -H "Content-Type: application/json" \
  -d '{
    "schema_source": {
      "type": "csv_url"
    },
    "workspace_id": "00000000-0000-0000-0000-000000000000",
    "deployment_mode": "dry_run"
  }'
```

**Response (HTTP 400)**:
```json
{
  "correlation_id": "880fb733-h5ce-74g7-d049-779988773333",
  "http_status_code": 400,
  "status": "validation_error",
  "error_detail": {
    "type": "https://agent.fabric.microsoft.com/errors/invalid-request",
    "title": "Request Validation Failed",
    "status": 400,
    "detail": "Field required: schema_source.url is required when type is csv_url",
    "instance": "/invoke",
    "correlation_id": "880fb733-h5ce-74g7-d049-779988773333",
    "remediation": "Provide valid URL in schema_source.url field"
  }
}
```

---

### Workflow Error (HTTP 500)

**Scenario**: Circular dependency detected during relationship analysis

**Response (HTTP 500)**:
```json
{
  "correlation_id": "990fc844-i6df-85h8-e150-880099884444",
  "http_status_code": 500,
  "status": "workflow_error",
  "error_detail": {
    "type": "https://agent.fabric.microsoft.com/errors/workflow-failure",
    "title": "Workflow Execution Failed",
    "status": 500,
    "detail": "Circular dependency detected between Order and Customer tables",
    "instance": "/invoke",
    "correlation_id": "990fc844-i6df-85h8-e150-880099884444",
    "workflow_step": "relationships",
    "failed_at": "2026-02-06T14:23:45Z",
    "remediation": "Remove circular foreign key constraints between the affected tables",
    "affected_objects": ["Order", "Customer"]
  },
  "execution_summary": {
    "total_duration_ms": 12500,
    "steps_executed": 3,
    "steps_succeeded": 2,
    "steps_failed": 1
  }
}
```

---

### Timeout (HTTP 504)

**Scenario**: Workflow exceeded 5-minute execution limit

**Response (HTTP 504)**:
```json
{
  "correlation_id": "aa0fd955-j7eg-96i9-f261-991100995555",
  "http_status_code": 504,
  "status": "timeout",
  "error_detail": {
    "type": "https://agent.fabric.microsoft.com/errors/timeout",
    "title": "Workflow Execution Timeout",
    "status": 504,
    "detail": "Workflow execution exceeded 5-minute timeout limit",
    "instance": "/invoke",
    "correlation_id": "aa0fd955-j7eg-96i9-f261-991100995555",
    "workflow_step": "measure_generation",
    "failed_at": "2026-02-06T14:28:45Z",
    "remediation": "Reduce schema scope using table_filter or sample_rows parameters"
  },
  "execution_summary": {
    "total_duration_ms": 300000,
    "steps_executed": 4,
    "steps_succeeded": 3
  }
}
```

---

## Request Parameters

### Schema Source Types

| Type | Description | Required Fields | Optional Fields |
|------|-------------|-----------------|-----------------|
| `csv_url` | Public CSV file URL | `url` | `sample_rows` (default: 100) |
| `sql_json` | SQL schema metadata | `tables` | `foreign_keys` |
| `lakehouse_connection` | Fabric Lakehouse | `workspace_id`, `item_id` | `table_filter` |

### Deployment Modes

| Mode | Behavior | Use Case |
|------|----------|----------|
| `dry_run` | Generate TMSL only (no deployment) | Local testing, preview modeling decisions |
| `validate_only` | Generate + validate (no deployment) | CI/CD validation pipelines |
| `auto_deploy` | Generate + validate + deploy | Automated deployments (requires approval for production) |

### Processing Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `detect_measures` | boolean | false | Auto-generate SUM/COUNT/AVG measures for numeric columns |
| `detect_hierarchies` | boolean | false | Auto-detect date (Year→Month→Day) and geographic hierarchies |
| `target_optimization` | enum | null | Optimization hint: `import`, `direct_query`, or `direct_lake` |

---

## Response Interpretation

### Success Response (HTTP 200)

**Key Fields**:
- `tmsl_output`: Complete TMSL artifact ready for deployment or further customization
- `validation_results`: Array of findings (info/warning/error) from anti-pattern detection
- `deployment_status`: Deployment progress (null when `deployment_mode` is `dry_run` or `validate_only`)
- `execution_summary`: Workflow timing and success metrics

**Validation Severities**:
- **info**: Informational finding (e.g., model statistics) - safe to ignore
- **warning**: Best practice violation - consider addressing before production
- **error**: Critical issue - must be resolved before deployment

---

## Correlation IDs

Every request/response includes a `correlation_id` for tracing:

1. **Client Provides**: Send `X-Correlation-ID` header with UUID v4
2. **Auto-Generated**: Agent generates UUID if header not provided
3. **Logging**: Included in all Application Insights telemetry
4. **Error Tracing**: Reference correlation ID when contacting support

**Example with explicit correlation ID**:
```bash
curl -X POST "..." \
  -H "X-Correlation-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -d '{...}'
```

---

## Integration Patterns

### Pattern 1: Point-and-Shoot (Dry Run)

Quickly preview semantic model design without touching Fabric workspaces.

```python
import requests
import uuid

response = requests.post(
    "https://pbi-semantic-agent.prod.azurecontainerapps.io/invoke",
    headers={
        "Content-Type": "application/json",
        "X-Correlation-ID": str(uuid.uuid4())
    },
    json={
        "schema_source": {
            "type": "csv_url",
            "url": "https://example.com/data.csv"
        },
        "workspace_id": "00000000-0000-0000-0000-000000000000",
        "deployment_mode": "dry_run",
        "options": {"detect_measures": True}
    }
)

tmsl = response.json()["tmsl_output"]
print(f"Generated {len(tmsl['model']['tables'])} tables")
```

---

### Pattern 2: CI/CD Validation

Validate semantic model design in CI/CD pipeline before deploying to staging.

```yaml
# GitHub Actions example
- name: Validate Semantic Model
  run: |
    RESPONSE=$(curl -X POST "https://pbi-semantic-agent.staging.azurecontainerapps.io/invoke" \
      -H "Content-Type: application/json" \
      -d @schema-input.json)
    
    STATUS=$(echo $RESPONSE | jq -r '.status')
    if [ "$STATUS" != "success" ]; then
      echo "Validation failed"
      echo $RESPONSE | jq '.error_detail'
      exit 1
    fi
    
    # Check for errors (not just warnings)
    ERRORS=$(echo $RESPONSE | jq '[.validation_results[] | select(.severity == "error")] | length')
    if [ $ERRORS -gt 0 ]; then
      echo "Found $ERRORS validation errors"
      exit 1
    fi
```

---

### Pattern 3: Lakehouse Auto-Deploy with Manual Approval

Trigger deployment after human approval in production.

```python
import requests

# Step 1: Validate only
validate_response = requests.post(url, json={
    "schema_source": {...},
    "workspace_id": workspace_id,
    "deployment_mode": "validate_only"
})

if validate_response.json()["status"] == "success":
    # Step 2: Request approval (custom approval workflow)
    approval = request_human_approval(validate_response.json()["tmsl_output"])
    
    if approval.approved:
        # Step 3: Deploy
        deploy_response = requests.post(url, json={
            "schema_source": {...},
            "workspace_id": workspace_id,
            "deployment_mode": "auto_deploy"
        })
        
        print(f"Deployment ID: {deploy_response.json()['deployment_status']['deployment_id']}")
```

---

## Troubleshooting

### Issue: "schema_source.url field required" (HTTP 400)

**Cause**: Missing `url` field when using `csv_url` type  
**Fix**: Ensure `schema_source` has both `type: "csv_url"` and `url: "https://..."`

---

### Issue: "Workflow timeout" (HTTP 504)

**Cause**: Processing very large schema (1000+ tables) exceeded 5-minute limit  
**Fix**: Reduce scope using `table_filter` or `sample_rows` parameters, or contact support to increase timeout for specific use case

---

### Issue: "Authentication failed" (HTTP 401)

**Cause**: Managed Identity lacks permissions to Fabric workspace  
**Fix**: Ensure Managed Identity has Reader role on target workspace

---

## Next Steps

- **API Contract**: See [invocation-api.yaml](contracts/invocation-api.yaml) for complete OpenAPI specification
- **Data Model**: See [data-model.md](data-model.md) for entity definitions
- **Implementation**: See [plan.md](plan.md) for technical design details
