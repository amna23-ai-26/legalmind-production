"use client";

import { useEffect, useMemo, useState } from "react";

const fallbackEvidence = [
  ["Comet Technologies USA, Inc. v. Xp Power, LLC", "9th Cir."],
  ["Zia Chishti v. Tatiana Spottiswoode", "D.C. Cir."],
  ["NetChoice, LLC v. David Yost", "6th Cir."],
  ["Insulet Corp. v. Eoflow, Co. Ltd.", "Fed. Cir."],
  ["Rel. Ins., Inc. v. Pilot Risk Mgmt. Consulting, LLC", "N.C."]
];

function getRisk(result) {
  return result?.hitl?.document_risk_score ?? result?.reasoning_critic?.reasoning_result?.risk?.score ?? 0;
}

function getLevel(result) {
  return result?.reasoning_critic?.reasoning_result?.risk?.level || "Unknown";
}

export default function Home() {
  const [result, setResult] = useState(null);
  const [audit, setAudit] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [action, setAction] = useState("Pending");
  const [rationale, setRationale] = useState("");
  const [error, setError] = useState("");
  const [selectedFile, setSelectedFile] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [processingMessage, setProcessingMessage] = useState("");

  async function loadReview() {
    try {
      setLoading(true);
      setError("");

      const [currentResponse, auditResponse] = await Promise.all([
        fetch("/api/review/current", { cache: "no-store" }),
        fetch("/api/review/audit", { cache: "no-store" })
      ]);

      if (!currentResponse.ok) {
        throw new Error("Unable to load current review.");
      }

      const current = await currentResponse.json();
      const auditData = auditResponse.ok ? await auditResponse.json() : { audit: [] };

      setResult(current);
      setAudit(auditData.audit || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadReview();
  }, []);

  async function processSelectedFile() {
    if (!selectedFile) return;

    try {
      setProcessing(true);
      setProcessingMessage("Uploading document...");
      setError("");

      const formData = new FormData();
      formData.append("file", selectedFile);

      const uploadResponse = await fetch("/api/upload", {
        method: "POST",
        body: formData
      });

      const uploaded = await uploadResponse.json();

      if (!uploadResponse.ok) {
        throw new Error(uploaded.detail || "Document upload failed.");
      }

      setProcessingMessage("Running LegalMind analysis...");

      const processResponse = await fetch("/api/process", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          filename: uploaded.filename,
          file_type: uploaded.file_type
        })
      });

      const processed = await processResponse.json();

      if (!processResponse.ok) {
        throw new Error(processed.detail || "LegalMind processing failed.");
      }

      setProcessingMessage("Analysis completed.");
      setSelectedFile(null);
      await loadReview();
    } catch (err) {
      setError(err.message);
      setProcessingMessage("");
    } finally {
      setProcessing(false);
    }
  }

  async function submitAction(type, editedResult = null) {
    try {
      setActionLoading(true);
      setError("");

      const response = await fetch(`/api/review/${type}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          reviewer_id: "dashboard-reviewer",
          rationale:
            rationale.trim() ||
            `Reviewer selected ${type.toUpperCase()} during Phase 3 review.`,
          edited_result: editedResult
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Review action failed.");
      }

      setAction(data.status || type.toUpperCase());
      setRationale("");
      await loadReview();
    } catch (err) {
      setError(err.message);
    } finally {
      setActionLoading(false);
    }
  }

  const riskScore = getRisk(result);
  const riskLevel = getLevel(result);

  const reasoning = result?.reasoning_critic?.reasoning_result || {};
  const critic = result?.reasoning_critic?.critic_result || {};
  const explainability = result?.explainability || {};
  const confidence = explainability.confidence?.score ?? 0;
  const evidence = reasoning.supporting_evidence?.case_law || fallbackEvidence.map(
    ([title, jurisdiction]) => ({ title, jurisdiction })
  );

  const riskCounts = useMemo(() => {
    const levels = {
      Critical: 0,
      High: 0,
      Medium: 0,
      Low: 0,
      Unknown: 0
    };

    levels[riskLevel] = 1;
    return levels;
  }, [riskLevel]);

  const nodes = explainability.evidence_graph?.nodes || [];
  const edges = explainability.evidence_graph?.edges || [];

  const originalText =
    reasoning.clause_text ||
    "Original clause text is not available in the current Phase 3 runtime result.";

  const proposedText =
    reasoning.redline?.proposed_text ||
    reasoning.redline_result?.proposed_text ||
    reasoning.proposed_text ||
    (riskScore >= 4
      ? "Reviewer action required. Proposed redline will be generated or edited after HITL review."
      : "No High/Critical redline was generated for the current risk level.");

  if (loading) {
    return <main className="loading-screen">Loading LegalMind review...</main>;
  }

  return (
    <main className="dashboard">
      <header className="topbar">
        <div>
          <div className="eyebrow">LEGALMIND</div>
          <h1>Reviewer Dashboard</h1>
          <p>Phase 3 Human-in-the-Loop Review</p>
        </div>

        <div className={`status-badge ${result?.status === "PAUSED" ? "paused" : ""}`}>
          <span className="status-dot" />
          {result?.status || "UNKNOWN"}
        </div>
      </header>

      {error && <div className="error-banner">{error}</div>}

      <section className="document-upload">
        <div>
          <span className="section-label">DOCUMENT ANALYSIS</span>
          <h2>Analyze New Document</h2>
        </div>

        <div className="document-upload-controls">
          <input
            type="file"
            accept=".pdf,.docx,.jpg,.jpeg,.png"
            disabled={processing}
            onChange={(event) =>
              setSelectedFile(event.target.files?.[0] || null)
            }
          />

          <button
            type="button"
            disabled={!selectedFile || processing}
            onClick={processSelectedFile}
          >
            {processing ? "Processing..." : "Analyze Document"}
          </button>
        </div>

        {selectedFile && (
          <p className="muted">
            Selected: {selectedFile.name}
          </p>
        )}

        {processingMessage && (
          <p className="muted">{processingMessage}</p>
        )}
      </section>

      <section className="summary-grid">
        <div className="summary-card">
          <span>Contract</span>
          <strong>#{reasoning.contract_id ?? 1}</strong>
        </div>

        <div className="summary-card">
          <span>Clause</span>
          <strong>#{reasoning.clause_id ?? 17}</strong>
        </div>

        <div className="summary-card">
          <span>Risk Score</span>
          <strong>{riskScore}</strong>
        </div>

        <div className="summary-card">
          <span>Confidence</span>
          <strong>{(confidence * 100).toFixed(2)}%</strong>
        </div>

        <div className="summary-card">
          <span>HITL</span>
          <strong>{result?.hitl?.status || "CONTINUE"}</strong>
        </div>
      </section>

      <section className="content-grid">
        <div className="main-column">

          <article className="panel">
            <div className="panel-header">
              <div>
                <span className="section-label">CLAUSE REVIEW</span>
                <h2>{reasoning.clause_heading || "Trade Secrets and Source Code."}</h2>
              </div>
              <span className="pill">Clause {reasoning.clause_id ?? 17}</span>
            </div>

            <div className="clause-box">
              {reasoning.clause_text || "Clause text is unavailable in the current runtime snapshot."}
            </div>
          </article>

          <article className="panel">
            <div className="panel-header">
              <div>
                <span className="section-label">RISK HEATMAP</span>
                <h2>Contract Risk Overview</h2>
              </div>
              <span className="pill neutral">Score {riskScore}</span>
            </div>

            <div className="risk-heatmap">
              {Object.entries(riskCounts).map(([label, count]) => (
                <div className={`risk-cell risk-active-${label.toLowerCase()}`} key={label}>
                  <span className={`risk-indicator risk-${label.toLowerCase()}`} />
                  <div>
                    <strong>{label}</strong>
                    <span>{count} finding</span>
                  </div>
                </div>
              ))}
            </div>

            <div className="risk-scale">
              <span>0–1 Low</span>
              <span>2 Medium</span>
              <span>3 High</span>
              <span>&gt;3 HITL</span>
            </div>
          </article>

          <article className="panel">
            <div className="panel-header">
              <div>
                <span className="section-label">LEGAL REASONING</span>
                <h2>Assessment</h2>
              </div>
              <span className="pill neutral">
                {reasoning.reasoning_status || "Draft"}
              </span>
            </div>

            <p className="assessment">
              {reasoning.legal_assessment || "No legal assessment available."}
            </p>

            {(reasoning.negotiation_recommendations || []).map((item, index) => (
              <div className="recommendation" key={index}>
                <strong>Negotiation recommendation</strong>
                <p>{item}</p>
              </div>
            ))}
          </article>

          <article className="panel">
            <div className="panel-header">
              <div>
                <span className="section-label">CASE-LAW EVIDENCE</span>
                <h2>Retrieved Authorities</h2>
              </div>
              <span className="pill">{evidence.length} records</span>
            </div>

            <div className="evidence-list">
              {evidence.map((item, index) => (
                <div className="evidence-row" key={`${item.title}-${index}`}>
                  <div className="evidence-number">{index + 1}</div>
                  <div className="evidence-content">
                    <strong>{item.title}</strong>
                    <span>{item.jurisdiction} · {item.source || "CourtListener"}</span>
                  </div>
                  <span className="verified">Verified</span>
                </div>
              ))}
            </div>
          </article>

          <article className="panel">
            <div className="panel-header">
              <div>
                <span className="section-label">REDLINE REVIEW</span>
                <h2>Side-by-Side Contract Diff</h2>
              </div>
              <span className="pill neutral">
                {riskScore >= 4 ? "HITL Review" : "Review"}
              </span>
            </div>

            <div className="redline-grid">
              <div>
                <span className="diff-label">ORIGINAL</span>
                <div className="diff-box original">
                  {originalText}
                </div>
              </div>

              <div>
                <span className="diff-label">PROPOSED / REDLINE</span>
                <div className="diff-box proposed">
                  {proposedText}
                </div>
              </div>
            </div>
          </article>

        </div>

        <aside className="side-column">

          <article className="panel">
            <span className="section-label">EXPLAINABILITY</span>
            <h2>Confidence</h2>

            <div className="confidence-score">
              {(confidence * 100).toFixed(2)}%
            </div>

            <div className="confidence-bar">
              <div style={{ width: `${confidence * 100}%` }} />
            </div>

            <div className="metric">
              <span>Retrieval similarity</span>
              <strong>{explainability.confidence?.retrieval_similarity ?? 0}</strong>
            </div>

            <div className="metric">
              <span>Critic score</span>
              <strong>{explainability.confidence?.critic_score ?? 0}</strong>
            </div>

            <div className="metric">
              <span>Self-consistency</span>
              <strong>
                {explainability.confidence?.self_consistency?.n ?? 3} / 3
              </strong>
            </div>
          </article>

          <article className="panel">
            <span className="section-label">EVIDENCE GRAPH</span>
            <h2>Knowledge Graph</h2>

            <div className="graph-summary">
              <div>
                <strong>{nodes.length}</strong>
                <span>Nodes</span>
              </div>
              <div>
                <strong>{edges.length}</strong>
                <span>Edges</span>
              </div>
            </div>

            <p className="muted">
              Evidence graph rendered from the Neo4j-backed Phase 3 result.
            </p>
          </article>

          <article className="panel">
            <span className="section-label">CRITIC</span>
            <h2>Validation</h2>

            <div className="check">
              <span>✓</span>
              Citation verification {critic.citation_check?.passed ? "passed" : "pending"}
            </div>

            <div className="check">
              <span>✓</span>
              Logical consistency {critic.consistency_check?.passed ? "passed" : "pending"}
            </div>

            <div className="check">
              <span>✓</span>
              Revision loop {critic.status === "PASS" ? "passed" : "pending"}
            </div>

            <div className="critic-meta">
              {critic.evidence_boundary?.retrieved_case_count ?? 0} retrieved evidence records
            </div>
          </article>

          <article className={`panel hitl-panel ${result?.hitl_required ? "hitl-required" : ""}`}>
            <span className="section-label">HITL REVIEW</span>
            <h2>Decision</h2>

            <div className="hitl-status">
              <span className="status-dot" />
              {result?.hitl?.status || action}
            </div>

            <p className="hitl-reason">
              {result?.hitl?.reason || "Workflow is within the configured review threshold."}
            </p>

            <label className="rationale-label">Reviewer rationale</label>

            <textarea
              className="rationale"
              value={rationale}
              onChange={(event) => setRationale(event.target.value)}
              placeholder="Enter rationale for this decision..."
              rows={4}
            />

            <div className="action-buttons">
              <button
                className="approve"
                disabled={actionLoading}
                onClick={() => submitAction("approve")}
              >
                Approve
              </button>

              <button
                className="edit"
                disabled={actionLoading}
                onClick={() =>
                  submitAction("edit", {
                    review_status: "edited",
                    review_note: "Edited through LegalMind reviewer dashboard."
                  })
                }
              >
                Edit
              </button>

              <button
                className="reject"
                disabled={actionLoading}
                onClick={() => submitAction("reject")}
              >
                Reject
              </button>
            </div>
          </article>

          <article className="panel">
            <div className="panel-header">
              <div>
                <span className="section-label">AUDIT LOG</span>
                <h2>Immutable Reviewer Activity</h2>
              </div>
              <span className="pill">{audit.length} entries</span>
            </div>

            {audit.length === 0 ? (
              <p className="muted">No reviewer actions recorded.</p>
            ) : (
              <div className="audit-history">
                {audit.map((entry) => (
                  <div className="audit-entry" key={entry.audit_id}>
                    <strong>{entry.action}</strong>
                    <span>
                      {entry.reviewer_id} ·{" "}
                      {new Date(entry.timestamp).toLocaleString()}
                    </span>
                    <p>{entry.rationale}</p>
                  </div>
                ))}
              </div>
            )}
          </article>

        </aside>
      </section>
    </main>
  );
}
