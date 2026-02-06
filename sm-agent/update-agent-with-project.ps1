#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Updates the deployed agent with the AI Foundry Project ID
.DESCRIPTION
    After creating an AI Foundry Project in the portal, run this script
    to update the container app with the real project ID and verify it works.
.PARAMETER ProjectId
    The AI Foundry Project ID (GUID) from the portal
.EXAMPLE
    .\update-agent-with-project.ps1 -ProjectId "12345678-1234-1234-1234-123456789abc"
#>

param(
    [Parameter(Mandatory=$true, HelpMessage="Enter the AI Foundry Project ID from the portal")]
    [ValidatePattern('^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$')]
    [string]$ProjectId
)

$ErrorActionPreference = "Stop"

$config = @{
    ResourceGroup = "rg-pbi-agent-dev"
    ContainerAppName = "pbi-semantic-agent"
    AgentUrl = "https://pbi-semantic-agent.delightfulisland-ec56bced.eastus.azurecontainerapps.io"
}

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "AI Foundry Agent - Project ID Update" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Resource Group: $($config.ResourceGroup)"
Write-Host "  Container App: $($config.ContainerAppName)"
Write-Host "  Project ID: $ProjectId"
Write-Host ""

# Step 1: Update container app environment variable
Write-Host "[1/4] Updating container app with Project ID..." -ForegroundColor Yellow
try {
    az containerapp update `
        --name $config.ContainerAppName `
        --resource-group $config.ResourceGroup `
        --set-env-vars "FOUNDRY_PROJECT_ID=$ProjectId" `
        --query "properties.{provisioningState:provisioningState, runningStatus:runningStatus}" `
        --output table | Out-String | Write-Host
    
    Write-Host "  ✓ Container app updated successfully" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Failed to update container app" -ForegroundColor Red
    Write-Host "  Error: $_" -ForegroundColor Red
    exit 1
}

# Step 2: Wait for container to restart
Write-Host ""
Write-Host "[2/4] Waiting for container to restart..." -ForegroundColor Yellow
Write-Host "  Waiting 45 seconds..." -ForegroundColor Gray
Start-Sleep -Seconds 45
Write-Host "  ✓ Wait complete" -ForegroundColor Green

# Step 3: Check health endpoint
Write-Host ""
Write-Host "[3/4] Verifying health endpoint..." -ForegroundColor Yellow
$healthUrl = "$($config.AgentUrl)/health"
$maxRetries = 3
$retryCount = 0
$success = $false

while ($retryCount -lt $maxRetries -and -not $success) {
    try {
        $response = Invoke-RestMethod -Uri $healthUrl -TimeoutSec 10
        
        Write-Host "  ✓ Health check successful!" -ForegroundColor Green
        Write-Host ""
        Write-Host "  Health Status:" -ForegroundColor Cyan
        Write-Host "    Status: $($response.status)"
        Write-Host "    Version: $($response.version)"
        Write-Host "    Foundry Config: $($response.config.foundry_project_id)"
        
        if ($response.config.foundry_project_id -eq $true) {
            Write-Host "    ✓ Project ID configured correctly" -ForegroundColor Green
            $success = $true
        } else {
            Write-Host "    ⚠ Project ID not reflected in health response" -ForegroundColor Yellow
        }
    } catch {
        $retryCount++
        if ($retryCount -lt $maxRetries) {
            Write-Host "  ⏳ Retry $retryCount/$maxRetries - waiting 15s..." -ForegroundColor Yellow
            Start-Sleep -Seconds 15
        } else {
            Write-Host "  ✗ Health check failed after $maxRetries attempts" -ForegroundColor Red
            Write-Host "  Error: $_" -ForegroundColor Red
            Write-Host ""
            Write-Host "  Troubleshooting:" -ForegroundColor Yellow
            Write-Host "    1. Check container logs: az containerapp logs show --name $($config.ContainerAppName) --resource-group $($config.ResourceGroup) --tail 50"
            Write-Host "    2. Check revision status: az containerapp revision list --name $($config.ContainerAppName) --resource-group $($config.ResourceGroup) --output table"
            Write-Host "    3. Visit portal: https://portal.azure.com/#resource/subscriptions/6c8e23df-4aec-4ed5-bec5-79853ea6c6c6/resourceGroups/rg-pbi-agent-dev/providers/Microsoft.App/containerApps/pbi-semantic-agent"
        }
    }
}

# Step 4: Display next steps
Write-Host ""
Write-Host "[4/4] Next Steps" -ForegroundColor Yellow
Write-Host ""

if ($success) {
    Write-Host "================================================" -ForegroundColor Green
    Write-Host "✅ Configuration Complete!" -ForegroundColor Green
    Write-Host "================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Your agent is now configured with the AI Foundry Project ID." -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "1. Register the agent in AI Foundry Studio:" -ForegroundColor White
    Write-Host "   - Open: https://ai.azure.com" -ForegroundColor Gray
    Write-Host "   - Navigate to your project" -ForegroundColor Gray
    Write-Host "   - Go to 'Agents' section" -ForegroundColor Gray
    Write-Host "   - Create/Register new agent with endpoint:" -ForegroundColor Gray
    Write-Host "     $($config.AgentUrl)/invoke" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "2. Test your agent:" -ForegroundColor White
    Write-Host "   - Health: $($config.AgentUrl)/health" -ForegroundColor Gray
    Write-Host "   - Docs: $($config.AgentUrl)/docs" -ForegroundColor Gray
    Write-Host "   - Invoke: $($config.AgentUrl)/invoke" -ForegroundColor Gray
    Write-Host ""
    Write-Host "3. Monitor with Application Insights:" -ForegroundColor White
    Write-Host "   https://portal.azure.com/#resource/subscriptions/6c8e23df-4aec-4ed5-bec5-79853ea6c6c6/resourceGroups/rg-pbi-agent-dev/providers/Microsoft.Insights/components/pbi-semantic-agent-dev-appins" -ForegroundColor Gray
    Write-Host ""
} else {
    Write-Host "================================================" -ForegroundColor Yellow
    Write-Host "⚠ Configuration Update Completed with Warnings" -ForegroundColor Yellow
    Write-Host "================================================" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "The Project ID was set, but verification failed." -ForegroundColor Yellow
    Write-Host "Please check the troubleshooting steps above." -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "Project ID: $ProjectId" -ForegroundColor Cyan
Write-Host ""
