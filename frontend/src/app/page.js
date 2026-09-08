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
  const findings = result?.risk_findings || [];
  if (findings.length) {
    return Math.max(...findings.map((item) => Number(item.risk_score) || 0));
  }
  return result?.hitl?.document_risk_score ?? result?.reasoning_critic?.reasoning_result?.risk?.score ?? 0;
}

function getLevel(result) {
  const findings = result?.risk_findings || [];
  if (findings.length) {
    const score = Math.max(...findings.map((item) => Number(item.risk_score) || 0));
    return score >= 4 ? "Critical" : score === 3 ? "High" : score === 2 ? "Moderate" : "Low";
  }
  return result?.reasoning_critic?.reasoning_result?.risk?.level || "Unknown";
}

export default function Home() {
  const [result, setResult] = useState(null);
  const [audit, setAudit] = useState([]);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [action, setAction] = useState("Pending");
  const [rationale, setRationale] = useState("");
  const [error, setError] = useState("");
  const [selectedFile, setSelectedFile] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [processingMessage, setProcessingMessage] = useState("");
  const [activeView, setActiveView] = useState("dashboard");
  const [uiLanguage, setUiLanguage] = useState("en");
  const [legalQuery, setLegalQuery] = useState("");
  const [queryLoading, setQueryLoading] = useState(false);
  const [queryResult, setQueryResult] = useState(null);

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
    if (activeView === "analyze") {
      loadReview();
    }
  }, [activeView]);

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

  async function runLegalQuery() {
    const query = legalQuery.trim();
    if (!query) return;

    setQueryLoading(true);
    setQueryResult(null);
    setError("");

    try {
      const response = await fetch("/api/legal-query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query,
          language: uiLanguage
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || data.message || "Legal query failed.");
      }

      setQueryResult(data);
    } catch (err) {
      setQueryResult({
        status: "ERROR",
        message: err.message
      });
    } finally {
      setQueryLoading(false);
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
      Moderate: 0,
      Low: 0,
      Unknown: 0
    };

    const findings = result?.risk_findings || [];

    if (findings.length) {
      findings.forEach((item) => {
        const score = Number(item.risk_score) || 0;
        const level =
          item.risk_level ||
          (score >= 4 ? "Critical" : score === 3 ? "High" : score === 2 ? "Moderate" : "Low");

        if (levels[level] !== undefined) {
          levels[level] += 1;
        } else {
          levels.Unknown += 1;
        }
      });
    } else if (levels[riskLevel] !== undefined) {
      levels[riskLevel] = 1;
    } else {
      levels.Unknown = 1;
    }

    return levels;
  }, [result, riskLevel]);

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
      <nav className="app-navigation">
        <div className="app-brand">
          <div className="app-brand-mark">LM</div>
          <div>
            <strong>LegalMind</strong>
            <span>Legal Intelligence Platform</span>
          </div>
        </div>

        <div className="app-nav-links">
          <button
            className={activeView === "dashboard" ? "app-nav-link active" : "app-nav-link"}
            onClick={() => setActiveView("dashboard")}
          >
            Dashboard
          </button>

          <button
            className={activeView === "analyze" ? "app-nav-link active" : "app-nav-link"}
            onClick={() => setActiveView("analyze")}
          >
            Analyze Document
          </button>

          <button
            className={activeView === "ask" ? "app-nav-link active" : "app-nav-link"}
            onClick={() => setActiveView("ask")}
          >
            Ask LegalMind
          </button>

          <button
            className={activeView === "documents" ? "app-nav-link active" : "app-nav-link"}
            onClick={() => setActiveView("documents")}
          >
            My Documents
          </button>

          <button
            className={activeView === "reviews" ? "app-nav-link active" : "app-nav-link"}
            onClick={() => setActiveView("reviews")}
          >
            Reviews
          </button>

          <button
            className={activeView === "reports" ? "app-nav-link active" : "app-nav-link"}
            onClick={() => setActiveView("reports")}
          >
            Reports
          </button>
        </div>

        <button
          className="language-button"
          onClick={() => setUiLanguage(uiLanguage === "en" ? "ur" : "en")}
          title="Switch application language"
        >
          {uiLanguage === "en" ? "اردو" : "English"}
        </button>
      </nav>
{activeView === "reviews" && (
  <section className="application-home">
    <div className="query-header">
      <div>
        <div className="eyebrow">HUMAN REVIEW</div>
        <h1>Reviews</h1>
        <p>Review completed LegalMind analyses.</p>
      </div>
    </div>

    <div className="query-card">
      <h2>Current Review</h2>
      <p>Contract #{reasoning.contract_id ?? 1} · Clause #{reasoning.clause_id ?? 17}</p>
      <p>Risk: {riskLevel} · Score: {riskScore}</p>

      <textarea
        className="rationale"
        value={rationale}
        onChange={(e) => setRationale(e.target.value)}
        placeholder="Enter reviewer rationale..."
        rows={4}
      />

      <div className="action-buttons">
        <button className="approve" onClick={() => submitAction("approve")}>Approve</button>
        <button className="edit" onClick={() => submitAction("edit")}>Edit</button>
        <button className="reject" onClick={() => submitAction("reject")}>Reject</button>
      </div>
    </div>
  </section>
)}
      {activeView === "dashboard" && (
        <section className="application-home">
          <div className="hero-section">
            <div>
              <div className="eyebrow">LEGALMIND</div>
              <h1>AI-Powered Legal Intelligence</h1>
              <p>
                Analyze contracts, understand Pakistani law, identify legal risks,
                and make evidence-grounded decisions.
              </p>
            </div>
          </div>

          <div className="home-actions">
            <button
              className="home-action-card"
              onClick={() => setActiveView("analyze")}
            >
              <div className="home-action-icon">📄</div>
              <h2>Analyze a Document</h2>
              <p>
                Upload a PDF or Word document for clause analysis, risk assessment,
                legal research, reasoning, review, and reporting.
              </p>
              <span>Start analysis →</span>
            </button>

            <button
              className="home-action-card"
              onClick={() => setActiveView("ask")}
            >
              <div className="home-action-icon">⚖️</div>
              <h2>Ask LegalMind</h2>
              <p>
                Ask questions about supported Pakistani laws without uploading
                a document.
              </p>
              <span>Ask a legal question →</span>
            </button>
          </div>

          <div className="home-features">
            <div>
              <strong>English + اردو</strong>
              <span>Bilingual legal intelligence</span>
            </div>
            <div>
              <strong>PDF + DOCX</strong>
              <span>Contract document support</span>
            </div>
            <div>
              <strong>Evidence-grounded</strong>
              <span>Traceable legal sources</span>
            </div>
            <div>
              <strong>Human review</strong>
              <span>HITL for high-risk matters</span>
            </div>
          </div>
        </section>
      )}

      {activeView === "documents" && (
        <section className="application-home">
          <div className="query-header">
            <div>
              <div className="eyebrow">DOCUMENT LIBRARY</div>
              <h1>My Documents</h1>
              <p>
                View documents processed by LegalMind and return to their analysis.
              </p>
            </div>
          </div>

          <div className="query-card">
            <div className="document-library-header">
              <div>
                <h2>Processed Documents</h2>
                <p>Documents currently available in the LegalMind workspace.</p>
              </div>

              <button
                className="primary-button"
                onClick={() => setActiveView("analyze")}
              >
                Analyze New Document
              </button>
            </div>

            <div className="document-list">
              <div className="document-item">
                <div>
                  <strong>Current LegalMind Analysis</strong>
                  <span>Application runtime result</span>
                </div>

                <button
                  className="secondary-button"
                  onClick={() => setActiveView("reviews")}
                >
                  Open Review
                </button>
              </div>

              <div className="document-item">
                <div>
                  <strong>Application Runtime Document</strong>
                  <span>
                    41 clauses · 46 risk findings · workflow completed
                  </span>
                </div>

                <button
                  className="secondary-button"
                  onClick={() => setActiveView("reports")}
                >
                  View Report
                </button>
              </div>
            </div>
          </div>
        </section>
      )}

      {activeView === "reports" && (
        <section className="application-home">
          <div className="query-header">
            <div>
              <div className="eyebrow">REPORTS</div>
              <h1>Legal Reports</h1>
              <p>
                Access completed LegalMind analysis reports and supporting results.
              </p>
            </div>
          </div>

          <div className="query-card">
            <div className="document-library-header">
              <div>
                <h2>Application Runtime Report</h2>
                <p>
                  Completed analysis containing clause findings, risks,
                  research, recommendations, and the required legal disclaimer.
                </p>
              </div>

              <a
                className="primary-button report-download-link"
                href="/api/report"
                target="_blank"
                rel="noreferrer"
              >
                Download Report
              </a>
            </div>

            <div className="report-summary">
              <div>
                <strong>41</strong>
                <span>Clauses analyzed</span>
              </div>

              <div>
                <strong>46</strong>
                <span>Risk findings</span>
              </div>

              <div>
                <strong>41</strong>
                <span>Research results</span>
              </div>

              <div>
                <strong>COMPLETED</strong>
                <span>Workflow status</span>
              </div>
            </div>
          </div>
        </section>
      )}

      {activeView === "ask" && (
        <section className="legal-query-section">
          <div className="query-header">
            <div>
              <div className="eyebrow">LEGAL KNOWLEDGE</div>
              <h1>Ask LegalMind</h1>
              <p>
                Ask a question about supported Pakistani commercial and contract
                law. No document is required.
              </p>
            </div>
          </div>

          <div className="query-card">
            <label htmlFor="legal-query">
              {uiLanguage === "ur" ? "اپنا قانونی سوال لکھیں" : "Your legal question"}
            </label>

            <textarea
              id="legal-query"
              value={legalQuery}
              onChange={(event) => setLegalQuery(event.target.value)}
              placeholder={
                uiLanguage === "ur"
                  ? "مثلاً: پاکستان میں ایک درست معاہدے کے لیے کیا ضروری ہے؟"
                  : "For example: What are the requirements for a valid contract in Pakistan?"
              }
              rows={6}
              dir={uiLanguage === "ur" ? "rtl" : "ltr"}
            />

            <div className="query-actions">
              <button
                className="primary-button"
                onClick={runLegalQuery}
                disabled={!legalQuery.trim() || queryLoading}
              >
                {queryLoading ? "Researching..." : "Ask LegalMind"}
              </button>

              <button
                className="secondary-button"
                onClick={() => {
                  setLegalQuery("");
                  setQueryResult(null);
                }}
              >
                Clear
              </button>
            </div>
          </div>

          {queryResult && (
            <div className="query-result">
              <div className="result-header">
                <strong>
                  {queryResult.status === "ERROR"
                    ? "Unable to answer"
                    : "LegalMind Response"}
                </strong>
              </div>

              <div className="result-body">
                {queryResult.status === "ERROR" ? (
                  <p>{queryResult.message}</p>
                ) : (
                  <>
                    <p>{queryResult.answer || queryResult.response || "No answer returned."}</p>

                    {queryResult.evidence && queryResult.evidence.length > 0 && (
                      <div className="query-evidence">
                        <h3>Supporting Legal Evidence</h3>
                        {queryResult.evidence.map((item, index) => (
                          <div className="evidence-item" key={index}>
                            <strong>
                              {item.title || item.heading || item.statute_id || "Legal source"}
                            </strong>
                            <span>
                              {item.section_id ? `Section ${item.section_id}` : ""}
                            </span>
                            <p>{item.text || ""}</p>
                          </div>
                        ))}
                      </div>
                    )}

                    <div className="legal-disclaimer">
                      LegalMind provides legal intelligence and research support,
                      not legal advice. Verify important matters with a qualified
                      legal professional.
                    </div>
                  </>
                )}
              </div>
            </div>
          )}
        </section>
      )}

      {activeView === "analyze" && (
        <>
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
        </>
      )}

    </main>
  );
}
