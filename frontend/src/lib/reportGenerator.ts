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
    requiredProficiency?: string;
    userProficiency?: string;
  }[];
}

// Maps backend result statuses and satisfaction to Met, Partial, or Missing.
function normalizeReportStatus(
  status?: string,
  matchType?: string,
  satisfaction?: number | null,
): "Met" | "Partial" | "Missing" {
  if (satisfaction !== undefined && satisfaction !== null) {
    if (satisfaction >= 0.999) return "Met";
    if (satisfaction > 0.0) return "Partial";
    return "Missing";
  }
  const norm = (status || "").toUpperCase();
  if (norm === "SATISFIED" || norm === "COVERED" || norm === "MET" || matchType === "EXACT") {
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

// Escapes special HTML characters to prevent layout breakage or script injection.
function escapeHtml(str?: string | null): string {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// Derives a short, student-friendly learning suggestion without numeric scores.
function getPracticalAdvice(priority: {
  name: string;
  explanation?: string;
  requiredProficiency?: string;
  userProficiency?: string;
}): string {
  const req = priority.requiredProficiency?.trim();
  const user = priority.userProficiency?.trim();

  if (req && req.toUpperCase() !== "NONE") {
    const formattedReq = req.charAt(0).toUpperCase() + req.slice(1).toLowerCase();
    if (user && user.toUpperCase() !== "NONE") {
      const formattedUser = user.charAt(0).toUpperCase() + user.slice(1).toLowerCase();
      return `Advance competency from demonstrated ${formattedUser} knowledge to the target ${formattedReq} level through hands-on project work.`;
    }
    return `Develop practical competency and coursework evidence to satisfy the target ${formattedReq} requirement for this role.`;
  }

  if (priority.explanation) {
    const match = priority.explanation.match(/Required:\s*([A-Za-z]+)(?:,\s*Demonstrated:\s*([A-Za-z]+))?/i);
    if (match) {
      const parsedReq = match[1].charAt(0).toUpperCase() + match[1].slice(1).toLowerCase();
      const parsedUser = match[2] ? match[2].charAt(0).toUpperCase() + match[2].slice(1).toLowerCase() : "";
      if (parsedUser && parsedUser.toLowerCase() !== "none") {
        return `Advance competency from demonstrated ${parsedUser} knowledge to the target ${parsedReq} level through hands-on project work.`;
      }
      return `Develop practical competency and coursework evidence to satisfy the target ${parsedReq} requirement for this role.`;
    }

    const clean = priority.explanation
      .replace(/Ranked\s*#\d+\s*learning\s*priority\s*(with\s*score\s*[\d.]+)?\.?/gi, "")
      .replace(/Driven\s*by\s*a\s*capability\s*gap\s*of\s*[\d.]+/gi, "")
      .replace(/and\s*an\s*industry\s*demand\s*weight\s*of\s*[\d.]+/gi, "")
      .replace(/\s*\([^)]*\)\s*/g, " ")
      .trim();

    if (clean.length > 10 && clean.length < 150) {
      return clean.charAt(0).toUpperCase() + clean.slice(1);
    }
  }

  return `Focus independent learning, course projects, and practical exercises on ${priority.name} to close this skill gap.`;
}

// Generates self-contained HTML for a concise, one-page A4 Career Readiness Report.
export function generateCareerReadinessReportHtml(data: ReportGenerationData): string {
  const roundedScore = Math.round(data.readinessScore);
  const scorePercent = Math.min(100, Math.max(0, roundedScore));
  const sanitizedRole = data.roleName.replace(/[^\w\s-]/g, "").trim();
  const dateFormatted = data.generatedDate;
  const shortId = data.analysisId.slice(0, 8).toUpperCase();

  const matchedSkills = data.skills.filter((s) => s.status === "Met" || s.status === "Partial");
  const missingSkills = data.skills.filter((s) => s.status === "Missing");
  const prioritiesToDisplay = data.priorities || [];

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Career Readiness Assessment — ${sanitizedRole}</title>
  <style>
    @page {
      size: A4 portrait;
      margin: 8mm 10mm;
    }
    *, *::before, *::after {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }
    html, body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      color: #0f172a;
      background: #f8fafc;
      line-height: 1.35;
      font-size: 11px;
      -webkit-font-smoothing: antialiased;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }

    /* Action bar for browser preview */
    .preview-toolbar {
      position: sticky;
      top: 0;
      z-index: 100;
      background: #0f172a;
      color: #f8fafc;
      padding: 9px 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    .preview-toolbar-title {
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.02em;
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
      padding: 5px 12px;
      border-radius: 5px;
      font-size: 11px;
      font-weight: 700;
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

    .report-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 14px 0 20px;
    }

    /* Single-page A4 dimensions without artificial clipping */
    .report-page {
      width: 210mm;
      min-height: 268mm;
      background: #ffffff;
      padding: 9mm 11mm;
      border: 1px solid #cbd5e1;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      box-sizing: border-box;
      page-break-after: avoid;
      break-after: avoid;
      page-break-inside: avoid;
      break-inside: avoid;
    }

    /* Report header and branding */
    .report-header {
      border-bottom: 1.5px solid #e2e8f0;
      padding-bottom: 6px;
      margin-bottom: 7px;
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
    }
    .header-brand .brand-name {
      font-size: 13.5px;
      font-weight: 900;
      letter-spacing: 0.05em;
      color: #4f46e5;
      text-transform: uppercase;
    }
    .header-brand .brand-tagline {
      font-size: 9px;
      color: #64748b;
      font-weight: 500;
      margin-top: 1px;
    }
    .header-doc {
      text-align: right;
    }
    .header-doc .doc-title {
      font-size: 13.5px;
      font-weight: 800;
      color: #0f172a;
      letter-spacing: -0.01em;
    }
    .header-doc .doc-ref {
      font-size: 9px;
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      font-weight: 600;
      color: #64748b;
      margin-top: 1px;
    }

    /* Metadata strip */
    .meta-strip {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 8px;
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 6px;
      padding: 5px 10px;
      margin-bottom: 7px;
    }
    .meta-col {
      display: flex;
      flex-direction: column;
      min-width: 0;
    }
    .meta-caption {
      font-size: 8px;
      font-weight: 700;
      color: #64748b;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .meta-data {
      font-size: 10.5px;
      font-weight: 700;
      color: #0f172a;
      margin-top: 1px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    /* Readiness score & 3 summary boxes */
    .overview-grid {
      display: grid;
      grid-template-columns: 190px 1fr;
      gap: 8px;
      margin-bottom: 7px;
      align-items: stretch;
    }

    /* Prominent score card */
    .score-card {
      border: 1.5px solid #e2e8f0;
      border-radius: 7px;
      background: #ffffff;
      padding: 8px 10px;
      display: flex;
      flex-direction: column;
      justify-content: center;
      gap: 4px;
    }
    .score-headline {
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: 6px;
    }
    .score-number {
      font-size: 28px;
      font-weight: 900;
      color: #4f46e5;
      line-height: 1;
      letter-spacing: -0.03em;
    }
    .tier-badge {
      display: inline-block;
      padding: 2px 6px;
      border-radius: 4px;
      font-size: 9px;
      font-weight: 800;
      background: #eef2ff;
      color: #4338ca;
      border: 1px solid #c7d2fe;
      white-space: nowrap;
    }
    .score-track {
      width: 100%;
      height: 5px;
      background: #e2e8f0;
      border-radius: 3px;
      overflow: hidden;
    }
    .score-fill {
      height: 100%;
      background: #4f46e5;
      border-radius: 3px;
    }
    .score-label {
      font-size: 8.5px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: #64748b;
    }

    /* 3 colored summary boxes */
    .summary-boxes-row {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 7px;
    }
    .summary-box {
      border-radius: 7px;
      padding: 7px 9px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      gap: 2px;
    }
    .box-matched {
      background: #f0fdf4;
      border: 1.5px solid #86efac;
    }
    .box-gaps {
      background: #fefce8;
      border: 1.5px solid #fde047;
    }
    .box-assessed {
      background: #faf5ff;
      border: 1.5px solid #e9d5ff;
    }
    .box-top-row {
      display: flex;
      align-items: center;
      gap: 5px;
    }
    .box-icon {
      width: 15px;
      height: 15px;
      border-radius: 4px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }
    .box-matched .box-icon { background: #dcfce7; color: #166534; }
    .box-gaps .box-icon { background: #fef9c3; color: #854d0e; }
    .box-assessed .box-icon { background: #f3e8ff; color: #6b21a8; }
    .box-title {
      font-size: 8px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      white-space: nowrap;
    }
    .box-matched .box-title { color: #15803d; }
    .box-gaps .box-title { color: #a16207; }
    .box-assessed .box-title { color: #7e22ce; }
    .box-val {
      font-size: 14px;
      font-weight: 900;
      line-height: 1.1;
      margin-top: 1px;
    }
    .box-matched .box-val { color: #166534; }
    .box-gaps .box-val { color: #854d0e; }
    .box-assessed .box-val { color: #6b21a8; }
    .box-desc {
      font-size: 8px;
      font-weight: 600;
      color: #64748b;
      margin-top: 1px;
    }

    /* Skills lists grid: matched vs missing */
    .skills-section {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      margin-bottom: 7px;
    }
    .skills-card {
      border: 1.5px solid #e2e8f0;
      border-radius: 7px;
      background: #ffffff;
      padding: 7px 10px;
      display: flex;
      flex-direction: column;
    }
    .skills-card-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding-bottom: 5px;
      margin-bottom: 5px;
      border-bottom: 1px solid #f1f5f9;
    }
    .skills-card-title {
      font-size: 9.5px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: #0f172a;
      display: flex;
      align-items: center;
      gap: 5px;
    }
    .dot-indicator {
      width: 5px;
      height: 5px;
      border-radius: 50%;
      flex-shrink: 0;
    }
    .dot-green { background: #16a34a; }
    .dot-yellow { background: #ca8a04; }
    .skills-count-badge {
      font-size: 8.5px;
      font-weight: 800;
      padding: 1px 5px;
      border-radius: 9999px;
    }
    .badge-count-green { background: #dcfce7; color: #15803d; }
    .badge-count-yellow { background: #fef9c3; color: #854d0e; }

    .skills-list {
      display: flex;
      flex-direction: column;
      gap: 3px;
    }
    .skills-list.multi-col {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 2px 8px;
    }
    .skill-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 5px;
      font-size: 9.5px;
      padding: 1px 0;
      border-bottom: 1px dashed #f1f5f9;
    }
    .skill-row:last-child {
      border-bottom: none;
    }
    .skill-name-text {
      font-weight: 600;
      color: #1e293b;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .status-badge {
      font-size: 7.5px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.03em;
      padding: 1px 4px;
      border-radius: 3px;
      flex-shrink: 0;
    }
    .badge-met {
      background: #f0fdf4;
      color: #15803d;
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
    .empty-note {
      font-size: 9px;
      color: #64748b;
      font-style: italic;
      padding: 4px 0;
    }

    /* Recommended improvement areas */
    .recommendations-section {
      margin-bottom: 7px;
    }
    .section-title-bar {
      font-size: 9.5px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: #475569;
      border-bottom: 1px solid #e2e8f0;
      padding-bottom: 3px;
      margin-bottom: 5px;
      display: flex;
      justify-content: space-between;
      align-items: baseline;
    }
    .section-title-sub {
      font-size: 8px;
      color: #94a3b8;
      font-weight: 500;
      text-transform: none;
    }
    .priorities-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 5px 8px;
    }
    .priorities-row.single-col {
      grid-template-columns: 1fr;
    }
    .priority-item-card {
      border: 1.5px solid #e2e8f0;
      border-radius: 6px;
      background: #ffffff;
      padding: 5px 8px;
      display: flex;
      flex-direction: column;
      gap: 2px;
    }
    .priority-header-line {
      display: flex;
      align-items: center;
      gap: 5px;
    }
    .priority-num-badge {
      font-size: 9px;
      font-weight: 800;
      width: 17px;
      height: 17px;
      background: #ede9fe;
      color: #5b21b6;
      border: 1px solid #ddd6fe;
      border-radius: 4px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }
    .priority-skill-heading {
      font-size: 10.5px;
      font-weight: 800;
      color: #0f172a;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .priority-advice-body {
      font-size: 9px;
      color: #475569;
      line-height: 1.3;
      margin: 0;
    }
    .empty-priorities-card {
      background: #f8fafc;
      border: 1px dashed #cbd5e1;
      border-radius: 6px;
      padding: 7px 10px;
      font-size: 9px;
      color: #64748b;
      line-height: 1.35;
    }

    /* Disclaimer & footer */
    .bottom-wrapper {
      margin-top: auto;
    }
    .disclaimer-box {
      font-size: 8px;
      color: #64748b;
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 5px;
      padding: 5px 8px;
      line-height: 1.3;
      margin-bottom: 4px;
    }
    .page-footer {
      border-top: 1px solid #e2e8f0;
      padding-top: 4px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 8px;
      color: #94a3b8;
    }

    /* Print stylesheet ensuring single page without page break */
    @media print {
      body {
        background: #ffffff !important;
        padding: 0 !important;
        margin: 0 !important;
      }
      .no-print {
        display: none !important;
      }
      .report-container {
        padding: 0 !important;
        margin: 0 !important;
      }
      .report-page {
        border: none !important;
        box-shadow: none !important;
        width: 100% !important;
        max-width: 100% !important;
        min-height: auto !important;
        max-height: none !important;
        padding: 0 !important;
        margin: 0 !important;
        page-break-after: avoid;
        break-after: avoid;
        page-break-inside: avoid;
        break-inside: avoid;
      }
    }
  </style>
</head>
<body>

  <!-- Screen-only action toolbar -->
  <div class="preview-toolbar no-print">
    <div class="preview-toolbar-title">
      Skillaro Career Readiness Assessment &nbsp;•&nbsp; One-Page Assessment Report
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
    <div class="report-page">
      <div>
        <!-- Branding & Document Title -->
        <div class="report-header">
          <div class="header-brand">
            <div class="brand-name">SKILLARO</div>
            <div class="brand-tagline">Academic-to-Industry Skill Bridge</div>
          </div>
          <div class="header-doc">
            <h1 class="doc-title">Career Readiness Report</h1>
            <div class="doc-ref">REF: ${shortId}</div>
          </div>
        </div>

        <!-- Metadata Strip -->
        <div class="meta-strip">
          <div class="meta-col">
            <span class="meta-caption">Target Role</span>
            <span class="meta-data" title="${escapeHtml(data.roleName)}">${escapeHtml(data.roleName)}</span>
          </div>
          <div class="meta-col">
            <span class="meta-caption">Career Level</span>
            <span class="meta-data">${escapeHtml(data.careerLevel || "Entry Level")}</span>
          </div>
          <div class="meta-col">
            <span class="meta-caption">Candidate</span>
            <span class="meta-data">${escapeHtml(data.studentName || "Candidate Evaluation")}</span>
          </div>
          <div class="meta-col">
            <span class="meta-caption">Assessment Date</span>
            <span class="meta-data">${escapeHtml(dateFormatted)}</span>
          </div>
        </div>

        <!-- Readiness Score Card & 3 Summary Badges -->
        <div class="overview-grid">
          <!-- Readiness Score -->
          <div class="score-card">
            <div class="score-headline">
              <span class="score-number">${roundedScore}%</span>
              <span class="tier-badge">${escapeHtml(data.tier)}</span>
            </div>
            <div class="score-track">
              <div class="score-fill" style="width: ${scorePercent}%;"></div>
            </div>
            <span class="score-label">Readiness Score</span>
          </div>

          <!-- 3 Colored Summary Boxes -->
          <div class="summary-boxes-row">
            <!-- Matched Skills -->
            <div class="summary-box box-matched">
              <div class="box-top-row">
                <span class="box-icon">
                  <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>
                </span>
                <span class="box-title">Matched Skills</span>
              </div>
              <div class="box-val">${matchedSkills.length} Skills</div>
              <div class="box-desc">${data.satisfiedCount} Met${data.partialCount > 0 ? `, ${data.partialCount} Partial` : ""}</div>
            </div>

            <!-- Skill Gaps -->
            <div class="summary-box box-gaps">
              <div class="box-top-row">
                <span class="box-icon">
                  <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                </span>
                <span class="box-title">Skill Gaps</span>
              </div>
              <div class="box-val">${data.missingCount} Missing</div>
              <div class="box-desc">To develop</div>
            </div>

            <!-- Total Assessed -->
            <div class="summary-box box-assessed">
              <div class="box-top-row">
                <span class="box-icon">
                  <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
                </span>
                <span class="box-title">Total Assessed</span>
              </div>
              <div class="box-val">${data.totalRequirements} Total</div>
              <div class="box-desc">Role standards</div>
            </div>
          </div>
        </div>

        <!-- Matched Skills & Missing Skills -->
        <div class="skills-section">
          <!-- Column 1: Matched Skills -->
          <div class="skills-card">
            <div class="skills-card-header">
              <span class="skills-card-title">
                <span class="dot-indicator dot-green"></span>
                <span>Matched Skills</span>
              </span>
              <span class="skills-count-badge badge-count-green">${matchedSkills.length}</span>
            </div>
            <div class="skills-list ${matchedSkills.length > 4 ? 'multi-col' : ''}">
              ${matchedSkills.length === 0 ? `
                <div class="empty-note">No matched skills recorded.</div>
              ` : matchedSkills.map((s) => `
                <div class="skill-row">
                  <span class="skill-name-text" title="${escapeHtml(s.name)}">${escapeHtml(s.name)}</span>
                  ${s.status === "Partial" ? `<span class="status-badge badge-partial">Partial</span>` : `<span class="status-badge badge-met">Met</span>`}
                </div>
              `).join("")}
            </div>
          </div>

          <!-- Column 2: Missing Skills -->
          <div class="skills-card">
            <div class="skills-card-header">
              <span class="skills-card-title">
                <span class="dot-indicator dot-yellow"></span>
                <span>Skill Gaps</span>
              </span>
              <span class="skills-count-badge badge-count-yellow">${missingSkills.length}</span>
            </div>
            <div class="skills-list ${missingSkills.length > 4 ? 'multi-col' : ''}">
              ${missingSkills.length === 0 ? `
                <div class="empty-note" style="color: #15803d; font-style: normal; font-weight: 600;">No skill gaps identified.</div>
              ` : missingSkills.map((s) => `
                <div class="skill-row">
                  <span class="skill-name-text" title="${escapeHtml(s.name)}">${escapeHtml(s.name)}</span>
                  <span class="status-badge badge-missing">Missing</span>
                </div>
              `).join("")}
            </div>
          </div>
        </div>

        <!-- Recommended Improvement Areas -->
        <div class="recommendations-section">
          <div class="section-title-bar">
            <span>Recommended Improvement Areas</span>
            <span class="section-title-sub">Targeted priorities for career readiness</span>
          </div>

          ${prioritiesToDisplay.length === 0 ? `
            <div class="empty-priorities-card">
              No explicit improvement priorities were identified for this assessment. All assessed requirements meet the target threshold or no specific skill gaps were returned.
            </div>
          ` : `
            <div class="priorities-row ${prioritiesToDisplay.length === 1 ? 'single-col' : ''}">
              ${prioritiesToDisplay.map((p, idx) => {
                const advice = getPracticalAdvice(p);
                return `
                  <div class="priority-item-card">
                    <div class="priority-header-line">
                      <span class="priority-num-badge">${idx + 1}</span>
                      <span class="priority-skill-heading" title="${escapeHtml(p.name)}">${escapeHtml(p.name)}</span>
                    </div>
                    <p class="priority-advice-body">${escapeHtml(advice)}</p>
                  </div>
                `;
              }).join("")}
            </div>
          `}
        </div>
      </div>

      <!-- Assessment Disclaimer and Footer -->
      <div class="bottom-wrapper">
        <div class="disclaimer-box">
          <strong>Advisory Note:</strong> This assessment evaluates deterministic alignment between candidate skill evidence and verified industry role expectations to guide targeted learning, rather than a prediction or guarantee of hiring.
        </div>
        <div class="page-footer">
          <span>Skillaro Academic-to-Industry Skill Bridge &nbsp;•&nbsp; Assessment ID: ${shortId}</span>
          <span>Generated: ${escapeHtml(dateFormatted)}</span>
        </div>
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

// Fetches live analysis report details and triggers the print-friendly 1-page report download.
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
      (s: SkillResultDetailItem) =>
        s.satisfaction !== null && s.satisfaction !== undefined
          ? s.satisfaction >= 0.999
          : s.result_status === "SATISFIED",
    ).length ??
    0;

  const partialCount =
    report?.readinessSummary?.partialCount ??
    detail?.skill_results?.filter(
      (s: SkillResultDetailItem) =>
        s.satisfaction !== null && s.satisfaction !== undefined
          ? s.satisfaction > 0 && s.satisfaction < 0.999
          : s.result_status === "PARTIAL" || s.result_status === "PARTIALLY_COVERED",
    ).length ??
    0;

  const missingCount =
    (report?.readinessSummary?.missingCount ?? 0) + (report?.readinessSummary?.deficientCount ?? 0) ||
    detail?.skill_results?.filter(
      (s: SkillResultDetailItem) =>
        s.result_status === "MISSING" || s.result_status === "DEFICIENT" || s.match_type === "MISSING",
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
        status: normalizeReportStatus(s.resultStatus, s.matchType, s.satisfaction),
        explanation: s.explanation || s.contributionExplanation,
      });
    }
  } else if (detail?.skill_results) {
    for (const sr of detail.skill_results) {
      skills.push({
        name: sr.required_skill_name,
        matchedName: sr.matched_skill_name || undefined,
        requiredProficiency: sr.required_proficiency || "INTERMEDIATE",
        status: normalizeReportStatus(sr.result_status, sr.match_type, sr.satisfaction),
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
    requiredProficiency?: string;
    userProficiency?: string;
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

    const peMatch = report?.priorityExplanations?.find(
      (pe) => (item.skillId && pe.skillId === item.skillId) || pe.skillName.toLowerCase() === name.toLowerCase(),
    );

    const explanation = item.explanation || peMatch?.explanation || undefined;
    const requiredProficiency = item.requiredProficiency || peMatch?.requiredProficiency || undefined;
    const userProficiency = item.userProficiency || peMatch?.userProficiency || undefined;

    priorities.push({
      rank,
      name,
      gap: gapVal,
      priorityScore: scoreVal,
      explanation,
      requiredProficiency,
      userProficiency,
    });
  }

  // Sort priorities in ascending rank order (rank 1 first, rank 2 second, etc.)
  priorities.sort((a, b) => {
    if (a.rank !== undefined && b.rank !== undefined && a.rank !== b.rank) {
      return a.rank - b.rank;
    }
    if (a.priorityScore !== undefined && b.priorityScore !== undefined && a.priorityScore !== b.priorityScore) {
      return b.priorityScore - a.priorityScore;
    }
    return 0;
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
  };

  const html = generateCareerReadinessReportHtml(reportData);

  // Open printable document in a new tab/window for PDF save or print
  const blob = new Blob([html], { type: "text/html;charset=utf-8" });
  const blobUrl = URL.createObjectURL(blob);

  const printWindow = window.open(blobUrl, "_blank");
  if (!printWindow) {
    const sanitizedRole = roleName.replace(/[^\w\s-]/g, "").trim().replace(/\s+/g, "_");
    const link = document.createElement("a");
    link.href = blobUrl;
    link.download = `Skillaro_Career_Readiness_Report_${sanitizedRole}_${analysisId.slice(0, 8)}.html`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
}
