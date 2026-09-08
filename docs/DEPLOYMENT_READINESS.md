# LegalMind — Production Deployment Readiness

## Purpose

This document defines the production deployment boundary for LegalMind
without claiming deployment capabilities that were not validated in the
current Google Colab environment.

## Application Services

### Frontend

- Next.js / React
- Production build validated
- Upload and review interfaces implemented

### Backend

- FastAPI
- Application processing endpoint
- Review endpoints
- Upload endpoint
- Runtime orchestration

## Required Production Services

A production deployment should provide:

- Frontend service
- FastAPI service
- PostgreSQL
- Qdrant
- Neo4j Aura Instance01
- LangSmith observability
- Persistent encrypted storage

## Security Boundary

Production deployment requirements:

- TLS 1.2 or newer for network communication
- AES-256 or equivalent strong encryption for data at rest
- Secret management outside source code
- Reviewer/Admin RBAC
- Immutable audit logging
- Sensitive-clause masking before hosted LLM processing
- Configurable retention policy
- Mandatory legal disclaimer

These requirements are architectural/deployment requirements and are not
represented as fully infrastructure-validated by the current Colab runtime.

## Neo4j Constraint

The existing Neo4j Aura Instance01 is the required graph instance.

No replacement instance may be created.

The current instance is externally unavailable. Until it becomes available,
Neo4j-backed EvidenceGraphBuilder and full graph-backed Explainability
validation remain blocked.

## Pakistan Case Law

Pakistan statutory retrieval is validated.

A Pakistan case-law provider is not configured.

CourtListener must remain limited to the validated US prototype/evaluation
track and must not be repurposed as a Pakistan case-law provider.

## Observability

LangSmith instrumentation is present in the application/runtime path.

A production deployment should additionally verify:

- end-to-end latency
- retry counts
- token/cost telemetry
- failed workflow traces
- service health
- alerting

These deployment-level checks are not claimed as fully validated in Colab.

## Planner

Planner architecture exists in the project.

Dynamic complexity classification and complete DAG routing require an
additional runtime validation before being claimed as fully validated.

## Deployment Acceptance Checklist

Before production release:

- [ ] TLS configured and externally verified
- [ ] Encryption at rest configured and verified
- [ ] Reviewer/Admin RBAC verified
- [ ] Retention policy verified
- [ ] Secret management verified
- [ ] Existing Neo4j Aura Instance01 available
- [ ] Evidence graph path revalidated
- [ ] Explainability graph path revalidated
- [ ] Pakistan case-law provider configured and validated
- [ ] Planner dynamic DAG behavior validated
- [ ] Production observability validated
- [ ] End-to-end production smoke test passed

## Current Truthful Status

The application and submission artifacts are validated.

The above unchecked items remain deployment/provider validation items and are
not falsely marked complete.
