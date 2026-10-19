import {
  readinessApi,
  formatAnalysisDate,
  formatCareerLevel,
  type AnalysisDetailResponse,
  type AnalysisReportResponse,
  type SkillResultDetailItem,
} from "./readinessApi";

export interface ReportGenerationData {
  analysisId: string;
  roleName: string;
  careerLevel?: string;
  domainName?: string;
  studentName?: string;
  generatedDate: string;
  readinessScore: number;
  tier: string;
  interpretation?: string;
  summaryText: string;
  totalRequirements: number;
  satisfiedCount: number;
  partialCount: number;
  missingCount: number;
  highestPrioritySkill?: {
    skillName: string;
    gap?: number;
    priorityScore?: number;
    explanation?: string;
  };
  skills: {
    name: string;
    matchedName?: string;
    requiredProficiency: string;
    status: "Met" | "Partial" | "Missing";
    explanation?: string;
  }[];
  priorities: {
    rank: number;
    name: string;
    gap?: number;
    priorityScore?: number;
    explanation?: string;
  }[];
}

// Maps backend result statuses to clean, restrained academic status labels
function normalizeReportStatus(status?: string, matchType?: string): "Met" | "Partial" | "Missing" {
  const norm = (status || "").toUpperCase();
  if (norm === "COVERED" || norm === "SATISFIED" || norm === "MET" || matchType === "EXACT") {
    return "Met";
  }
  if (
    norm === "PARTIALLY_COVERED" ||
    norm === "PARTIAL" ||
    norm === "PARTIALLY_MET" ||
    matchType === "PARTIAL_RELATIONSHIP" ||
    matchType === "RELATIONSHIP"
  ) {
    return "Partial";
  }
  return "Missing";
}

// Formats capability gap percentages cleanly for report display
function formatGapValue(gap?: number | null): string {
  if (gap === undefined || gap === null || isNaN(Number(gap))) return "—";
  const num = Number(gap);
  if (num <= 0) return "0%";
  if (num <= 1) return `${Math.round(num * 100)}%`;
  return `${Math.round(num)}%`;
}

// Formats priority scores cleanly to at most one decimal place
function formatPriorityScore(score?: number | null): string {
  if (score === undefined || score === null || isNaN(Number(score))) return "—";
  const num = Number(score);
  return Number.isInteger(num) ? num.toString() : num.toFixed(1);
}

// Escapes special HTML characters to prevent layout breakage or script injection
function escapeHtml(str?: string | null): string {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// Generates self-contained HTML for a clean, academic two-page Career Readiness Report
export function generateCareerReadinessReportHtml(data: ReportGenerationData): string {
  const roundedScore = Math.round(data.readinessScore);
  const scorePercent = Math.min(100, Math.max(0, roundedScore));
  const sanitizedRole = data.roleName.replace(/[^\w\s-]/g, "").trim();
  const dateFormatted = data.generatedDate;
  const shortId = data.analysisId.slice(0, 8).toUpperCase();

  const topPriority = data.highestPrioritySkill || (data.priorities.length > 0 ? {
    skillName: data.priorities[0].name,
    gap: data.priorities[0].gap,
    priorityScore: data.priorities[0].priorityScore,
    explanation: data.priorities[0].explanation,
  } : null);

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Career Readiness Assessment — ${sanitizedRole}</title>
  <style>
    @page {
      size: A4 portrait;
      margin: 14mm 16mm;
    }
    *, *::before, *::after {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      color: #1e293b;
      background: #f8fafc;
      line-height: 1.45;
      font-size: 12px;
      -webkit-font-smoothing: antialiased;
    }

    /* Screen-only action toolbar */
    .preview-toolbar {
      position: sticky;
      top: 0;
      z-index: 100;
      background: #0f172a;
      color: #f8fafc;
      padding: 10px 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    .preview-toolbar-title {
      font-size: 13px;
      font-weight: 600;
    }
    .preview-toolbar-actions {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .btn {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px 14px;
      border-radius: 5px;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      text-decoration: none;
      border: 1px solid transparent;
      transition: background 0.15s ease;
    }
    .btn-primary {
      background: #4f46e5;
      color: #ffffff;
      border-color: #4338ca;
    }
    .btn-primary:hover {
      background: #4338ca;
    }
    .btn-secondary {
      background: #ffffff;
      color: #1e293b;
      border-color: #cbd5e1;
    }
    .btn-secondary:hover {
      background: #f1f5f9;
    }

    /* Preview page container */
    .report-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 24px 0 40px;
      gap: 20px;
    }

    /* Fixed A4 Page Dimensions (fits 2 pages exactly without trailing page spillover) */
    .report-page {
      width: 210mm;
      min-height: 272mm;
      max-height: 272mm;
      background: #ffffff;
      padding: 16mm 18mm;
      border: 1px solid #cbd5e1;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.08);
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      overflow: hidden;
      page-break-after: always;
      break-after: page;
    }
    .page-2 {
      page-break-after: avoid;
      break-after: avoid;
    }

    /* Academic Header */
    .academic-header {
      border-bottom: 1.5px solid #e2e8f0;
      padding-bottom: 10px;
      margin-bottom: 16px;
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
    }
    .brand-title {
      font-size: 13px;
      font-weight: 800;
      letter-spacing: 0.04em;
      color: #4f46e5;
      text-transform: uppercase;
    }
    .brand-sub {
      font-size: 10px;
      color: #64748b;
      margin-top: 2px;
      font-weight: 500;
    }
    .header-ref {
      font-size: 10px;
      color: #64748b;
      text-align: right;
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    }

    /* Document Title Block */
    .report-title-block {
      margin-bottom: 14px;
    }
    .report-title {
      font-size: 18px;
      font-weight: 800;
      color: #0f172a;
      letter-spacing: -0.01em;
    }
    .report-subtitle {
      font-size: 11px;
      color: #64748b;
      margin-top: 2px;
    }

    /* Metadata Summary Box */
    .meta-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 10px;
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 6px;
      padding: 10px 14px;
      margin-bottom: 14px;
    }
    .meta-item {
      display: flex;
      flex-direction: column;
    }
    .meta-label {
      font-size: 9px;
      font-weight: 700;
      color: #64748b;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .meta-value {
      font-size: 11px;
      font-weight: 700;
      color: #0f172a;
      margin-top: 2px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    /* Overall Readiness Score Card */
    .score-card {
      border: 1px solid #e2e8f0;
      border-radius: 6px;
      background: #ffffff;
      padding: 14px 18px;
      margin-bottom: 14px;
      display: grid;
      grid-template-columns: 140px 1fr;
      gap: 20px;
      align-items: center;
    }
    .score-number-box {
      border-right: 1px solid #e2e8f0;
      padding-right: 16px;
      text-align: center;
    }
    .score-num {
      font-size: 38px;
      font-weight: 800;
      color: #4f46e5;
      line-height: 1;
      letter-spacing: -0.02em;
    }
    .score-caption {
      font-size: 9.5px;
      font-weight: 700;
      color: #64748b;
      text-transform: uppercase;
      margin-top: 4px;
      letter-spacing: 0.04em;
    }
    .score-details-box {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    .tier-badge {
      display: inline-block;
      align-self: flex-start;
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 10px;
      font-weight: 700;
      background: #eef2ff;
      color: #4338ca;
      border: 1px solid #c7d2fe;
    }
    .progress-bar-track {
      width: 100%;
      height: 7px;
      background: #e2e8f0;
      border-radius: 4px;
      overflow: hidden;
      margin-top: 2px;
    }
    .progress-bar-fill {
      height: 100%;
      background: #4f46e5;
      border-radius: 4px;
      width: ${scorePercent}%;
    }
    .score-interpretation {
      font-size: 11px;
      color: #334155;
      line-height: 1.4;
      margin-top: 2px;
    }

    /* Section Headings */
    .section-heading {
      font-size: 11px;
      font-weight: 700;
      color: #475569;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      border-bottom: 1px solid #e2e8f0;
      padding-bottom: 4px;
      margin: 12px 0 8px;
    }

    /* Coverage Metric Boxes */
    .metrics-row {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 10px;
      margin-bottom: 14px;
    }
    .metric-card {
      border: 1px solid #e2e8f0;
      border-radius: 6px;
      padding: 10px 12px;
      background: #ffffff;
      text-align: center;
    }
    .metric-number {
      font-size: 20px;
      font-weight: 800;
      color: #0f172a;
      line-height: 1;
    }
    .metric-title {
      font-size: 9px;
      font-weight: 700;
      color: #64748b;
      text-transform: uppercase;
      margin-top: 4px;
      letter-spacing: 0.03em;
    }

    /* Summary Narrative Card */
    .narrative-card {
      border: 1px solid #e2e8f0;
      border-radius: 6px;
      background: #ffffff;
      padding: 12px 14px;
      margin-bottom: 12px;
    }
    .narrative-text {
      font-size: 11.5px;
      color: #334155;
      line-height: 1.5;
    }

    /* Priority Callout */
    .priority-callout {
      border: 1px solid #e2e8f0;
      border-left: 3.5px solid #4f46e5;
      border-radius: 5px;
      padding: 10px 14px;
      background: #f8fafc;
      margin-bottom: 12px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 14px;
    }
    .priority-callout-title {
      font-size: 11.5px;
      font-weight: 700;
      color: #0f172a;
    }
    .priority-callout-sub {
      font-size: 10px;
      color: #64748b;
      margin-top: 1px;
    }

    /* Research Disclaimer */
    .academic-disclaimer {
      font-size: 9.5px;
      color: #64748b;
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 5px;
      padding: 8px 12px;
      line-height: 1.4;
      margin-top: 6px;
    }

    /* Table Styles */
    .table-wrapper {
      border: 1px solid #e2e8f0;
      border-radius: 6px;
      overflow: hidden;
      margin-bottom: 12px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 11px;
      text-align: left;
    }
    th {
      background: #f8fafc;
      color: #475569;
      font-size: 9.5px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      padding: 8px 10px;
      border-bottom: 1px solid #e2e8f0;
    }
    td {
      padding: 7px 10px;
      border-bottom: 1px solid #f1f5f9;
      vertical-align: top;
      color: #334155;
      line-height: 1.35;
    }
    tr:last-child td {
      border-bottom: none;
    }
    tr:nth-child(even) td {
      background: #fafafa;
    }

    /* Status Badges */
    .badge {
      display: inline-block;
      padding: 2px 7px;
      border-radius: 4px;
      font-size: 9.5px;
      font-weight: 700;
      letter-spacing: 0.02em;
    }
    .badge-met {
      background: #f0fdf4;
      color: #166534;
      border: 1px solid #bbf7d0;
    }
    .badge-partial {
      background: #fefce8;
      color: #854d0e;
      border: 1px solid #fef08a;
    }
    .badge-missing {
      background: #fef2f2;
      color: #991b1b;
      border: 1px solid #fecaca;
    }

    /* Priorities table and list styles (Page 2) */
    .priorities-table th {
      background: #f8fafc;
      color: #475569;
      font-size: 9px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      padding: 7px 10px;
      border-bottom: 1px solid #e2e8f0;
    }
    .priorities-table td {
      padding: 6px 10px;
      border-bottom: 1px solid #f1f5f9;
      vertical-align: middle;
      font-size: 11px;
      color: #334155;
      line-height: 1.35;
    }
    .priority-rank-badge {
      display: inline-block;
      font-size: 9.5px;
      font-weight: 800;
      color: #4338ca;
      background: #eef2ff;
      border: 1px solid #c7d2fe;
      border-radius: 4px;
      padding: 1px 6px;
      min-width: 24px;
      text-align: center;
    }
    .empty-priorities-box {
      border: 1px solid #e2e8f0;
      border-radius: 6px;
      background: #f8fafc;
      padding: 12px 14px;
      font-size: 11px;
      color: #64748b;
      line-height: 1.45;
      margin-bottom: 12px;
    }

    /* Status Legend */
    .legend-row {
      display: flex;
      align-items: center;
      gap: 14px;
      font-size: 9.5px;
      color: #64748b;
      border-top: 1px solid #e2e8f0;
      padding-top: 8px;
      margin-top: 4px;
    }
    .legend-item {
      display: flex;
      align-items: center;
      gap: 5px;
    }

    /* Footer */
    .academic-footer {
      border-top: 1px solid #e2e8f0;
      padding-top: 8px;
      margin-top: 8px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 9.5px;
      color: #94a3b8;
    }

    /* Print Stylesheet */
    @media print {
      body {
        background: #ffffff !important;
      }
      .no-print {
        display: none !important;
      }
      .report-container {
        padding: 0 !important;
        gap: 0 !important;
      }
      .report-page {
        border: none !important;
        box-shadow: none !important;
        width: 100% !important;
        min-height: 270mm !important;
        max-height: 270mm !important;
        padding: 0 !important;
        margin: 0 !important;
      }
    }
  </style>
</head>
<body>

  <!-- Screen-only action toolbar -->
  <div class="preview-toolbar no-print">
    <div class="preview-toolbar-title">
      Skillaro Career Readiness Assessment &nbsp;•&nbsp; Official Assessment Report
    </div>
    <div class="preview-toolbar-actions">
      <button onclick="window.print()" class="btn btn-primary">
        Save as PDF / Print
      </button>
      <button onclick="window.close()" class="btn btn-secondary">
        Close
      </button>
    </div>
  </div>

  <div class="report-container">

    <!-- ==================== PAGE 1: CAREER READINESS SUMMARY ==================== -->
    <div class="report-page page-1">
      <div>
        <!-- Academic Header -->
        <div class="academic-header">
          <div>
            <div class="brand-title">SKILLARO</div>
            <div class="brand-sub">Academic-to-Industry Skill Bridge &nbsp;|&nbsp; Career Assessment</div>
          </div>
          <div class="header-ref">
            <div>REF: ${shortId}</div>
            <div>PAGE 1 OF 2</div>
          </div>
        </div>

        <!-- Document Title -->
        <div class="report-title-block">
          <h1 class="report-title">Career Readiness Assessment Report</h1>
          <p class="report-subtitle">Evaluation of candidate capability alignment against active industry requirements.</p>
        </div>

        <!-- Metadata Grid -->
        <div class="meta-grid">
          <div class="meta-item">
            <span class="meta-label">Target Role</span>
            <span class="meta-value">${data.roleName}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">Career Level</span>
            <span class="meta-value">${data.careerLevel || "Entry Level"}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">Candidate</span>
            <span class="meta-value">${data.studentName || "Candidate Evaluation"}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">Assessment Date</span>
            <span class="meta-value">${dateFormatted}</span>
          </div>
        </div>

        <!-- Overall Score Card -->
        <div class="score-card">
          <div class="score-number-box">
            <div class="score-num">${roundedScore}%</div>
            <div class="score-caption">Readiness Score</div>
          </div>
          <div class="score-details-box">
            <span class="tier-badge">${data.tier}</span>
            <div class="progress-bar-track">
              <div class="progress-bar-fill"></div>
            </div>
            <p class="score-interpretation">
              ${data.interpretation || "The overall readiness score reflects evidence-adjusted coverage of the target role's weighted requirements."}
            </p>
          </div>
        </div>

        <!-- Requirement Coverage Summary -->
        <div class="section-heading">Requirement Coverage Summary</div>
        <div class="metrics-row">
          <div class="metric-card">
            <div class="metric-number">${data.totalRequirements}</div>
            <div class="metric-title">Total Assessed</div>
          </div>
          <div class="metric-card">
            <div class="metric-number" style="color: #15803d;">${data.satisfiedCount}</div>
            <div class="metric-title">Requirements Met</div>
          </div>
          <div class="metric-card">
            <div class="metric-number" style="color: #b45309;">${data.partialCount}</div>
            <div class="metric-title">Partially Covered</div>
          </div>
          <div class="metric-card">
            <div class="metric-number" style="color: #b91c1c;">${data.missingCount}</div>
            <div class="metric-title">Skill Gaps</div>
          </div>
        </div>

        <!-- Executive Summary -->
        <div class="section-heading">Executive Summary</div>
        <div class="narrative-card">
          <p class="narrative-text">
            ${data.summaryText || "Evaluation performed against verified industry role expectations and demonstrated candidate proficiencies."}
          </p>
        </div>

        <!-- Primary Growth Focus Callout -->
        ${topPriority ? `
        <div class="priority-callout">
          <div>
            <div class="priority-callout-title">Primary Learning Focus: ${escapeHtml(topPriority.skillName)}</div>
            <div class="priority-callout-sub">
              ${topPriority.gap !== undefined && topPriority.gap !== null ? `Remaining Capability Gap: ${formatGapValue(topPriority.gap)}` : ""}
              ${topPriority.priorityScore !== undefined && topPriority.priorityScore !== null ? ` &nbsp;•&nbsp; Learning Priority Index: ${formatPriorityScore(topPriority.priorityScore)}` : ""}
            </div>
          </div>
          <span class="tier-badge" style="background: #ffffff; border-color: #cbd5e1;">Top Priority</span>
        </div>
        ` : ""}

        <!-- Advisory Disclaimer -->
        <div class="academic-disclaimer">
          <strong>Advisory Note:</strong> This assessment evaluates deterministic alignment between candidate skill evidence and industry requirements. It serves as an academic and professional development guide to inform targeted learning, rather than a prediction or guarantee of hiring.
        </div>
      </div>

      <!-- Page 1 Footer -->
      <div class="academic-footer">
        <div>Skillaro Academic-to-Industry Skill Bridge &nbsp;•&nbsp; Assessment ID: ${shortId}</div>
        <div>Page 1 of 2</div>
      </div>
    </div>


    <!-- ==================== PAGE 2: SKILLS & IMPROVEMENT PRIORITIES ==================== -->
    <div class="report-page page-2">
      <div>
        <!-- Academic Header -->
        <div class="academic-header">
          <div>
            <div class="brand-title">SKILLARO</div>
            <div class="brand-sub">Academic-to-Industry Skill Bridge &nbsp;|&nbsp; Career Assessment</div>
          </div>
          <div class="header-ref">
            <div>REF: ${shortId}</div>
            <div>PAGE 2 OF 2</div>
          </div>
        </div>

        <!-- Section 1: Evaluated Skills Table -->
        <div class="report-title-block">
          <h2 class="report-title" style="font-size: 16px;">Evaluated Skills & Requirement Coverage</h2>
          <p class="report-subtitle">Itemized analysis of specific competencies evaluated against the target profile.</p>
        </div>

        <div class="table-wrapper">
          <table>
            <thead>
              <tr>
                <th style="width: 32%;">Skill Requirement</th>
                <th style="width: 16%;">Required Level</th>
                <th style="width: 14%;">Status</th>
                <th style="width: 38%;">Assessment Findings / Rationale</th>
              </tr>
            </thead>
            <tbody>
              ${data.skills.slice(0, 8).map((skill) => {
    const badgeClass =
      skill.status === "Met" ? "badge-met" : skill.status === "Partial" ? "badge-partial" : "badge-missing";
    return `
                <tr>
                  <td>
                    <strong>${skill.name}</strong>
                    ${skill.matchedName && skill.matchedName !== skill.name ? `<div style="font-size: 9px; color: #64748b;">via ${skill.matchedName}</div>` : ""}
                  </td>
                  <td style="font-weight: 600; color: #475569;">${skill.requiredProficiency}</td>
                  <td>
                    <span class="badge ${badgeClass}">${skill.status}</span>
                  </td>
                  <td style="font-size: 10px; color: #334155;">
                    ${skill.explanation || (skill.status === "Met" ? "Demonstrated proficiency satisfies the required level." : skill.status === "Partial" ? "Partial capability demonstrated against required depth." : "Requirement not yet evidenced in profile.")}
                  </td>
                </tr>
                `;
  }).join("")}
            </tbody>
          </table>
        </div>

        <!-- Section 2: Prioritized Improvement Areas -->
        <div class="section-heading">Prioritized Improvement Areas</div>
        ${data.priorities && data.priorities.length > 0 ? `
        <div class="table-wrapper" style="margin-bottom: 12px;">
          <table class="priorities-table">
            <thead>
              <tr>
                <th style="width: 12%; text-align: center;">Rank</th>
                <th style="width: 46%;">Priority Skill Area</th>
                <th style="width: 21%; text-align: center;">Capability Gap</th>
                <th style="width: 21%; text-align: right;">Priority Index</th>
              </tr>
            </thead>
            <tbody>
              ${data.priorities.map((p) => `
                <tr>
                  <td style="text-align: center; vertical-align: middle;">
                    <span class="priority-rank-badge">#${p.rank}</span>
                  </td>
                  <td>
                    <strong>${escapeHtml(p.name)}</strong>
                    ${p.explanation ? `<div style="font-size: 9.5px; color: #64748b; margin-top: 1px; line-height: 1.3;">${escapeHtml(p.explanation)}</div>` : ""}
                  </td>
                  <td style="text-align: center; vertical-align: middle; font-weight: 600; color: #b45309;">
                    ${formatGapValue(p.gap)}
                  </td>
                  <td style="text-align: right; vertical-align: middle; font-weight: 700; color: #4338ca;">
                    ${formatPriorityScore(p.priorityScore)}
                  </td>
                </tr>
              `).join("")}
            </tbody>
          </table>
        </div>
        ` : `
        <div class="empty-priorities-box">
          No prioritized improvement areas were identified for this assessment. All assessed requirements meet the target threshold or no specific skill gaps were returned.
        </div>
        `}

        <!-- Section 3: Next Steps Guidance -->
        <div class="section-heading">Developmental Next Steps</div>
        <div class="narrative-card" style="margin-bottom: 10px;">
          <p class="narrative-text" style="font-size: 11px;">
            Requirements designated as <strong>Met</strong> satisfy industry expectations. Learners should focus independent study, project coursework, or laboratory practice on top-ranked priority skills to address remaining gaps and maximize readiness.
          </p>
        </div>

        <!-- Status Legend -->
        <div class="legend-row">
          <span style="font-weight: 700; color: #475569;">Legend:</span>
          <div class="legend-item">
            <span class="badge badge-met">Met</span>
            <span>Requirement satisfied</span>
          </div>
          <div class="legend-item">
            <span class="badge badge-partial">Partial</span>
            <span>Partial capability</span>
          </div>
          <div class="legend-item">
            <span class="badge badge-missing">Missing</span>
            <span>Not yet evidenced</span>
          </div>
        </div>
      </div>

      <!-- Page 2 Footer -->
      <div class="academic-footer">
        <div>Skillaro Academic-to-Industry Skill Bridge &nbsp;•&nbsp; Assessment ID: ${shortId}</div>
        <div>Page 2 of 2</div>
      </div>
    </div>

  </div>

  <script>
    window.addEventListener('load', function() {
      setTimeout(function() {
        if (!window.location.search.includes('noprint')) {
          window.print();
        }
      }, 400);
    });
  </script>
</body>
</html>`;
}

// Fetches live analysis report details and triggers the print-friendly 2-page report download
export async function downloadCareerReadinessReport(
  analysisId: string,
  roleNameHint?: string,
  studentName?: string,
): Promise<void> {
  // Concurrently fetch analysis detail and explanation report
  const [detailResult, reportResult] = await Promise.allSettled([
    readinessApi.getAnalysisById(analysisId),
    readinessApi.getAnalysisReport(analysisId),
  ]);

  const detail: AnalysisDetailResponse | null =
    detailResult.status === "fulfilled" ? detailResult.value : null;
  const report: AnalysisReportResponse | null =
    reportResult.status === "fulfilled" ? reportResult.value : null;

  if (!detail && !report) {
    throw new Error("Unable to retrieve report details from the readiness engine.");
  }

  const roleName =
    report?.roleName || detail?.role_name || roleNameHint || "Target Role";
  const careerLevel = formatCareerLevel(detail?.career_level);
  const rawScore = report?.readinessSummary?.readinessScore ?? detail?.readiness_score ?? 0;
  const readinessScore = Number(rawScore) || 0;
  const tier = report?.readinessSummary?.tier || (readinessScore >= 80 ? "Good Readiness" : "Moderate Readiness");

  const satisfiedCount =
    report?.readinessSummary?.satisfiedCount ??
    detail?.skill_results?.filter(
      (s: SkillResultDetailItem) => s.result_status === "SATISFIED" || s.result_status === "COVERED",
    ).length ??
    0;

  const partialCount =
    report?.readinessSummary?.partialCount ??
    detail?.skill_results?.filter(
      (s: SkillResultDetailItem) => s.result_status === "PARTIAL" || s.result_status === "PARTIALLY_COVERED",
    ).length ??
    0;

  const missingCount =
    (report?.readinessSummary?.missingCount ?? 0) + (report?.readinessSummary?.deficientCount ?? 0) ||
    detail?.skill_results?.filter(
      (s: SkillResultDetailItem) => s.result_status === "MISSING" || s.result_status === "DEFICIENT",
    ).length ||
    0;

  const totalRequirements =
    report?.readinessSummary?.totalRequirements ??
    detail?.skill_results?.length ??
    satisfiedCount + partialCount + missingCount;

  // Map skill items from report explanations or analysis detail
  const skills: ReportGenerationData["skills"] = [];
  if (report?.skillExplanations && report.skillExplanations.length > 0) {
    for (const s of report.skillExplanations) {
      skills.push({
        name: s.skillName,
        matchedName: s.matchedSkillName || undefined,
        requiredProficiency: s.requiredProficiency || "INTERMEDIATE",
        status: normalizeReportStatus(s.resultStatus, s.matchType),
        explanation: s.explanation || s.contributionExplanation,
      });
    }
  } else if (detail?.skill_results) {
    for (const sr of detail.skill_results) {
      skills.push({
        name: sr.required_skill_name,
        matchedName: sr.matched_skill_name || undefined,
        requiredProficiency: sr.required_proficiency || "INTERMEDIATE",
        status: normalizeReportStatus(sr.result_status, sr.match_type),
        explanation: `Demonstrated coverage credit ${(sr.coverage_credit * 100).toFixed(0)}%.`,
      });
    }
  }

  // Collect all returned priority skills from explanation report or analysis details
  const priorities: ReportGenerationData["priorities"] = [];
  const rawPriorities: Array<{
    skillId?: string;
    skillName?: string;
    name?: string;
    priorityRank?: number;
    rank?: number;
    learningPriority?: number;
    priorityScore?: number;
    gap?: number;
    explanation?: string;
  }> =
    (report?.priorityExplanations && report.priorityExplanations.length > 0)
      ? report.priorityExplanations
      : (detail?.priority_skills && detail.priority_skills.length > 0)
        ? detail.priority_skills
        : Array.isArray((detail as unknown as { prioritySkills?: unknown[] })?.prioritySkills) &&
          (detail as unknown as { prioritySkills: unknown[] }).prioritySkills.length > 0
          ? ((detail as unknown as { prioritySkills: unknown[] }).prioritySkills as typeof rawPriorities)
          : Array.isArray((detail?.c04_payload as { prioritySkills?: unknown[] })?.prioritySkills) &&
            (detail?.c04_payload as { prioritySkills: unknown[] }).prioritySkills.length > 0
            ? ((detail?.c04_payload as { prioritySkills: unknown[] }).prioritySkills as typeof rawPriorities)
            : [];

  for (const item of rawPriorities) {
    const name = item.skillName || item.name;
    if (!name) continue;

    const rankVal = item.priorityRank ?? item.rank;
    const rank = rankVal !== undefined && rankVal !== null && !isNaN(Number(rankVal)) ? Number(rankVal) : priorities.length + 1;
    const gapVal = item.gap !== undefined && item.gap !== null && !isNaN(Number(item.gap)) ? Number(item.gap) : undefined;
    const scoreVal =
      item.learningPriority !== undefined && item.learningPriority !== null && !isNaN(Number(item.learningPriority))
        ? Number(item.learningPriority)
        : item.priorityScore !== undefined && item.priorityScore !== null && !isNaN(Number(item.priorityScore))
          ? Number(item.priorityScore)
          : undefined;

    // Use explanation directly if present or locate matching skill explanation
    const explanation =
      item.explanation ||
      report?.priorityExplanations?.find(
        (pe) => (item.skillId && pe.skillId === item.skillId) || pe.skillName.toLowerCase() === name.toLowerCase(),
      )?.explanation ||
      undefined;

    priorities.push({
      rank,
      name,
      gap: gapVal,
      priorityScore: scoreVal,
      explanation,
    });
  }

  // Sort into descending priority order (Rank 1 / highest priority first, then Rank 2, etc.)
  priorities.sort((a, b) => {
    if (a.rank !== undefined && b.rank !== undefined && a.rank !== b.rank) {
      return a.rank - b.rank;
    }
    if (a.priorityScore !== undefined && b.priorityScore !== undefined && a.priorityScore !== b.priorityScore) {
      return b.priorityScore - a.priorityScore;
    }
    return 0;
  });

  // Normalize rank sequence to guarantee clean 1-based ranks
  priorities.forEach((p, idx) => {
    if (!p.rank || p.rank <= 0) {
      p.rank = idx + 1;
    }
  });

  const generatedDate = formatAnalysisDate(report?.generatedAt || detail?.completed_at || detail?.started_at);

  const reportData: ReportGenerationData = {
    analysisId,
    roleName,
    careerLevel,
    domainName: "Information Technology",
    studentName,
    generatedDate,
    readinessScore,
    tier,
    interpretation: report?.readinessSummary?.interpretation,
    summaryText:
      report?.readinessSummary?.summaryText ||
      `Evaluated ${totalRequirements} requirement(s) for role '${roleName}'. ${satisfiedCount} fully satisfied, ${partialCount} partial, and ${missingCount} missing.`,
    totalRequirements,
    satisfiedCount,
    partialCount,
    missingCount,
    skills,
    priorities,
    highestPrioritySkill: priorities.length > 0 ? {
      skillName: priorities[0].name,
      gap: priorities[0].gap,
      priorityScore: priorities[0].priorityScore,
      explanation: priorities[0].explanation,
    } : undefined,
  };

  const html = generateCareerReadinessReportHtml(reportData);

  // Open printable document in a new tab/window
  const blob = new Blob([html], { type: "text/html;charset=utf-8" });
  const blobUrl = URL.createObjectURL(blob);

  const printWindow = window.open(blobUrl, "_blank");
  if (!printWindow) {
    // If pop-up was blocked by browser, trigger direct file download
    const sanitizedRole = roleName.replace(/[^\w\s-]/g, "").trim().replace(/\s+/g, "_");
    const link = document.createElement("a");
    link.href = blobUrl;
    link.download = `Skillaro_Career_Readiness_Report_${sanitizedRole}_${analysisId.slice(0, 8)}.html`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
}
