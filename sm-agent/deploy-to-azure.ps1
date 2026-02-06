#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Complete automated deployment of Power BI Semantic Modeling Agent to Azure AI Foundry

.DESCRIPTION
    This script automates the entire deployment process:
    1. Creates Azure Container Registry
    2. Builds and pushes Docker image
    3. Creates Azure Container Apps environment
    4. Deploys the agent container
    5. Registers agent in Azure AI Foundry

.PARAMETER ResourceGroup
    Name of the resource group (default: rg-pbi-agent-dev)

.PARAMETER Location
    Azure region (default: eastus)

.PARAMETER Environment
    Deployment environment (dev, staging, prod) (default: dev)

.EXAMPLE
    .\deploy-to-azure.ps1
    
.EXAMPLE
    .\deploy-to-azure.ps1 -Environment prod -Location westus2
#>

param(
    [Parameter(Mandatory=$false)]
    [string]$ResourceGroup = "rg-pbi-agent-dev",
    
    [Parameter(Mandatory=$false)]
    [string]$Location = "eastus",
    
    [Parameter(Mandatory=$false)]
    [ValidateSet('dev', 'staging', 'prod')]
    [string]$Environment = "dev",
    
    [Parameter(Mandatory=$false)]
    [string]$ImageTag = "1.0.0"
)

$ErrorActionPreference = "Stop"

# Map script environment names to application environment names
$appEnvironment = switch ($Environment) {
    'dev' { 'development' }
    'staging' { 'staging' }
    'prod' { 'production' }
    default { 'development' }
}

# Configuration
$config = @{
    AcrName = "pbisemanticagent"
    WorkspaceName = "pbi-semantic-agent-$Environment"
    ContainerAppEnv = "pbi-agent-env-$Environment"
    ContainerAppName = "pbi-semantic-agent"
    ImageName = "pbi-semantic-agent"
    ManagedIdentityName = "pbi-semantic-agent-$Environment-identity"
    AppInsightsName = "pbi-semantic-agent-$Environment-appins"
}

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Azure AI Foundry Agent Deployment" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Resource Group: $ResourceGroup" -ForegroundColor Gray
Write-Host "  Location: $Location" -ForegroundColor Gray
Write-Host "  Environment: $Environment" -ForegroundColor Gray
Write-Host "  Image Tag: $ImageTag" -ForegroundColor Gray
Write-Host ""

# Verify Azure CLI login
Write-Host "[1/6] Verifying Azure CLI authentication..." -ForegroundColor Yellow
try {
    $account = az account show 2>$null | ConvertFrom-Json
    Write-Host "  ✓ Logged in as: $($account.user.name)" -ForegroundColor Green
    Write-Host "  ✓ Subscription: $($account.name)" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Not logged in to Azure CLI" -ForegroundColor Red
    Write-Host "  Run 'az login' first" -ForegroundColor Red
    exit 1
}

# Step 1: Create Azure Container Registry
Write-Host ""
Write-Host "[2/6] Creating Azure Container Registry..." -ForegroundColor Yellow

$acrExists = az acr show --name $config.AcrName --resource-group $ResourceGroup 2>$null
if ($acrExists) {
    Write-Host "  ℹ ACR already exists: $($config.AcrName)" -ForegroundColor Gray
} else {
    Write-Host "  Creating ACR: $($config.AcrName)..." -ForegroundColor Gray
    az acr create `
        --name $config.AcrName `
        --resource-group $ResourceGroup `
        --location $Location `
        --sku Standard `
        --admin-enabled false `
        --tags Environment=$Environment Application=PowerBI-Semantic-Agent | Out-Null
    
    Write-Host "  ✓ ACR created successfully" -ForegroundColor Green
}

# Grant managed identity pull access to ACR
Write-Host "  Configuring ACR permissions..." -ForegroundColor Gray
$identityPrincipalId = az identity show `
    --name $config.ManagedIdentityName `
    --resource-group $ResourceGroup `
    --query principalId `
    --output tsv

$acrId = az acr show `
    --name $config.AcrName `
    --resource-group $ResourceGroup `
    --query id `
    --output tsv

# Check if role assignment exists
$roleExists = az role assignment list `
    --assignee $identityPrincipalId `
    --scope $acrId `
    --role "AcrPull" `
    --query "[0].id" `
    --output tsv 2>$null

if (-not $roleExists) {
    az role assignment create `
        --assignee $identityPrincipalId `
        --role "AcrPull" `
        --scope $acrId | Out-Null
    Write-Host "  ✓ Granted AcrPull role to managed identity" -ForegroundColor Green
} else {
    Write-Host "  ℹ AcrPull role already assigned" -ForegroundColor Gray
}

# Step 2: Build and push Docker image
Write-Host ""
Write-Host "[3/6] Building and pushing Docker image..." -ForegroundColor Yellow
Write-Host "  This may take 2-3 minutes..." -ForegroundColor Gray

$imageName = "$($config.AcrName).azurecr.io/$($config.ImageName):$ImageTag"

az acr build `
    --registry $config.AcrName `
    --image "$($config.ImageName):$ImageTag" `
    --file Dockerfile `
    . 2>&1 | Out-Null

Write-Host "  ✓ Image built and pushed: $imageName" -ForegroundColor Green

# Step 3: Create Container Apps Environment
Write-Host ""
Write-Host "[4/6] Setting up Azure Container Apps environment..." -ForegroundColor Yellow

$containerAppEnvExists = az containerapp env show `
    --name $config.ContainerAppEnv `
    --resource-group $ResourceGroup 2>$null

if ($containerAppEnvExists) {
    Write-Host "  ℹ Container Apps environment already exists" -ForegroundColor Gray
} else {
    Write-Host "  Creating Container Apps environment..." -ForegroundColor Gray
    
    $logAnalyticsId = az monitor log-analytics workspace show `
        --resource-group $ResourceGroup `
        --workspace-name "pbi-semantic-agent-$Environment-logs" `
        --query customerId `
        --output tsv
    
    $logAnalyticsKey = az monitor log-analytics workspace get-shared-keys `
        --resource-group $ResourceGroup `
        --workspace-name "pbi-semantic-agent-$Environment-logs" `
        --query primarySharedKey `
        --output tsv
    
    az containerapp env create `
        --name $config.ContainerAppEnv `
        --resource-group $ResourceGroup `
        --location $Location `
        --logs-workspace-id $logAnalyticsId `
        --logs-workspace-key $logAnalyticsKey `
        --tags Environment=$Environment Application=PowerBI-Semantic-Agent | Out-Null
    
    Write-Host "  ✓ Container Apps environment created" -ForegroundColor Green
}

# Step 4: Deploy Container App
Write-Host ""
Write-Host "[5/6] Deploying agent container..." -ForegroundColor Yellow

# Get Application Insights connection string
$appInsightsConnString = az monitor app-insights component show `
    --app $config.AppInsightsName `
    --resource-group $ResourceGroup `
    --query connectionString `
    --output tsv

# Get managed identity resource ID
$identityId = az identity show `
    --name $config.ManagedIdentityName `
    --resource-group $ResourceGroup `
    --query id `
    --output tsv

$containerAppExists = az containerapp show `
    --name $config.ContainerAppName `
    --resource-group $ResourceGroup 2>$null

if ($containerAppExists) {
    Write-Host "  Updating existing container app..." -ForegroundColor Gray
    az containerapp update `
        --name $config.ContainerAppName `
        --resource-group $ResourceGroup `
        --image $imageName `
        --set-env-vars `
            "APP_INSIGHTS_CONNECTION_STRING=$appInsightsConnString" `
            "ENVIRONMENT=$appEnvironment" `
            "USE_MANAGED_IDENTITY=true" `
            "FOUNDRY_PROJECT_ID=placeholder" | Out-Null
    
    Write-Host "  ✓ Container app updated" -ForegroundColor Green
} else {
    Write-Host "  Creating new container app..." -ForegroundColor Gray
    az containerapp create `
        --name $config.ContainerAppName `
        --resource-group $ResourceGroup `
        --environment $config.ContainerAppEnv `
        --image $imageName `
        --target-port 8000 `
        --ingress external `
        --registry-server "$($config.AcrName).azurecr.io" `
        --user-assigned $identityId `
        --registry-identity $identityId `
        --cpu 0.5 `
        --memory 1Gi `
        --min-replicas 1 `
        --max-replicas 3 `
        --env-vars `
            "APP_INSIGHTS_CONNECTION_STRING=$appInsightsConnString" `
            "ENVIRONMENT=$appEnvironment" `
            "USE_MANAGED_IDENTITY=true" `
            "FOUNDRY_PROJECT_ID=placeholder" `
        --tags Environment=$Environment Application=PowerBI-Semantic-Agent | Out-Null
    
    Write-Host "  ✓ Container app created" -ForegroundColor Green
}

# Get container app URL
$containerAppUrl = az containerapp show `
    --name $config.ContainerAppName `
    --resource-group $ResourceGroup `
    --query properties.configuration.ingress.fqdn `
    --output tsv

$containerAppUrl = "https://$containerAppUrl"

Write-Host "  ✓ Container URL: $containerAppUrl" -ForegroundColor Green

# Verify health endpoint
Write-Host "  Verifying health endpoint..." -ForegroundColor Gray
Start-Sleep -Seconds 5

try {
    $healthResponse = Invoke-RestMethod -Uri "$containerAppUrl/health" -Method Get -TimeoutSec 10
    Write-Host "  ✓ Health check passed: $($healthResponse.status)" -ForegroundColor Green
} catch {
    Write-Host "  ⚠ Health check failed (container may still be starting)" -ForegroundColor Yellow
}

# Step 5: Register Agent in AI Foundry
Write-Host ""
Write-Host "[6/6] Registering agent in Azure AI Foundry..." -ForegroundColor Yellow
Write-Host "  Creating Python registration script..." -ForegroundColor Gray

# Create temporary Python script for agent registration
$pythonScript = @"
import os
import sys
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

try:
    # Get workspace details
    workspace_name = "$($config.WorkspaceName)"
    resource_group = "$ResourceGroup"
    subscription_id = "$($account.id)"
    
    # Construct project endpoint
    project_endpoint = f"https://eastus.api.azureml.ms/api/v1.0/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.MachineLearningServices/workspaces/{workspace_name}"
    
    # Create AI Project client
    credential = DefaultAzureCredential()
    project_client = AIProjectClient(
        endpoint=project_endpoint,
        credential=credential
    )
    
    # Register agent
    print("  Registering agent with AI Foundry...")
    agent = project_client.agents.create_agent(
        name="pbi-semantic-modeling-agent",
        description="Automated Power BI semantic model generation from data schemas",
        model="gpt-4",  # Model for orchestration if needed
        instructions="Generate optimized Power BI semantic models with best-practice patterns",
        tools=[{"type": "code_interpreter"}],
        metadata={
            "version": "$ImageTag",
            "endpoint": "$containerAppUrl",
            "health_endpoint": "$containerAppUrl/health",
            "invoke_endpoint": "$containerAppUrl/invoke",
            "environment": "$Environment",
            "capabilities": ["csv_schema", "lakehouse_schema", "sql_schema", "dry_run", "deployment"]
        }
    )
    
    print(f"  ✓ Agent registered successfully!")
    print(f"  Agent ID: {agent.id}")
    print(f"  Agent Name: {agent.name}")
    
except ImportError:
    print("  ⚠ azure-ai-projects package not installed")
    print("  Run: pip install azure-ai-projects")
    sys.exit(1)
except Exception as e:
    print(f"  ⚠ Agent registration via SDK not available: {str(e)}")
    print(f"  You can manually register in the portal:")
    print(f"  https://ml.azure.com/workspaces/{workspace_name}")
    sys.exit(0)
"@

$tempPyFile = Join-Path $env:TEMP "register_agent.py"
$pythonScript | Out-File -FilePath $tempPyFile -Encoding UTF8

# Try to run Python registration
try {
    python $tempPyFile
} catch {
    Write-Host "  ℹ Python registration skipped (optional)" -ForegroundColor Gray
} finally {
    Remove-Item $tempPyFile -ErrorAction SilentlyContinue
}

# Summary
Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📦 Resources Deployed:" -ForegroundColor Yellow
Write-Host "  • Container Registry: $($config.AcrName).azurecr.io" -ForegroundColor Gray
Write-Host "  • Container Image: $imageName" -ForegroundColor Gray
Write-Host "  • Container App: $($config.ContainerAppName)" -ForegroundColor Gray
Write-Host "  • AI Foundry Workspace: $($config.WorkspaceName)" -ForegroundColor Gray
Write-Host ""
Write-Host "🌐 Endpoints:" -ForegroundColor Yellow
Write-Host "  • Agent URL: $containerAppUrl" -ForegroundColor Gray
Write-Host "  • Health: $containerAppUrl/health" -ForegroundColor Gray
Write-Host "  • API Docs: $containerAppUrl/docs" -ForegroundColor Gray
Write-Host "  • Invoke: $containerAppUrl/invoke" -ForegroundColor Gray
Write-Host ""
Write-Host "🔗 Azure Portal Links:" -ForegroundColor Yellow
Write-Host "  • AI Foundry: https://ml.azure.com/workspaces/$($config.WorkspaceName)" -ForegroundColor Gray
Write-Host "  • Container App: https://portal.azure.com/#resource/subscriptions/$($account.id)/resourceGroups/$ResourceGroup/providers/Microsoft.App/containerApps/$($config.ContainerAppName)" -ForegroundColor Gray
Write-Host "  • Application Insights: https://portal.azure.com/#resource/subscriptions/$($account.id)/resourceGroups/$ResourceGroup/providers/Microsoft.Insights/components/$($config.AppInsightsName)" -ForegroundColor Gray
Write-Host ""
Write-Host "✅ Test your deployment:" -ForegroundColor Yellow
Write-Host "  curl $containerAppUrl/health" -ForegroundColor Cyan
Write-Host ""
