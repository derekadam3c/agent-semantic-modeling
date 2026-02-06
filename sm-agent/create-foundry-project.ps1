#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Creates an Azure AI Foundry Project in the existing workspace
.DESCRIPTION
    Uses Azure REST API to create an AI Foundry Project resource
#>

$ErrorActionPreference = "Stop"

$config = @{
    SubscriptionId = "6c8e23df-4aec-4ed5-bec5-79853ea6c6c6"
    ResourceGroup = "rg-pbi-agent-dev"
    Location = "eastus"
    WorkspaceName = "pbi-semantic-agent-dev"
    ProjectName = "pbi-semantic-agent-project"
    ProjectDisplayName = "PBI Semantic Agent Project"
    ProjectDescription = "AI Foundry project for Power BI Semantic Modeling Agent"
}

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Azure AI Foundry Project Creation" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Workspace: $($config.WorkspaceName)"
Write-Host "  Project Name: $($config.ProjectName)"
Write-Host "  Location: $($config.Location)"
Write-Host ""

# Step 1: Get workspace resource ID
Write-Host "[1/5] Getting workspace details..." -ForegroundColor Yellow
try {
    $workspace = az ml workspace show `
        --name $config.WorkspaceName `
        --resource-group $config.ResourceGroup `
        --query "{id:id, location:location, workspaceId:workspace_id}" `
        --output json | ConvertFrom-Json
    
    Write-Host "  ✓ Workspace found" -ForegroundColor Green
    Write-Host "    Workspace ID: $($workspace.workspaceId)" -ForegroundColor Gray
} catch {
    Write-Host "  ✗ Failed to get workspace" -ForegroundColor Red
    exit 1
}

# Step 2: Get access token
Write-Host ""
Write-Host "[2/5] Getting Azure access token..." -ForegroundColor Yellow
try {
    $token = az account get-access-token --resource https://management.azure.com --query accessToken --output tsv
    Write-Host "  ✓ Access token obtained" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Failed to get access token" -ForegroundColor Red
    exit 1
}

# Step 3: Create project using Azure ML API
Write-Host ""
Write-Host "[3/5] Creating AI Foundry Project..." -ForegroundColor Yellow

$projectResourceId = "/subscriptions/$($config.SubscriptionId)/resourceGroups/$($config.ResourceGroup)/providers/Microsoft.MachineLearningServices/workspaces/$($config.ProjectName)"

$projectBody = @{
    location = $config.Location
    identity = @{
        type = "SystemAssigned"
    }
    properties = @{
        friendlyName = $config.ProjectDisplayName
        description = $config.ProjectDescription
        hubResourceId = $workspace.id
    }
    kind = "Project"
    tags = @{
        Environment = "dev"
        Application = "PowerBI-Semantic-Agent"
        CreatedBy = "PowerShell-Script"
        CreationDate = (Get-Date -Format "yyyy-MM-dd")
    }
} | ConvertTo-Json -Depth 10

$apiVersion = "2024-04-01"
$uri = "https://management.azure.com$projectResourceId`?api-version=$apiVersion"

try {
    $headers = @{
        "Authorization" = "Bearer $token"
        "Content-Type" = "application/json"
    }
    
    $response = Invoke-RestMethod `
        -Uri $uri `
        -Method Put `
        -Headers $headers `
        -Body $projectBody `
        -TimeoutSec 120
    
    Write-Host "  ✓ Project creation initiated" -ForegroundColor Green
    Write-Host "    Project ID: $($response.id)" -ForegroundColor Gray
    
} catch {
    Write-Host "  ✗ Failed to create project" -ForegroundColor Red
    Write-Host "  Error: $_" -ForegroundColor Red
    
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $reader.BaseStream.Position = 0
        $reader.DiscardBufferedData()
        $responseBody = $reader.ReadToEnd()
        Write-Host "  Response: $responseBody" -ForegroundColor Red
    }
    exit 1
}

# Step 4: Wait for project provisioning
Write-Host ""
Write-Host "[4/5] Waiting for project provisioning..." -ForegroundColor Yellow
Write-Host "  This may take 1-2 minutes..." -ForegroundColor Gray

$maxRetries = 24  # 2 minutes with 5-second intervals
$retryCount = 0
$projectReady = $false

while ($retryCount -lt $maxRetries -and -not $projectReady) {
    Start-Sleep -Seconds 5
    $retryCount++
    
    try {
        $checkResponse = Invoke-RestMethod `
            -Uri $uri `
            -Method Get `
            -Headers $headers `
            -TimeoutSec 30
        
        $provisioningState = $checkResponse.properties.provisioningState
        
        if ($provisioningState -eq "Succeeded") {
            Write-Host "  ✓ Project provisioned successfully!" -ForegroundColor Green
            $projectReady = $true
            $projectDetails = $checkResponse
        } elseif ($provisioningState -eq "Failed") {
            Write-Host "  ✗ Project provisioning failed" -ForegroundColor Red
            Write-Host "  State: $provisioningState" -ForegroundColor Red
            exit 1
        } else {
            Write-Host "  ⏳ Provisioning... ($provisioningState) - Attempt $retryCount/$maxRetries" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  ⚠ Check failed, retrying..." -ForegroundColor Yellow
    }
}

if (-not $projectReady) {
    Write-Host "  ⚠ Provisioning timeout - check portal for status" -ForegroundColor Yellow
    Write-Host "  Portal: https://ml.azure.com" -ForegroundColor Gray
}

# Step 5: Get project details and workspace ID
Write-Host ""
Write-Host "[5/5] Retrieving project details..." -ForegroundColor Yellow

try {
    $project = az ml workspace show `
        --name $config.ProjectName `
        --resource-group $config.ResourceGroup `
        --query "{name:name, workspaceId:workspace_id, location:location, hubResourceId:hub_resource_id}" `
        --output json | ConvertFrom-Json
    
    Write-Host "  ✓ Project details retrieved" -ForegroundColor Green
    Write-Host ""
    Write-Host "================================================" -ForegroundColor Green
    Write-Host "✅ AI Foundry Project Created Successfully!" -ForegroundColor Green
    Write-Host "================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Project Details:" -ForegroundColor Cyan
    Write-Host "  Name: $($project.name)" -ForegroundColor White
    Write-Host "  Project ID: $($project.workspaceId)" -ForegroundColor Yellow
    Write-Host "  Location: $($project.location)" -ForegroundColor White
    Write-Host "  Hub: $($config.WorkspaceName)" -ForegroundColor White
    Write-Host ""
    Write-Host "📋 Next Steps:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "1. Update your agent with the Project ID:" -ForegroundColor White
    Write-Host "   .\update-agent-with-project.ps1 -ProjectId '$($project.workspaceId)'" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "2. Access your project in AI Foundry Studio:" -ForegroundColor White
    Write-Host "   https://ai.azure.com" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "3. Register your agent:" -ForegroundColor White
    Write-Host "   - Navigate to your project in AI Foundry Studio" -ForegroundColor Gray
    Write-Host "   - Go to 'Agents' section" -ForegroundColor Gray
    Write-Host "   - Add agent with endpoint:" -ForegroundColor Gray
    Write-Host "     https://pbi-semantic-agent.delightfulisland-ec56bced.eastus.azurecontainerapps.io/invoke" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "IMPORTANT: Save this Project ID for agent configuration!" -ForegroundColor Yellow
    Write-Host "Project ID: $($project.workspaceId)" -ForegroundColor Green
    Write-Host ""
    
    # Save to file for reference
    $outputFile = "foundry-project-details.txt"
    @"
Azure AI Foundry Project Details
================================
Created: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

Project Name: $($project.name)
Project ID: $($project.workspaceId)
Location: $($project.location)
Hub: $($config.WorkspaceName)
Resource Group: $($config.ResourceGroup)

Next Steps:
1. Update agent: .\update-agent-with-project.ps1 -ProjectId '$($project.workspaceId)'
2. AI Foundry Studio: https://ai.azure.com
3. Agent Endpoint: https://pbi-semantic-agent.delightfulisland-ec56bced.eastus.azurecontainerapps.io/invoke
"@ | Out-File -FilePath $outputFile -Encoding UTF8
    
    Write-Host "Project details saved to: $outputFile" -ForegroundColor Gray
    Write-Host ""
    
} catch {
    Write-Host "  ⚠ Could not retrieve project details via CLI" -ForegroundColor Yellow
    Write-Host "  Please check the portal for the Project ID" -ForegroundColor Yellow
    Write-Host "  Portal: https://ml.azure.com" -ForegroundColor Gray
}
