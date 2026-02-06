# Research: Foundry Agent Registration & Deployment

**Feature**: 001-foundry-agent-registration  
**Date**: 2026-02-05  
**Status**: Complete

## Overview

This document captures research outcomes and technology decisions for implementing Azure AI Foundry agent registration and deployment capabilities for the Power BI Semantic Modeling Agent.

## Research Tasks Completed

### 1. Azure AI Foundry Agent Registration Patterns

**Decision**: Use Azure AI Projects SDK (`azure-ai-projects`) with agent manifest pattern for registration.

**Rationale**:
- Official Microsoft SDK provides first-class support for agent registration and lifecycle management
- Manifest-based approach allows declarative configuration of agent metadata, input/output schemas, and endpoints
- SDK handles authentication, retries, and error handling according to Azure best practices
- Supports both code-first and configuration-first workflows

**Alternatives Considered**:
- **Direct REST API calls**: Rejected due to lack of SDK conveniences (retry logic, authentication helpers, typed responses)
- **Azure CLI automation**: Rejected as not suitable for programmatic deployment pipelines
- **Custom agent orchestration**: Rejected as reinventing capabilities already provided by Foundry

**References**:
- [Azure AI Projects SDK Documentation](https://learn.microsoft.com/azure/ai-services/agents/)
- [Agent registration best practices](https://learn.microsoft.com/azure/ai-studio/how-to/deploy-models-custom)

---

### 2. Container Image Strategy for Agent Packaging

**Decision**: Multi-stage Docker build with Python 3.11-slim base, FastAPI for HTTP interface, and organized dependency layers.

**Rationale**:
- Multi-stage builds minimize final image size (target <2GB) by separating build dependencies from runtime
- Python slim base provides necessary system libraries while reducing attack surface
- FastAPI is lightweight, async-capable, and well-suited for agent HTTP interfaces
- Layer organization (system deps → Python deps → application code) optimizes caching and rebuild times

**Implementation Details**:
- **Stage 1**: Build dependencies (compile wheels for packages like `cryptography`, `lxml`)
- **Stage 2**: Runtime - copy built wheels and install runtime-only dependencies
- **Health endpoint**: `/health` (GET) returns `200 OK` with JSON payload `{"status": "healthy", "version": "x.y.z"}`
- **Invocation endpoint**: `/invoke` (POST) accepts JSON request body with schema and workspace ID

**Alternatives Considered**:
- **Single-stage build**: Rejected due to larger image size (includes build tools in final image)
- **Distroless base**: Rejected due to debugging complexity and Python tooling compatibility
- **Flask instead of FastAPI**: Rejected as FastAPI provides better async support and automatic OpenAPI schema generation

**References**:
- [Docker Python best practices](https://docs.docker.com/language/python/build-images/)
- [Multi-stage builds](https://docs.docker.com/build/building/multi-stage/)

---

### 3. Managed Identity Setup and Fabric Workspace Access

**Decision**: Use system-assigned managed identity for agent authentication to Fabric, with Terraform-managed role assignments for workspace access.

**Rationale**:
- System-assigned identity lifecycle is tied to agent resource (auto-cleanup on deletion)
- Eliminates need to manage secrets or rotate credentials
- Terraform enables infrastructure-as-code for role assignments (Contributor on Fabric workspace)
- Supports least-privilege principle (grant only necessary permissions per environment)

**Implementation Details**:
- Identity created during agent registration in Foundry
- Role assignments: `Fabric Workspace Admin` or `Fabric Contributor` depending on environment
- Validation: Agent checks workspace access at startup and before each invocation
- Error handling: Permission errors return HTTP 403 with diagnostic message identifying missing role

**Alternatives Considered**:
- **User-assigned identity**: Rejected as adds management overhead and doesn't provide lifecycle benefits for single-agent use case
- **Service principal with client secret**: Rejected due to secret rotation requirements and increased security risk
- **User credentials (OAuth)**: Rejected as violates autonomous operation principle (requires user login)

**References**:
- [Managed identities for Azure resources](https://learn.microsoft.com/azure/active-directory/managed-identities-azure-resources/)
- [Fabric workspace access control](https://learn.microsoft.com/fabric/security/workspace-access)

---

### 4. Logging and Observability Integration

**Decision**: Structured JSON logging to Azure Application Insights using OpenTelemetry SDK with correlation IDs for distributed tracing.

**Rationale**:
- Application Insights is Azure-native and integrates well with Foundry monitoring
- OpenTelemetry provides vendor-neutral instrumentation and future-proofs observability
- Correlation IDs enable end-to-end trace from Foundry invocation → agent execution → Fabric deployment
- Structured JSON logs support advanced querying in Kusto (Log Analytics)

**Implementation Details**:
- Log levels: DEBUG (dev), INFO (staging/prod), ERROR (always)
- Correlation ID: Propagated from Foundry request header `X-Correlation-ID`
- Metrics: Request count, duration (p50/p95/p99), error rate, health check latency
- Custom dimensions: agent_version, workspace_id, invocation_id, operation_name

**Alternatives Considered**:
- **Azure Monitor Logs directly**: Rejected as lacks distributed tracing capabilities
- **Third-party APM (Datadog, New Relic)**: Rejected to avoid external dependencies and additional costs
- **Simple file logging**: Rejected as doesn't support aggregation or alerting

**References**:
- [Application Insights for Python](https://learn.microsoft.com/azure/azure-monitor/app/opencensus-python)
- [OpenTelemetry Python SDK](https://opentelemetry.io/docs/instrumentation/python/)

---

### 5. Deployment Strategy and Versioning

**Decision**: Blue-green deployment with semantic versioning (MAJOR.MINOR.PATCH) and approval gates for production using GitHub Actions workflows.

**Rationale**:
- Blue-green enables zero-downtime deployments and instant rollback on failure
- Semantic versioning clearly communicates breaking changes (major), features (minor), fixes (patch)
- GitHub Actions provides native Azure integration and approval workflows
- Approval gates satisfy constitution requirement for human-in-the-loop production deployments

**Implementation Details**:
- **Dev environment**: Auto-deploy on merge to main (no approval required)
- **Staging environment**: Auto-deploy on tag push (e.g., `v1.1.0-rc.1`)
- **Production environment**: Manual approval required (designated approvers in GitHub)
- **Rollback**: Redeploy previous version tag, old version kept running until new passes health check
- **Version detection**: Tag from Git (e.g., `git describe --tags`) embedded in container image and health response

**Alternatives Considered**:
- **Canary deployment**: Rejected as adds complexity for MVP (can add post-MVP)
- **Rolling update**: Rejected as doesn't provide instant rollback capability
- **Manual deployment scripts**: Rejected as doesn't scale and increases error risk

**References**:
- [Blue-green deployment pattern](https://learn.microsoft.com/azure/architecture/patterns/blue-green-deployment)
- [GitHub Actions deployment protection rules](https://docs.github.com/actions/deployment/targeting-different-environments/using-environments-for-deployment)

---

### 6. Health Check and Monitoring Design

**Decision**: HTTP health endpoint with detailed status checks (application status, Fabric connectivity, resource usage) and 5-second timeout.

**Rationale**:
- Foundry requires health endpoint for agent lifecycle management (determines when agent is ready/degraded)
- Detailed checks enable proactive issue detection (e.g., Fabric API unreachable)
- 5-second timeout balances responsiveness with thorough validation
- Standardized JSON response enables automated monitoring and alerting

**Implementation Details**:
- **Endpoint**: `GET /health`
- **Response format**:
  ```json
  {
    "status": "healthy",  // healthy | degraded | unhealthy
    "version": "1.0.0",
    "checks": {
      "application": "healthy",
      "fabric_connectivity": "healthy",
      "memory_usage_mb": 512,
      "uptime_seconds": 3600
    },
    "timestamp": "2026-02-05T12:34:56Z"
  }
  ```
- **Status thresholds**:
  - `healthy`: All checks pass, memory <80% limit
  - `degraded`: Non-critical check fails (e.g., Fabric API slow but reachable)
  - `unhealthy`: Critical check fails (e.g., Fabric API unreachable, memory >95%)
- **Timeout**: Return partial status if checks exceed 5s (prevents cascade failures)

**Alternatives Considered**:
- **Simple 200 OK response**: Rejected as doesn't provide diagnostic information
- **Separate liveness/readiness endpoints (Kubernetes pattern)**: Rejected as Foundry doesn't require this distinction
- **Detailed database health checks**: N/A (agent is stateless)

**References**:
- [Health check pattern](https://learn.microsoft.com/azure/architecture/patterns/health-endpoint-monitoring)
- [HTTP health check best practices](https://tools.ietf.org/id/draft-inadarei-api-health-check-06.html)

---

## Summary of Key Technology Decisions

| Area | Decision | Key Rationale |
|------|----------|---------------|
| **Foundry SDK** | azure-ai-projects | Official SDK, manifest pattern, auth helpers |
| **Container Base** | python:3.11-slim | Balance of size, compatibility, security |
| **HTTP Framework** | FastAPI | Async support, auto schema, lightweight |
| **Authentication** | System-assigned managed identity | No secrets, auto lifecycle, least privilege |
| **Observability** | Application Insights + OpenTelemetry | Azure-native, distributed tracing, advanced querying |
| **Deployment** | Blue-green with GitHub Actions | Zero downtime, approval gates, instant rollback |
| **Versioning** | Semantic versioning (Git tags) | Clear communication, automated in CI/CD |

---

## Open Questions Resolution

**Q: Can Foundry handle custom Python agent containers?**  
**A**: Yes, confirmed via Azure AI Projects SDK documentation - Foundry supports custom containers with HTTP endpoints for health and invocation.

**Q: What permission level is needed for Fabric workspace operations?**  
**A**: `Fabric Workspace Admin` or `Fabric Contributor` role required for semantic model deployment - validated in Fabric RBAC documentation.

**Q: How are in-flight requests handled during deployment?**  
**A**: Foundry supports graceful shutdown - agent receives SIGTERM, completes in-flight requests (up to 30s grace period), then terminates. New requests route to new version.

**Q: What container registry should be used?**  
**A**: Azure Container Registry (ACR) - integrates with Foundry, supports managed identity pull, provides vulnerability scanning.

---

## Next Steps

Research complete. Ready to proceed to Phase 1 (data model and contracts generation).
