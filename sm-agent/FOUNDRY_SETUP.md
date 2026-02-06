# Azure AI Foundry Project Setup & Agent Registration

## Current Status
✅ Azure ML Workspace (Hub): `pbi-semantic-agent-dev`  
✅ Container App Deployed: https://pbi-semantic-agent.delightfulisland-ec56bced.eastus.azurecontainerapps.io  
⏳ AI Foundry Project: **Needs Creation**  
⏳ Agent Registration: **Pending**

---

## Step 1: Create AI Foundry Project (via Portal)

Azure AI Foundry projects must be created through the portal:

1. **Open AI Foundry Studio:**
   ```
   https://ai.azure.com
   ```

2. **Navigate to Your Workspace:**
   - Click on "All resources" or "Hubs"
   - Find and click: `pbi-semantic-agent-dev`
   - Resource Group: `rg-pbi-agent-dev`
   - Location: East US

3. **Create a New Project:**
   - Click **"+ New project"** button
   - Project name: `pbi-semantic-agent-project`
   - Hub: `pbi-semantic-agent-dev` (should be pre-selected)
   - Click **"Create"**

4. **Get the Project ID:**
   - Once created, click on the project
   - Look for "Project settings" or properties
   - Copy the **Project ID** (GUID format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)
   - Save this ID - you'll need it for the next step

---

## Step 2: Update Container App with Project ID

Once you have the Project ID from Step 1, run this PowerShell script:

```powershell
# Replace with your actual Project ID from Step 1
$ProjectId = "PASTE-PROJECT-ID-HERE"

# Update container app
az containerapp update `
    --name pbi-semantic-agent `
    --resource-group rg-pbi-agent-dev `
    --set-env-vars "FOUNDRY_PROJECT_ID=$ProjectId"

Write-Host "✓ Container app updated with Project ID: $ProjectId" -ForegroundColor Green
Write-Host "⏳ Waiting 30 seconds for container restart..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Test health endpoint
$healthUrl = "https://pbi-semantic-agent.delightfulisland-ec56bced.eastus.azurecontainerapps.io/health"
try {
    $response = Invoke-RestMethod -Uri $healthUrl
    Write-Host "✓ Agent is healthy!" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 3
} catch {
    Write-Host "⚠ Health check failed. Check container logs." -ForegroundColor Yellow
}
```

---

## Step 3: Register Agent in AI Foundry (via Portal)

Currently, the easiest way to register an agent is through the AI Foundry Studio portal:

1. **Navigate to Your Project:**
   - Open https://ai.azure.com
   - Click on your project: `pbi-semantic-agent-project`

2. **Register the Agent:**
   - In the left navigation, look for **"Agents"** or **"Deployments"**
   - Click **"+ Create"** or **"+ New agent"**
   - Fill in the details:
     - **Name**: `pbi-semantic-agent`
     - **Description**: `Power BI Semantic Modeling Agent - automated semantic model generation`
     - **Endpoint URL**: `https://pbi-semantic-agent.delightfulisland-ec56bced.eastus.azurecontainerapps.io/invoke`
     - **Authentication**: Managed Identity (select the `pbi-semantic-agent-dev-identity`)
   - Click **"Create"** or **"Register"**

3. **Test the Agent:**
   - Once registered, there should be a "Test" or "Playground" option
   - Try a simple test request to verify the agent responds

---

## Alternative: Agent Registration via Python SDK

If you prefer to automate agent registration with Python:

### Prerequisites
```powershell
pip install azure-ai-projects azure-identity
```

### Registration Script
```python
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

# Configuration (update with your values)
PROJECT_ID = "YOUR-PROJECT-ID-FROM-STEP-1"
SUBSCRIPTION_ID = "6c8e23df-4aec-4ed5-bec5-79853ea6c6c6"
RESOURCE_GROUP = "rg-pbi-agent-dev"
WORKSPACE_NAME = "pbi-semantic-agent-dev"

# Agent details
AGENT_ENDPOINT = "https://pbi-semantic-agent.delightfulisland-ec56bced.eastus.azurecontainerapps.io"

# Initialize client
credential = DefaultAzureCredential()
client = AIProjectClient(
    credential=credential,
    subscription_id=SUBSCRIPTION_ID,
    resource_group_name=RESOURCE_GROUP,
    project_name=WORKSPACE_NAME
)

# Register agent
agent = client.agents.create(
    name="pbi-semantic-agent",
    description="Power BI Semantic Modeling Agent for automated semantic model generation and deployment",
    endpoint=f"{AGENT_ENDPOINT}/invoke",
    version="1.0.1",
    tags={
        "environment": "dev",
        "application": "powerbi-semantic-modeling"
    }
)

print(f"✓ Agent registered successfully!")
print(f"  Agent ID: {agent.id}")
print(f"  Endpoint: {agent.endpoint}")
```

---

## Verification Checklist

After completing the steps above:

- [ ] AI Foundry Project created in workspace
- [ ] Project ID obtained and saved
- [ ] Container app updated with real Project ID
- [ ] Container health endpoint responding (shows `foundry_project_id: true`)
- [ ] Agent registered in AI Foundry
- [ ] Agent test successful from AI Foundry Studio

---

## Troubleshooting

### Container App "Activation Failed"
Check container logs:
```powershell
az containerapp logs show `
    --name pbi-semantic-agent `
    --resource-group rg-pbi-agent-dev `
    --type console `
    --tail 50
```

### Health Endpoint Not Responding
Check revision status:
```powershell
az containerapp revision list `
    --name pbi-semantic-agent `
    --resource-group rg-pbi-agent-dev `
    --output table
```

### Agent Not Receiving Requests
- Verify the invoke endpoint is accessible: 
  ```
  https://pbi-semantic-agent.delightfulisland-ec56bced.eastus.azurecontainerapps.io/docs
  ```
- Check Application Insights for error logs
- Verify managed identity has necessary permissions

---

## Quick Links

- **AI Foundry Studio**: https://ai.azure.com
- **Container App Portal**: https://portal.azure.com/#resource/subscriptions/6c8e23df-4aec-4ed5-bec5-79853ea6c6c6/resourceGroups/rg-pbi-agent-dev/providers/Microsoft.App/containerApps/pbi-semantic-agent
- **Application Insights**: https://portal.azure.com/#resource/subscriptions/6c8e23df-4aec-4ed5-bec5-79853ea6c6c6/resourceGroups/rg-pbi-agent-dev/providers/Microsoft.Insights/components/pbi-semantic-agent-dev-appins
- **Agent Health**: https://pbi-semantic-agent.delightfulisland-ec56bced.eastus.azurecontainerapps.io/health
- **Agent API Docs**: https://pbi-semantic-agent.delightfulisland-ec56bced.eastus.azurecontainerapps.io/docs
