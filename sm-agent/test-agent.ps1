#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Tests the deployed Power BI Semantic Modeling Agent
.DESCRIPTION
    Validates all agent endpoints and performs a dry-run invocation test
#>

$ErrorActionPreference = "Stop"

$config = @{
    AgentUrl = "https://pbi-semantic-agent.delightfulisland-ec56bced.eastus.azurecontainerapps.io"
}

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Power BI Semantic Modeling Agent - Test Suite" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Agent URL: $($config.AgentUrl)" -ForegroundColor Yellow
Write-Host ""

# Test 1: Health Endpoint
Write-Host "[1/3] Testing /health endpoint..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "$($config.AgentUrl)/health" -TimeoutSec 10
    Write-Host "  ✓ Health endpoint OK" -ForegroundColor Green
    Write-Host "    Status: $($health.status)" -ForegroundColor Gray
    Write-Host "    Version: $($health.version)" -ForegroundColor Gray
    Write-Host "    Environment: $($health.environment)" -ForegroundColor Gray
    
    if ($health.config.foundry_project_id) {
        Write-Host "    Foundry Project ID: ✓ Configured" -ForegroundColor Green
    } else {
        Write-Host "    Foundry Project ID: ⚠ Not configured" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ✗ Health check failed" -ForegroundColor Red
    Write-Host "  Error: $_" -ForegroundColor Red
    exit 1
}

# Test 2: OpenAPI Docs
Write-Host ""
Write-Host "[2/3] Testing /docs endpoint..." -ForegroundColor Yellow
try {
    $docs = Invoke-WebRequest -Uri "$($config.AgentUrl)/docs" -UseBasicParsing -TimeoutSec 10
    if ($docs.StatusCode -eq 200) {
        Write-Host "  ✓ API documentation available" -ForegroundColor Green
        Write-Host "    URL: $($config.AgentUrl)/docs" -ForegroundColor Gray
    }
} catch {
    Write-Host "  ⚠ Docs endpoint not available (may be disabled in prod)" -ForegroundColor Yellow
}

# Test 3: Invoke Endpoint (Dry Run)
Write-Host ""
Write-Host "[3/3] Testing /invoke endpoint (dry run)..." -ForegroundColor Yellow

$testPayload = @{
    schema_source = @{
        type = "csv_url"
        url = "https://raw.githubusercontent.com/microsoft/powerbi-desktop-samples/main/Sample%20Reports/Supplier%20Quality%20Analysis%20Sample.csv"
        sample_rows = 100
    }
    workspace_id = "00000000-0000-0000-0000-000000000000"
    deployment_mode = "dry_run"
    options = @{
        detect_measures = $true
        detect_hierarchies = $true
        target_optimization = "direct_lake"
    }
} | ConvertTo-Json -Depth 10

try {
    $headers = @{
        "Content-Type" = "application/json"
        "X-Correlation-ID" = "test-$([guid]::NewGuid())"
    }
    
    Write-Host "  Sending test request..." -ForegroundColor Gray
    $response = Invoke-RestMethod `
        -Uri "$($config.AgentUrl)/invoke" `
        -Method Post `
        -Body $testPayload `
        -Headers $headers `
        -TimeoutSec 60
    
    Write-Host "  ✓ Invoke endpoint OK" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Response Summary:" -ForegroundColor Cyan
    Write-Host "    Status: $($response.status)" -ForegroundColor Gray
    Write-Host "    Message: $($response.message)" -ForegroundColor Gray
    
    if ($response.model_definition) {
        Write-Host "    Tables Detected: $($response.model_definition.tables.Count)" -ForegroundColor Gray
        Write-Host "    Relationships: $($response.model_definition.relationships.Count)" -ForegroundColor Gray
    }
    
    if ($response.artifacts) {
        Write-Host "    TMDL Generated: $(if ($response.artifacts.tmdl) { '✓' } else { '✗' })" -ForegroundColor Gray
        Write-Host "    TMSL Generated: $(if ($response.artifacts.tmsl) { '✓' } else { '✗' })" -ForegroundColor Gray
    }
    
} catch {
    Write-Host "  ✗ Invoke endpoint failed" -ForegroundColor Red
    Write-Host "  Error: $_" -ForegroundColor Red
    
    if ($_.Exception.Response) {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Write-Host "  Status Code: $statusCode" -ForegroundColor Red
        
        try {
            $errorBody = $_.ErrorDetails.Message | ConvertFrom-Json
            Write-Host "  Error Details:" -ForegroundColor Red
            Write-Host "    $($errorBody.detail)" -ForegroundColor Red
        } catch {
            # Error body not JSON
        }
    }
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Test Results Summary" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "All critical endpoints tested." -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. If not done yet, create AI Foundry Project: https://ai.azure.com"
Write-Host "  2. Register agent in AI Foundry with invoke endpoint"
Write-Host "  3. Test agent from AI Foundry Studio playground"
Write-Host ""
Write-Host "Useful Links:" -ForegroundColor Yellow
Write-Host "  • Health: $($config.AgentUrl)/health"
Write-Host "  • Docs: $($config.AgentUrl)/docs"
Write-Host "  • Invoke: $($config.AgentUrl)/invoke"
Write-Host "  • Portal: https://portal.azure.com/#resource/subscriptions/6c8e23df-4aec-4ed5-bec5-79853ea6c6c6/resourceGroups/rg-pbi-agent-dev/providers/Microsoft.App/containerApps/pbi-semantic-agent"
Write-Host ""
