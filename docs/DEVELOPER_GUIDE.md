# LegalMind — Developer Guide

## 1. Project Root

`/content/drive/MyDrive/legalmind`

## 2. Major Runtime Components

- `app/main.py`
- `app/application_runtime.py`
- `app/workflow/phase4_pakistan_runtime.py`
- `app/workflow/phase3_workflow.py`
- `app/workflow/reasoning_critic_loop.py`
- `app/research/pakistan_evidence_adapter.py`
- `app/retrieval/hybrid_retriever.py`
- `app/retrieval/evidence_ranker.py`
- `app/agents/critic_agent.py`
- `app/agents/explainability_agent.py`
- `app/report_generator.py`

## 3. Frontend

Frontend root:

`frontend/`

Technology:

- Next.js 14.2.5
- React
- production build validated

Application routes include:

- `/`
- `/api/upload`
- `/api/process`
- `/api/review/current`
- `/api/review/audit`
- `/api/review/[action]`

## 4. Persisted Application Result

`data/processed/application_runtime_result.json`

## 5. Generated Report

`outputs/reports/application_runtime.docx`

## 6. Submission Package

`submission/`

The package contains the final verified application artifacts and submission
manifest.

## 7. Frozen Architecture Rule

Do not modify, rebuild, redesign, or repurpose Phase 1–4 frozen components.

Any future extension must be implemented as an additive layer.

## 8. Neo4j Constraint

Do not create a replacement Neo4j instance.

The existing Aura Instance01 must be reused if it becomes available.

## 9. Jurisdiction Constraint

Do not use CourtListener as a Pakistan case-law provider.

Pakistan case-law integration requires a separately configured authoritative
provider.

## 10. Reproducibility

The saved Google Drive state is authoritative. Runtime validation should be
performed against the existing artifacts rather than reconstructed from
scratch.
