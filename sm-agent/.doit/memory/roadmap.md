# Project Roadmap

**Project**: Power BI Semantic Modeling & Deployment Agent
**Last Updated**: 2026-02-05
**Managed by**: `/doit.roadmapit`

## Vision

Build an autonomous AI agent that accepts dataset schemas, designs industry-standard Power BI semantic models using best practices, and deploys them to Microsoft Fabric workspaces. The MVP delivers a working Foundry-registered agent that demonstrates end-to-end flow from CSV input to validated semantic model output.

---

## Active Requirements

### P1 - Critical (Must Have for MVP)

<!-- Minimal set to deploy and test a working Foundry-registered agent -->

- [ ] Foundry Agent Registration & Deployment `[001-foundry-agent-registration]`
  - **Rationale**: Core infrastructure required to deploy agent to Azure AI Foundry and make it callable. Without this, no agent exists to test. Includes agent manifest, container deployment, and health checks.

- [ ] Agent Invocation Handler `[002-agent-invocation-handler]`
  - **Rationale**: Entry point that receives requests from Foundry and orchestrates the 8-step workflow. Essential for agent-user interaction. Handles request/response schema and error boundaries.

- [ ] CSV Schema Parser `[003-csv-schema-parser]`
  - **Rationale**: Simplest input format for MVP. Parses CSV headers and sample rows to extract schema metadata. Proves the intake step works without complex format handling.

- [ ] Basic Fact/Dimension Classifier `[004-fact-dimension-classifier]`
  - **Rationale**: Core intelligence that differentiates fact from dimension tables using simple heuristics. Demonstrates the agent's modeling capability without requiring complex analysis.

- [ ] Minimal TMSL Generator `[005-tmsl-generator]`
  - **Rationale**: Produces deployable TMSL artifacts (tables, columns, basic measures). Proves the agent can generate valid Power BI model definitions that Fabric can consume.

- [ ] Fabric Dry-Run Deployment `[006-fabric-dry-run]`
  - **Rationale**: Validates workspace connectivity and pre-deployment checks without actual deployment risk. Proves end-to-end connectivity to Fabric and closes the loop on the 8-step workflow.

### P2 - High Priority (Significant Business Value)

<!-- Features that make the agent production-ready and handle real-world scenarios -->

- [ ] SQL Schema Parser `[007-sql-schema-parser]`
  - **Rationale**: Supports SQL INFORMATION_SCHEMA exports, enabling enterprise database integration. Second most common input format after CSV.

- [ ] Lakehouse/Warehouse Schema Parser `[008-lakehouse-parser]`
  - **Rationale**: Native Fabric integration for Lakehouse and Warehouse sources. Critical for Direct Lake scenarios and Fabric-first usage.

- [ ] Relationship Inference & Validation `[009-relationship-builder]`
  - **Rationale**: Automatically detects relationships between fact/dimension tables based on key patterns. Transforms isolated tables into connected semantic models.

- [ ] Anti-Pattern Detection System `[010-anti-pattern-detector]`
  - **Rationale**: Flags circular relationships, high-cardinality issues, and performance problems. Ensures generated models follow best practices and prevents deployment of suboptimal designs.

- [ ] DAX Measure Generation `[011-measure-builder]`
  - **Rationale**: Generates common measures (SUM, COUNT, AVERAGE) for numeric columns. Makes models immediately useful for analysis without manual measure creation.

- [ ] Actual Fabric Deployment with Approval Gates `[012-fabric-deployment]`
  - **Rationale**: Moves from dry-run to actual deployment with human-in-the-loop approval for production. Required for production use per constitution governance principles.

### P3 - Medium Priority (Valuable)

<!-- Enhancements that improve model quality and user experience -->

- [ ] Date Hierarchy Detection `[013-hierarchy-date]`
  - **Rationale**: Automatically creates Year > Quarter > Month > Day hierarchies for date columns. Common pattern that improves user experience in Power BI reports.

- [ ] Geographic Hierarchy Detection `[014-hierarchy-geo]`
  - **Rationale**: Detects Country > State > City hierarchies. Enables drill-down in geographic analyses.

- [ ] Performance Optimization Recommendations `[015-performance-analyzer]`
  - **Rationale**: Analyzes measure complexity and relationship cardinality to suggest optimizations. Helps users understand performance implications before deployment.

- [ ] Direct Lake Optimization Checks `[016-direct-lake-optimizer]`
  - **Rationale**: Validates model compatibility with Direct Lake mode and suggests optimizations. Critical for Fabric-native performance benefits.

- [ ] Tableau TWB Metadata Parser `[017-tableau-parser]`
  - **Rationale**: Supports migration scenarios from Tableau to Power BI. Enables organizations to port existing Tableau semantic models.

- [ ] TMDL Generator (in addition to TMSL) `[018-tmdl-generator]`
  - **Rationale**: Modern tabular model format with better source control integration. Preferred for GitOps workflows.

### P4 - Low Priority (Nice to Have)

<!-- Advanced features for specialized scenarios -->

- [ ] Calculation Groups Support `[019-calculation-groups]`
  - **Rationale**: Enables time intelligence and complex calculation patterns. Advanced DAX feature for sophisticated models.

- [ ] Incremental Model Updates `[020-incremental-updates]`
  - **Rationale**: Supports updating existing models without full replacement. Useful for iterative refinement but not critical for initial deployments.

- [ ] Advanced Telemetry & Diagnostics `[021-telemetry]`
  - **Rationale**: Detailed performance metrics and diagnostic dashboards. Valuable for optimization but not required for basic operation.

- [ ] Multi-Model Deployment Orchestration `[022-multi-model-deploy]`
  - **Rationale**: Deploy multiple related models in coordinated fashion. Enterprise-scale feature for complex deployments.

- [ ] Custom Hierarchy Builder `[023-hierarchy-custom]`
  - **Rationale**: Detects domain-specific hierarchies beyond date/geography. Specialized feature for niche use cases.

---

## Deferred Items

<!-- Items that were considered but intentionally deferred with reason -->

| Item | Original Priority | Deferred Date | Reason |
|------|-------------------|---------------|--------|
| _No items deferred yet_ | - | - | - |

---

## Notes

- Items marked with `[###-feature-name]` reference link to feature branches for tracking
- When a feature completes via `/doit.checkin`, matching items are moved to `completed_roadmap.md`
- Use `/doit.roadmapit add [item]` to add new items
- Use `/doit.roadmapit defer [item]` to move items to deferred section
- Use `/doit.roadmapit reprioritize` to change item priorities
- P1 represents the **minimal viable agent** deployable to Azure AI Foundry for testing
- P2 makes the agent production-ready with real-world input formats and validation

---

## Notes

- Items marked with `[###-feature-name]` reference link to feature branches for tracking
- When a feature completes via `/doit.checkin`, matching items are moved to `completed_roadmap.md`
- Use `/doit.roadmapit add [item]` to add new items
- Use `/doit.roadmapit defer [item]` to move items to deferred section
- Use `/doit.roadmapit reprioritize` to change item priorities
