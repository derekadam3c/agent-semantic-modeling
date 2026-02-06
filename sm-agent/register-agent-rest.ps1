#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Register Power BI Semantic Modeling Agent in Azure AI Foundry using REST API

.DESCRIPTION
    This script registers the deployed agent as a connection in Azure AI Foundry
    using direct REST API calls since the SDK APIs are still in preview.

.EXAMPLE
    .\register-agent-rest.ps1
#>

param(
    [Parameter(Mandatory=$false)]
    [string]$SubscriptionId = "6c8e23df-4aec-4ed5-bec5-79853ea6c6c6",
    
    [Parameter(Mandatory=$false)]
    [string]$ResourceGroup = "rg-pbi-agent-dev",
    
    [Parameter(Mandatory=$false)]
    [string]$ProjectName = "pbi-semantic-agent-project",
    
    [Parameter(Mandatory=$false)]
    [string]$ConnectionName = "pbi-semantic-agent-connection",
    
    [Parameter(Mandatory=$false)]
    [string]$AgentEndpoint = "https://pbi-semantic-agent.delightfulisland-ec56bced.eastus.azurecontainerapps.io"
)

$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Azure AI Foundry Agent Registration (REST API)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

Write-Host "`nConfiguration:"
Write-Host "  Subscription: $SubscriptionId"
Write-Host "  Resource Group: $ResourceGroup"
Write-Host "  Project: $ProjectName"
Write-Host "  Connection Name: $ConnectionName"
Write-Host "  Agent Endpoint: $AgentEndpoint"

# Step 1: Get access token
Write-Host "`n[1/4] Getting Azure access token..." -ForegroundColor Yellow
try {
    $token = az account get-access-token --query accessToken --output tsv
    
    if (-not $token) {
        throw "Failed to get access token"
    }
    
    Write-Host "  ✓ Access token obtained" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Failed to get access token: $_" -ForegroundColor Red
    Write-Host "`n  Please run: az login" -ForegroundColor Yellow
    exit 1
}

# Step 2: Test agent health
Write-Host "`n[2/4] Testing agent health..." -ForegroundColor Yellow
try {
    $healthUrl = "$AgentEndpoint/health"
    $health = Invoke-RestMethod -Uri $healthUrl -Method Get -TimeoutSec 10
    
    Write-Host "  ✓ Agent is healthy" -ForegroundColor Green
    Write-Host "    Status: $($health.status)"
    Write-Host "    Version: $($health.version)"
    Write-Host "    Environment: $($health.environment)"
} catch {
    Write-Host "  ✗ Agent health check failed: $_" -ForegroundColor Red
    Write-Host "`n  Please verify the agent is running and accessible." -ForegroundColor Yellow
    exit 1
}

# Step 3: Register connection in AI Foundry
Write-Host "`n[3/4] Registering agent connection..." -ForegroundColor Yellow

$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

$connectionBody = @{
    properties = @{
        category = "CustomKeys"
        target = $AgentEndpoint
        authType = "ManagedIdentity"
        isSharedToAll = $true
        metadata = @{
            agent_name = "pbi-semantic-modeling-agent"
            agent_version = "1.0.1"
            endpoint_type = "container_app"
            description = "Power BI Semantic Modeling Agent - Automated semantic model generation"
            endpoints = @{
                invoke = "$AgentEndpoint/invoke"
                health = "$AgentEndpoint/health"
                docs = "$AgentEndpoint/docs"
            }
            capabilities = @{
                semantic_modeling = $true
                tmdl_generation = $true
                tmsl_generation = $true
                auto_relationships = $true
                hierarchy_detection = $true
                measure_suggestions = $true
            }
            data_sources = @("csv", "sql", "lakehouse", "tableau")
            managed_identity_client_id = "53475ffa-5155-4aae-9c9d-f96a520822fd"
        }
    }
} | ConvertTo-Json -Depth 10

$connectionUrl = "https://management.azure.com/subscriptions/$SubscriptionId/resourceGroups/$ResourceGroup/providers/Microsoft.MachineLearningServices/workspaces/$ProjectName/connections/$ConnectionName`?api-version=2024-04-01"

try {
    Write-Host "  Creating connection: $ConnectionName" -ForegroundColor Gray
    
    $response = Invoke-RestMethod `
        -Uri $connectionUrl `
        -Method Put `
        -Headers $headers `
        -Body $connectionBody `
        -ErrorAction Stop
    
    Write-Host "  ✓ Connection registered successfully" -ForegroundColor Green
    Write-Host "    Connection ID: $($response.id)" -ForegroundColor Gray
    
    $connectionCreated = $true
    
} catch {
    $errorDetails = $_.ErrorDetails.Message | ConvertFrom-Json -ErrorAction SilentlyContinue
    
    if ($errorDetails.error.code -eq "WorkspaceConnectionAlreadyExists") {
        Write-Host "  ⚠ Connection already exists - updating..." -ForegroundColor Yellow
        
        try {
            $response = Invoke-RestMethod `
                -Uri $connectionUrl `
                -Method Patch `
                -Headers $headers `
                -Body $connectionBody `
                -ErrorAction Stop
                
            Write-Host "  ✓ Connection updated successfully" -ForegroundColor Green
            $connectionCreated = $true
        } catch {
            Write-Host "  ✗ Failed to update connection: $_" -ForegroundColor Red
            $connectionCreated = $false
        }
    } else {
        Write-Host "  ✗ Failed to register connection: $_" -ForegroundColor Red
        Write-Host "`n  Error details:" -ForegroundColor Yellow
        Write-Host "  $($_.ErrorDetails.Message)" -ForegroundColor Yellow
        $connectionCreated = $false
    }
}

# Step 4: Verify registration
Write-Host "`n[4/4] Verifying registration..." -ForegroundColor Yellow

if ($connectionCreated) {
    try {
        $listUrl = "https://management.azure.com/subscriptions/$SubscriptionId/resourceGroups/$ResourceGroup/providers/Microsoft.MachineLearningServices/workspaces/$ProjectName/connections?api-version=2024-04-01"
        
        $connections = Invoke-RestMethod `
            -Uri $listUrl `
            -Method Get `
            -Headers $headers
        
        $agentConnection = $connections.value | Where-Object { $_.name -eq $ConnectionName }
        
        if ($agentConnection) {
            Write-Host "  ✓ Agent connection verified in project" -ForegroundColor Green
            Write-Host "    Name: $($agentConnection.name)" -ForegroundColor Gray
            Write-Host "    Type: $($agentConnection.properties.category)" -ForegroundColor Gray
            Write-Host "    Target: $($agentConnection.properties.target)" -ForegroundColor Gray
        } else {
            Write-Host "  ⚠ Connection created but not found in list" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  ⚠ Could not verify connection: $_" -ForegroundColor Yellow
    }
}

# Summary
Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "  Registration Summary" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

if ($connectionCreated) {
    Write-Host "`n✓ Agent registration completed!" -ForegroundColor Green
    
    Write-Host "`nNext Steps:"
    Write-Host "  1. Open AI Foundry Studio: https://ai.azure.com"
    Write-Host "  2. Navigate to project: $ProjectName"
    Write-Host "  3. Go to Management > Connections"
    Write-Host "  4. Look for connection: $ConnectionName"
    Write-Host "`nAgent Endpoints:"
    Write-Host "  • Invoke: $AgentEndpoint/invoke"
    Write-Host "  • Health: $AgentEndpoint/health"
    Write-Host "  • Docs: $AgentEndpoint/docs"
    
    Write-Host "`nTest Command:"
    Write-Host @"
  `$payload = @{
      schema_source = @{
          type = "csv"
          url = "https://yourdata.com/file.csv"
      }
      model_name = "TestModel"
      dry_run = `$true
  } | ConvertTo-Json
  
  Invoke-RestMethod -Uri "$AgentEndpoint/invoke" ``
      -Method Post ``
      -Body `$payload ``
      -ContentType "application/json"
"@
    
} else {
    Write-Host "`n⚠ Agent registration encountered issues" -ForegroundColor Yellow
    Write-Host "`nAlternative Options:"
    Write-Host "  1. Use agent directly via HTTP endpoint (no registration needed)"
    Write-Host "  2. Manually create connection in AI Foundry Studio portal"
    Write-Host "  3. Contact Azure support for assistance"
    Write-Host "`nYour agent is still fully functional at:"
    Write-Host "  $AgentEndpoint/invoke"
}

Write-Host "`n============================================================" -ForegroundColor Cyan
