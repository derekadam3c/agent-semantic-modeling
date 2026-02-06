# Azure AI Foundry - Manual Agent Registration Guide

## ✅ Your Agent is Deployed and Ready!

**Agent Status**: Healthy and responding  
**Project**: pbi-semantic-agent-project (9c84093c-7e74-4437-9172-fb929ab3987b)  
**Endpoint**: https://pbi-semantic-agent.delightfulisland-ec56bced.eastus.azurecontainerapps.io

---

## Option 1: Register via AI Foundry Studio (RECOMMENDED)

### Step-by-Step Instructions:

1. **Open AI Foundry Studio**  
   Navigate to: https://ai.azure.com

2. **Select Your Project**
   - In the left sidebar, find **"Projects"**
   - Click on: **pbi-semantic-agent-project**
   - You should see: Resource Group `rg-pbi-agent-dev`, Location `East US`

3. **Create a Connection**
   - In the left navigation, find **"Management"** or **"Settings"**
   - Click on **"Connections"**
   - Click **"+ New Connection"**
   - Select **"Custom" or "API"**
   - Enter details:
     ```
     Name: pbi-semantic-agent-connection
     Category: CustomKeys
     Target: https://pbi-semantic-agent.delightfulisland-ec56bced.eastus.azurecontainerapps.io
     Metadata:
       - endpoint_type: Container App
       - authentication: Managed Identity
       - agent_version: 1.0.1
     ```

4. **Register as Agent/Model Deployment** (If available)
   - Navigate to **"Deployments"** section
   - Click **"+ Create deployment"** or **"+ Deploy model"**
   - Choose **"Custom deployment"** or **"Bring your own endpoint"**
   - Enter:
     ```
     Deployment name: pbi-semantic-modeling-agent
     Endpoint URI: https://pbi-semantic-agent.delightfulisland-ec56bced.eastus.azurecontainerapps.io/invoke
     Authentication: Managed Identity
     Client ID: 53475ffa-5155-4aae-9c9d-f96a520822fd
     ```

5. **Test in Playground**
   - Navigate to **"Playground"** or **"Chat"**
   - Look for option to select custom agent/deployment
   - Test with sample payload (see below)

---

## Option 2: Register via Azure REST API

### Using PowerShell:

```powershell
# Get access token
$token = az account get-access-token --query accessToken --output tsv

# Register connection
$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

$connectionBody = @{
    properties = @{
        category = "CustomKeys"
        target = "https://pbi-semantic-agent.delightfulisland-ec56bced.eastus.azurecontainerapps.io"
        authType = "ManagedIdentity"
        isSharedToAll = $true
        metadata = @{
            agent_name = "pbi-semantic-modeling-agent"
            agent_version = "1.0.1"
            endpoint_type = "container_app"
            capabilities = "semantic-modeling,tmdl-generation,relationship-detection"
        }
    }
} | ConvertTo-Json -Depth 10

$connectionUrl = "https://management.azure.com/subscriptions/6c8e23df-4aec-4ed5-bec5-79853ea6c6c6/resourceGroups/rg-pbi-agent-dev/providers/Microsoft.MachineLearningServices/workspaces/pbi-semantic-agent-project/connections/pbi-semantic-agent-connection?api-version=2024-04-01"

Invoke-RestMethod -Uri $connectionUrl -Method Put -Headers $headers -Body $connectionBody
```

---

## Option 3: Use as Standalone API (No Registration Required)

**Your agent is already fully functional!** You can use it directly without formal Foundry registration:

### Test Invoke Endpoint:

```powershell
# PowerShell
$payload = @{
    schema_source = @{
        type = "csv"
        url = "https://yourdata.com/file.csv"
    }
    model_name = "SalesModel"
    dry_run = $true
    generation_options = @{
        auto_detect_relationships = $true
        create_date_hierarchies = $true
        suggest_measures = $true
    }
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri "https://pbi-semantic-agent.delightfulisland-ec56bced.eastus.azurecontainerapps.io/invoke" `
    -Method Post `
    -Body $payload `
    -ContentType "application/json" | ConvertTo-Json -Depth 10
```

```bash
# cURL
curl -X POST "https://pbi-semantic-agent.delightfulisland-ec56bced.eastus.azurecontainerapps.io/invoke" \
  -H "Content-Type: application/json" \
  -d '{
    "schema_source": {
      "type": "csv",
      "url": "https://yourdata.com/file.csv"
    },
    "model_name": "SalesModel",
    "dry_run": true,
    "generation_options": {
      "auto_detect_relationships": true,
      "create_date_hierarchies": true,
      "suggest_measures": true
    }
  }'
```

```python
# Python
import requests

payload = {
    "schema_source": {
        "type": "csv",
        "url": "https://yourdata.com/file.csv"
    },
    "model_name": "SalesModel",
    "dry_run": True,
    "generation_options": {
        "auto_detect_relationships": True,
        "create_date_hierarchies": True,
        "suggest_measures": True
    }
}

response = requests.post(
    "https://pbi-semantic-agent.delightfulisland-ec56bced.eastus.azurecontainerapps.io/invoke",
    json=payload
)

print(response.json())
```

---

## Integration with AI Foundry Prompts

You can call your agent from AI Foundry prompt flow using HTTP request node:

1. **Create Prompt Flow**
   - In AI Foundry Studio, go to **"Prompt flow"**
   - Create new flow

2. **Add HTTP Node**
   - Add **HTTP** node to flow
   - Configure:
     ```
     URL: https://pbi-semantic-agent.delightfulisland-ec56bced.eastus.azurecontainerapps.io/invoke
     Method: POST
     Headers: Content-Type: application/json
     Body: (dynamic from flow inputs)
     ```

3. **Connect to Other Nodes**
   - Use agent output in subsequent LLM calls
   - Build complex AI workflows

---

## Monitoring & Troubleshooting

### View Agent Logs:

```powershell
# Container logs
az containerapp logs show --name pbi-semantic-agent --resource-group rg-pbi-agent-dev --tail 100

# Application Insights queries
# Navigate to: Application Insights > Logs
# Run KQL queries:
```

```kql
// Recent requests
requests
| where timestamp > ago(1h)
| project timestamp, name, url, success, resultCode, duration
| order by timestamp desc

// Errors
exceptions
| where timestamp > ago(1h)
| project timestamp, type, outerMessage
| order by timestamp desc
```

### Test Health:

```powershell
Invoke-RestMethod -Uri "https://pbi-semantic-agent.delightfulisland-ec56bced.eastus.azurecontainerapps.io/health"
```

### View API Docs:

Open in browser: https://pbi-semantic-agent.delightfulisland-ec56bced.eastus.azurecontainerapps.io/docs

---

## Why SDK Registration May Not Work Yet

The Azure AI Foundry platform is rapidly evolving. As of February 2026:

- ✅ **Agent deployment working**: Your container is deployed and healthy
- ✅ **Direct API calls working**: You can invoke the agent via HTTPS
- ⚠️ **SDK registration limited**: `azure-ai-projects` SDK still in preview
- ⚠️ **Portal UX varying**: Portal UI may not show all agent types yet

**Bottom line**: Your agent is production-ready for direct API usage. Formal "registration" is more about UI discoverability in AI Foundry Studio than functionality.

---

## Alternative: Register as Azure AI Model

If you want the agent to appear in AI Foundry catalog:

```powershell
# Register as custom model
az ml model create \
  --name pbi-semantic-modeling-agent \
  --version 1.0.1 \
  --type custom_model \
  --path "https://pbi-semantic-agent.delightfulisland-ec56bced.eastus.azurecontainerapps.io" \
  --resource-group rg-pbi-agent-dev \
  --workspace-name pbi-semantic-agent-project \
  --description "Power BI Semantic Modeling Agent"
```

---

## Summary: What You Can Do NOW

1. ✅ **Call agent directly** from any application using HTTP requests
2. ✅ **Monitor via Application Insights** for telemetry and diagnostics
3. ✅ **Use in Prompt Flows** by adding HTTP nodes
4. ✅ **Integrate with Power BI** deployment workflows
5. ⏳ **Wait for GA of registration APIs** for formal catalog listing

**Your agent is FULLY FUNCTIONAL - registration is optional!**

---

## Quick Test Command

```powershell
# Quick health check
Invoke-RestMethod -Uri "https://pbi-semantic-agent.delightfulisland-ec56bced.eastus.azurecontainerapps.io/health" | ConvertTo-Json

# View API documentation
Start-Process "https://pbi-semantic-agent.delightfulisland-ec56bced.eastus.azurecontainerapps.io/docs"
```

**Need help?** Check container logs or Application Insights for detailed diagnostics.
