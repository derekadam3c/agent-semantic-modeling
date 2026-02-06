# Research: Agent Invocation Handler

**Feature**: Agent Invocation Handler  
**Branch**: 002-agent-invocation-handler  
**Date**: 2026-02-06  
**Phase**: Phase 0 - Technical Research

## Purpose

Document technical research and design decisions for implementing the Agent Invocation Handler - the core HTTP endpoint that receives requests from Azure AI Foundry, validates inputs, orchestrates the 8-step semantic modeling workflow, and returns structured responses.

## Research Questions & Decisions

### 1. Request Validation Strategy

**Question**: How should we validate incoming requests to ensure schema compliance before starting workflow processing?

**Decision**: Use Pydantic v2 models with FastAPI automatic validation

**Rationale**:
- **Type Safety**: Pydantic provides runtime type checking with IDE autocomplete support
- **Automatic OpenAPI**: FastAPI auto-generates OpenAPI documentation from Pydantic models
- **Error Messages**: Pydantic produces detailed field-level validation errors matching FR-008 requirement
- **Performance**: Pydantic v2 uses Rust core for 5-10x faster validation than custom validators
- **Ecosystem Fit**: Already established in codebase (`src/core/config.py` uses Pydantic Settings)

**Alternatives Considered**:
- **JSON Schema validation** (rejected): Requires manual schema maintenance separate from code, no type hints for IDE
- **Marshmallow** (rejected): Slower than Pydantic v2, less integrated with FastAPI, requires separate schema definitions
- **Manual validation** (rejected): Error-prone, no automatic documentation generation, duplicates effort

**Implementation Notes**:
- Create `src/core/schemas.py` with request/response models
- Use discriminated unions for `schema_source` polymorphic type (csv_url | sql_json | lakehouse_connection)
- Leverage Pydantic validators for business rules (e.g., URL format, deployment_mode enum)

---

### 2. Workflow Orchestration Pattern

**Question**: How should we orchestrate the 8-step workflow to enable testability, error handling, and progress tracking?

**Decision**: Command/Mediator pattern with async Python and step-based execution

**Rationale**:
- **Testability**: Each workflow step is independently testable with clear input/output contracts
- **Error Handling**: Mediator captures exceptions at step boundaries and maps to structured error responses
- **Observability**: Step-level telemetry enables pinpointing failures in specific workflow phases
- **Flexibility**: New steps can be added or reordered without changing handler logic
- **Timeout Support**: Async execution enables per-step or total workflow timeouts

**Alternatives Considered**:
- **Direct sequential calls** (rejected): Tight coupling between handler and steps, difficult to add cross-cutting concerns
- **Celery/distributed tasks** (rejected): Overkill for MVP synchronous execution, adds infrastructure complexity
- **State machine library** (rejected): Over-engineered for linear 8-step pipeline, state machines better for branching workflows

**Implementation Notes**:
- Create `src/orchestration/workflow_executor.py` with `WorkflowExecutor` class
- Define `WorkflowStep` protocol in `src/orchestration/workflow_steps.py` with `execute(context) -> StepResult` signature
- Use `asyncio.timeout()` for workflow-level 5-minute timeout
- Track execution state in `WorkflowExecution` object passed through all steps

---

### 3. Error Response Structure

**Question**: What error response format should we use to provide actionable debugging information while conforming to HTTP standards?

**Decision**: RFC 7807 Problem Details JSON with custom extension fields

**Rationale**:
- **Standard**: RFC 7807 is IETF standard for HTTP API error responses, widely recognized
- **Extensible**: Supports custom fields like `correlation_id`, `workflow_step`, `remediation_hints`
- **Tool Support**: Many HTTP clients and API gateways understand RFC 7807 format
- **Consistency**: Aligns with Azure API error response patterns

**Implementation**:
```json
{
  "type": "https://agent.fabric.microsoft.com/errors/workflow-failure",
  "title": "Workflow Execution Failed",
  "status": 500,
  "detail": "Relationship analysis detected circular dependency between tables",
  "instance": "/invoke",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "workflow_step": "relationship_analysis",
  "failed_at": "2026-02-06T14:23:45Z",
  "remediation": "Remove circular foreign key constraints between Order and Customer tables",
  "affected_objects": ["Order", "Customer"]
}
```

**Alternatives Considered**:
- **Simple error message string** (rejected): Not machine-parseable, lacks structure for debugging
- **Custom error format** (rejected): No ecosystem support, requires documenting custom schema
- **GraphQL errors** (rejected): Not applicable for REST-based Foundry integration

**Implementation Notes**:
- Create `ErrorResponse` Pydantic model in `src/core/schemas.py`
- Map Python exceptions to RFC 7807 error types in `src/orchestration/error_handler.py`
- Include correlation_id in all error responses for Application Insights trace correlation

---

### 4. Correlation ID Management

**Question**: How should we handle correlation IDs for request tracing across Foundry, the agent, and downstream Fabric APIs?

**Decision**: Accept optional `X-Correlation-ID` header, generate UUID v4 if not provided, propagate to all logs and API calls

**Rationale**:
- **End-to-End Tracing**: Enables tracing requests from Foundry → Agent → Fabric with single identifier
- **Debugging**: Correlation ID in logs allows stitching together all events for a single invocation
- **Standard Practice**: X-Correlation-ID is de facto standard for distributed request tracing
- **Idempotence**: Same correlation ID can identify retry attempts vs new requests

**Alternatives Considered**:
- **Always generate internal ID** (rejected): Breaks trace continuity if Foundry already assigned ID
- **OpenTelemetry Trace ID only** (rejected): Requires OTel-aware tooling, less human-friendly than UUID
- **Require correlation ID in body** (rejected): Headers are standard location for request metadata

**Implementation Notes**:
- Add FastAPI dependency to extract `X-Correlation-ID` header or generate UUID
- Store correlation_id in request context for access by all workflow steps
- Include correlation_id as custom dimension in Application Insights telemetry
- Return correlation_id in response headers and body for client reference

---

### 5. Schema Source Router Pattern

**Question**: How should the handler route to different parsers (CSV, SQL, Lakehouse) based on schema source type?

**Decision**: Factory pattern with polymorphic schema source types and parser registry

**Rationale**:
- **Extensibility**: New schema source types (e.g., Tableau TWB) can be added without modifying handler
- **Type Safety**: Discriminated union ensures only valid configurations reach parsers
- **Testing**: Parsers can be mocked/stubbed independently for handler unit tests
- **Separation of Concerns**: Handler doesn't need knowledge of parser implementation details

**Implementation**:
```python
# src/core/schemas.py
class CsvUrlSource(BaseModel):
    type: Literal["csv_url"]
    url: HttpUrl
    sample_rows: int = 100

class SqlJsonSource(BaseModel):
    type: Literal["sql_json"]
    tables: List[TableSchema]

class LakehouseSource(BaseModel):
    type: Literal["lakehouse_connection"]
    workspace_id: UUID
    item_id: UUID

SchemaSource = Annotated[
    Union[CsvUrlSource, SqlJsonSource, LakehouseSource],
    Field(discriminator="type")
]

# src/orchestration/workflow_executor.py
PARSER_REGISTRY = {
    "csv_url": CsvParser,
    "sql_json": SqlParser,
    "lakehouse_connection": LakehouseParser
}

def get_parser(source: SchemaSource) -> SchemaParser:
    return PARSER_REGISTRY[source.type](source)
```

**Alternatives Considered**:
- **if/elif chain** (rejected): Brittle, not extensible, requires handler modification for new types
- **Separate endpoint per source type** (rejected): Violates DRY, complicates Foundry integration
- **Strategy pattern with explicit type parameter** (rejected): Less type-safe than discriminated union

---

### 6. Timeout and Background Task Handling

**Question**: How should we handle long-running workflows that may exceed HTTP timeout limits?

**Decision**: MVP uses synchronous execution with 5-minute timeout, return HTTP 504 on timeout with partial results

**Rationale**:
- **Simplicity**: Synchronous model avoids complexity of async job tracking and polling
- **Foundry Contract**: Matches expected request/response pattern for AI Foundry agents
- **Immediate Feedback**: Users get results or errors without polling separate status endpoint
- **MVP Scope**: Specification states "all processing is synchronous with timeout handling"

**Future Enhancement Path**:
- **Phase 2**: Add async processing with `HTTP 202 Accepted` + status polling endpoint
- **Implementation**: Use FastAPI BackgroundTasks for non-blocking execution
- **Status Storage**: Azure Cosmos DB or Table Storage for job status lookup by correlation_id

**Alternatives Considered**:
- **Immediate async with polling** (rejected for MVP): Adds API complexity, requires additional endpoints
- **No timeout** (rejected): Violates FR-012, can hang indefinitely on problematic schemas
- **WebSocket streaming** (rejected): Not supported by standard Azure AI Foundry agent integration

**Implementation Notes**:
- Use `asyncio.wait_for(workflow_execution(), timeout=300)` to enforce 5-minute limit
- On `asyncio.TimeoutError`, return HTTP 504 with partial results from completed steps
- Log timeout events to Application Insights with workflow progress metadata

---

## Key Takeaways

1. **Pydantic + FastAPI** provides optimized request validation with built-in documentation generation
2. **Mediator orchestration pattern** enables testable, observable workflow with clear error boundaries
3. **RFC 7807 error responses** provide standardized, machine-parseable debugging information
4. **Correlation ID propagation** enables end-to-end request tracing from Foundry through Fabric
5. **Factory pattern with discriminated unions** provides type-safe, extensible schema source routing
6. **Synchronous execution with timeout** matches MVP scope while leaving path for async enhancement

## References

- [Pydantic v2 Documentation](https://docs.pydantic.dev/)
- [FastAPI Request Validation](https://fastapi.tiangolo.com/tutorial/body/)
- [RFC 7807 Problem Details](https://datatracker.ietf.org/doc/html/rfc7807)
- [Azure API Error Guidelines](https://github.com/microsoft/api-guidelines/blob/vNext/Guidelines.md#7102-error-condition-responses)
- [Python asyncio Timeouts](https://docs.python.org/3/library/asyncio-task.html#timeouts)

## Open Questions

*None - all technical decisions resolved for MVP implementation*
