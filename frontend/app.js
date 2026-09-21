// MkatabaWatch Frontend Application Engine

let currentLang = localStorage.getItem("mkataba_lang") || "en";
let currentScreen = "dashboard";
let selectedProjectId = null;
let cachedProjects = [];
let pendingReviewAction = null;
let currentRawOcdsJson = "";

function t(key) {
  if (window.I18N && window.I18N[currentLang] && window.I18N[currentLang][key]) {
    return window.I18N[currentLang][key];
  }
  return key;
}

function setLanguage(lang) {
  currentLang = lang;
  localStorage.setItem("mkataba_lang", lang);
  document.getElementById("lang-en")?.classList.toggle("active", lang === "en");
  document.getElementById("lang-sw")?.classList.toggle("active", lang === "sw");
  updateStaticStrings();
  if (currentScreen === "dashboard") {
    renderProjectsTable(cachedProjects);
  } else if (currentScreen === "project-detail" && selectedProjectId) {
    loadProjectDetail(selectedProjectId);
  } else if (currentScreen === "verification-queue") {
    loadVerificationQueue();
  }
}

function updateStaticStrings() {
  document.querySelectorAll("[data-i18n]").forEach(el => {
    const key = el.getAttribute("data-i18n");
    el.textContent = t(key);
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach(el => {
    const key = el.getAttribute("data-i18n-placeholder");
    el.setAttribute("placeholder", t(key));
  });
}

// --- Navigation & History Management ---
function navigateTo(screenId, params = {}, pushState = true) {
  currentScreen = screenId;

  if (pushState) {
    let hash = `#${screenId}`;
    if (params.projectId) hash += `/${params.projectId}`;
    history.pushState({ screen: screenId, ...params }, "", hash);
  }

  document.querySelectorAll(".app-screen").forEach(el => el.style.display = "none");
  const target = document.getElementById(`screen-${screenId}`);
  if (target) target.style.display = "block";

  document.querySelectorAll(".nav-btn").forEach(btn => btn.classList.remove("active"));
  const activeNav = document.getElementById(`nav-${screenId}`);
  if (activeNav) activeNav.classList.add("active");

  window.scrollTo({ top: 0, behavior: "smooth" });
}

function navigateBack() {
  if (history.length > 1) {
    history.back();
  } else {
    navigateTo("dashboard");
  }
}

window.addEventListener("popstate", (event) => {
  if (event.state && event.state.screen) {
    if (event.state.screen === "project-detail" && event.state.projectId) {
      viewProject(event.state.projectId, false);
    } else if (event.state.screen === "reconciliation" && event.state.projectId) {
      reconcileProject(event.state.projectId, false);
    } else {
      navigateTo(event.state.screen, {}, false);
    }
  } else {
    navigateTo("dashboard", {}, false);
  }
});

// --- Formatters ---
function formatCurrency(amount, currency = "TZS") {
  if (!amount) return "TZS 0";
  return `${currency} ${Number(amount).toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
}

function formatDate(dateStr) {
  if (!dateStr) return "N/A";
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString(currentLang === "sw" ? "sw-TZ" : "en-GB", {
      year: 'numeric', month: 'short', day: 'numeric'
    });
  } catch (e) {
    return dateStr.substring(0, 10);
  }
}

// --- AI Status Check ---
async function fetchAiEngineStatus() {
  const badgeText = document.getElementById("ai-engine-text");
  try {
    const res = await fetch("/api/ai-status");
    const data = await res.json();
    if (badgeText) {
      badgeText.textContent = `${data.provider} (${data.model})`;
      badgeText.title = data.message;
    }
  } catch (e) {
    if (badgeText) badgeText.textContent = "AI Rules Engine (Offline Active)";
  }
}

// --- Stats & Projects List ---
async function fetchStats() {
  try {
    const res = await fetch("/api/stats");
    const data = await res.json();
    document.getElementById("stat-contracts-val").textContent = data.total_projects || 0;
    document.getElementById("stat-total-val").textContent = formatCurrency(data.total_value_tzs);
    document.getElementById("stat-discrepancies-val").textContent = data.discrepancies_flagged || 0;
    document.getElementById("stat-evidence-val").textContent = data.total_evidence_submissions || 0;
  } catch (err) {
    console.error("Error fetching stats:", err);
  }
}

async function loadProjects() {
  const search = document.getElementById("search-input")?.value || "";
  const region = document.getElementById("region-filter")?.value || "all";
  const sector = document.getElementById("sector-filter")?.value || "all";
  const status = document.getElementById("status-filter")?.value || "";

  let url = `/api/projects?`;
  if (search) url += `search=${encodeURIComponent(search)}&`;
  if (region !== "all") url += `region=${encodeURIComponent(region)}&`;
  if (sector !== "all") url += `sector=${encodeURIComponent(sector)}&`;
  if (status) url += `evidence_status=${encodeURIComponent(status)}&`;

  try {
    const res = await fetch(url);
    const projects = await res.json();
    cachedProjects = projects;
    renderProjectsTable(projects);
    populateProjectSelect(projects);
  } catch (err) {
    console.error("Error loading projects:", err);
  }
}

function renderProjectsTable(projects) {
  const tbody = document.getElementById("projects-tbody");
  if (!tbody) return;
  tbody.innerHTML = "";

  if (projects.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:32px; color:var(--text-muted);">${t("no_queue_items")}</td></tr>`;
    return;
  }

  projects.forEach(p => {
    const tr = document.createElement("tr");

    let statusBadge = `<span class="badge badge-no-evidence">${t("status_no_evidence")}</span>`;
    if (p.latest_reconciliation) {
      if (p.latest_reconciliation.status === "discrepancy_flagged") {
        statusBadge = `<span class="badge badge-discrepancy">${t("status_discrepancy")} (${p.latest_reconciliation.confidence})</span>`;
      } else if (p.latest_reconciliation.status === "consistent") {
        statusBadge = `<span class="badge badge-consistent">${t("status_consistent")}</span>`;
      } else {
        statusBadge = `<span class="badge badge-needs-evidence">${t("status_needs_evidence")}</span>`;
      }
    } else if (p.evidence_count > 0) {
      statusBadge = `<span class="badge badge-needs-evidence">${p.evidence_count} ${t("community_evidence")}</span>`;
    }

    tr.innerHTML = `
      <td class="project-name-cell">
        <a href="javascript:void(0)" onclick="viewProject('${p.id}')">${p.title}</a>
        <div class="project-ocid">${p.ocid}</div>
        <span class="badge badge-sector">${p.sector || 'Public Works'}</span>
      </td>
      <td><strong>${p.buyer}</strong></td>
      <td>${p.contractor}</td>
      <td class="value-cell">${formatCurrency(p.contract_value, p.currency)}</td>
      <td>${p.region}</td>
      <td>${statusBadge}</td>
      <td>
        <div style="display:flex; gap:6px; flex-wrap:wrap;">
          <button class="btn btn-secondary btn-sm" onclick="viewProject('${p.id}')">${t("view_details")}</button>
          <button class="btn btn-primary btn-sm" onclick="reconcileProject('${p.id}')">${t("reconcile_btn")}</button>
        </div>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function populateProjectSelect(projects) {
  const select = document.getElementById("evidence-project-select");
  if (!select) return;
  select.innerHTML = `<option value="">-- ${t("select_project_label")} --</option>`;
  projects.forEach(p => {
    const opt = document.createElement("option");
    opt.value = p.id;
    opt.textContent = `[${p.region}] ${p.title} (${p.buyer})`;
    select.appendChild(opt);
  });
}

// --- Screen 2: Project Profile ---
async function viewProject(projectId, pushState = true) {
  selectedProjectId = projectId;
  navigateTo("project-detail", { projectId }, pushState);
  await loadProjectDetail(projectId);
}

async function loadProjectDetail(projectId) {
  try {
    const res = await fetch(`/api/projects/${projectId}`);
    if (!res.ok) return;
    const p = await res.json();

    document.getElementById("detail-title").textContent = p.title;
    document.getElementById("detail-ocid").textContent = `OCID: ${p.ocid}`;
    
    // Set direct API endpoint for official feed (loads instantaneously)
    const nestLink = document.getElementById("detail-nest-link");
    if (nestLink) {
      nestLink.href = `https://nest.go.tz/gateway/nest-data-portal-api/api/records/${p.ocid}`;
      nestLink.setAttribute("title", "Opens direct verified JSON record from Tanzania PPRA Gateway");
    }

    document.getElementById("detail-buyer").textContent = p.buyer;
    document.getElementById("detail-contractor").textContent = p.contractor;
    document.getElementById("detail-value").textContent = formatCurrency(p.contract_value, p.currency);
    document.getElementById("detail-location").textContent = p.location_name || p.region;
    document.getElementById("detail-period").textContent = `${formatDate(p.start_date)} — ${formatDate(p.expected_completion_date)} (${p.duration_days || 'N/A'} days)`;
    document.getElementById("detail-status").textContent = p.official_status?.toUpperCase();
    document.getElementById("detail-progress").textContent = p.official_reported_progress ? `${p.official_reported_progress}%` : "Not reported in official NeST feed";
    document.getElementById("detail-last-updated").textContent = formatDate(p.last_updated);

    // Evidence List
    const evidenceList = document.getElementById("detail-evidence-list");
    evidenceList.innerHTML = "";

    if (!p.evidence_submissions || p.evidence_submissions.length === 0) {
      evidenceList.innerHTML = `
        <div style="padding:24px; text-align:center; background:#f8fafc; border-radius:var(--radius); border:1px dashed var(--border-dark);">
          <p style="color:var(--text-muted); margin-bottom:12px;">${t("no_evidence_msg")}</p>
          <button class="btn btn-primary btn-sm" onclick="openSubmitForProject('${p.id}')">${t("submit_first_evidence")}</button>
        </div>
      `;
    } else {
      p.evidence_submissions.forEach(ev => {
        const card = document.createElement("div");
        card.className = "evidence-card";
        const demoBadge = ev.is_seeded_demo_data ? `<span class="badge badge-demo">${t("badge_demo")}</span>` : `<span class="badge badge-community">${t("badge_community")}</span>`;
        const obsLabel = t(`obs_${ev.observation_type}`) || ev.observation_type.replace('_', ' ').toUpperCase();

        card.innerHTML = `
          <div class="evidence-header">
            <div>
              <strong>${ev.submitted_by}</strong> &nbsp;
              ${demoBadge}
            </div>
            <span class="badge badge-needs-evidence">${obsLabel}</span>
          </div>
          <div class="evidence-meta">
            <span>Date: ${formatDate(ev.timestamp)}</span>
            ${ev.gps_lat ? `<span>GPS: Lat ${ev.gps_lat.toFixed(4)}, Lng ${ev.gps_lng.toFixed(4)}</span>` : ""}
          </div>
          <p style="font-size:0.9rem; line-height:1.5;">${ev.description}</p>
          ${ev.photo_url ? `<img src="${ev.photo_url}" class="evidence-photo-thumb" alt="Field Photo" onerror="this.style.display='none'"/>` : ""}
        `;
        evidenceList.appendChild(card);
      });
    }

    // Latest Reconciliation display on Project Profile
    const reconBox = document.getElementById("detail-latest-reconciliation");
    const container = document.getElementById("detail-recon-output-container");
    if (p.reconciliation_results && p.reconciliation_results.length > 0 && container) {
      reconBox.style.display = "block";
      renderReconciliationHtml(container, p.reconciliation_results[0]);
    } else if (reconBox) {
      reconBox.style.display = "none";
    }

  } catch (err) {
    console.error("Error loading project detail:", err);
  }
}

// --- Official OCDS Record Inspector Modal ---
async function inspectCurrentOcds() {
  if (!selectedProjectId) return;
  const modal = document.getElementById("ocds-modal");
  const content = document.getElementById("ocds-modal-content");
  const title = document.getElementById("ocds-modal-title");

  modal.style.display = "flex";
  content.textContent = "Loading live OCDS record from Tanzania PPRA feed...";

  try {
    const res = await fetch(`/api/projects/${selectedProjectId}/raw-ocds`);
    const data = await res.json();
    currentRawOcdsJson = JSON.stringify(data, null, 2);
    title.textContent = `Official OCDS Record: ${data.ocid}`;
    content.textContent = currentRawOcdsJson;
  } catch (e) {
    content.textContent = "Failed to load OCDS record: " + e.message;
  }
}

function closeOcdsModal() {
  document.getElementById("ocds-modal").style.display = "none";
}

function copyOcdsJson() {
  if (currentRawOcdsJson) {
    navigator.clipboard.writeText(currentRawOcdsJson).then(() => {
      alert("OCDS JSON copied to clipboard.");
    });
  }
}

function openSubmitForProject(projectId) {
  navigateTo("submit-evidence", { projectId });
  const select = document.getElementById("evidence-project-select");
  if (select) select.value = projectId;
}

// --- Screen 3: Submit Community Evidence ---
function handlePhotoPreview(input) {
  const container = document.getElementById("photo-preview-container");
  const img = document.getElementById("photo-preview-element");
  if (input.files && input.files[0]) {
    const reader = new FileReader();
    reader.onload = function(e) {
      img.src = e.target.result;
      container.style.display = "block";
    };
    reader.readAsDataURL(input.files[0]);
  } else {
    container.style.display = "none";
  }
}

function captureCurrentLocation() {
  const gpsInput = document.getElementById("evidence-gps");
  if (!navigator.geolocation) {
    alert("Geolocation is not supported by your browser. Please enter coordinates manually.");
    return;
  }
  gpsInput.setAttribute("placeholder", "Detecting GPS satellites...");
  navigator.geolocation.getCurrentPosition(
    pos => {
      gpsInput.value = `${pos.coords.latitude.toFixed(5)}, ${pos.coords.longitude.toFixed(5)}`;
    },
    err => {
      console.warn("GPS capture error:", err);
      gpsInput.value = "-6.16300, 35.75160"; // Default Dodoma coordinates
    },
    { timeout: 8000, enableHighAccuracy: true }
  );
}

async function handleEvidenceSubmit(e) {
  e.preventDefault();
  const btn = document.getElementById("submit-evidence-btn");

  const projectId = document.getElementById("evidence-project-select").value;
  const observationType = document.querySelector('input[name="observation_type"]:checked')?.value;
  const description = document.getElementById("evidence-description").value.trim();
  const submittedBy = document.getElementById("evidence-submitter").value.trim();
  const gpsRaw = document.getElementById("evidence-gps").value.trim();
  const obsDate = document.getElementById("evidence-date").value;
  const photoFile = document.getElementById("evidence-photo").files[0];

  // Client-side strict validation for all fields
  if (!projectId) {
    alert("Please select a project to monitor.");
    return;
  }
  if (!observationType) {
    alert("Please select an observation type.");
    return;
  }
  if (!description || description.length < 15) {
    alert("Field description is required and must be at least 15 characters long.");
    return;
  }
  if (!photoFile) {
    alert("Photo evidence is required for audit integrity. Please attach a photo.");
    return;
  }
  if (!gpsRaw || !gpsRaw.includes(",")) {
    alert("Valid GPS coordinates (latitude, longitude) are required.");
    return;
  }
  if (!obsDate) {
    alert("Observation date is required.");
    return;
  }
  if (!submittedBy) {
    alert("Monitor name or community affiliation is required.");
    return;
  }

  const parts = gpsRaw.split(",");
  const lat = parseFloat(parts[0].trim());
  const lng = parseFloat(parts[1].trim());

  btn.disabled = true;
  btn.textContent = t("submitting");

  try {
    const formData = new FormData();
    formData.append("project_id", projectId);
    formData.append("observation_type", observationType);
    formData.append("description", description);
    formData.append("submitted_by", submittedBy);
    formData.append("gps_lat", lat);
    formData.append("gps_lng", lng);
    formData.append("timestamp", `${obsDate}T12:00:00Z`);
    formData.append("photo", photoFile);

    const res = await fetch("/api/evidence/upload", {
      method: "POST",
      body: formData
    });

    if (res.ok) {
      alert(`${t("submission_success_title")}\n\n${t("submission_success_desc")}`);
      document.getElementById("evidence-form").reset();
      document.getElementById("photo-preview-container").style.display = "none";
      fetchStats();
      viewProject(projectId);
    } else {
      const err = await res.json();
      alert("Submission error: " + (err.detail || "Unable to save report"));
    }
  } catch (err) {
    console.error("Submission failed:", err);
    alert("Network error submitting report. Please try again.");
  } finally {
    btn.disabled = false;
    btn.textContent = t("submit_evidence_btn");
  }
}

// --- Screen 4: AI Reconciliation View ---
async function reconcileProject(projectId, pushState = true) {
  selectedProjectId = projectId;
  navigateTo("reconciliation", { projectId }, pushState);

  const statusBanner = document.getElementById("recon-loading-state");
  const contentBox = document.getElementById("recon-content-box");
  statusBanner.style.display = "block";
  contentBox.style.display = "none";

  try {
    // 1. Fetch project profile & evidence
    const pRes = await fetch(`/api/projects/${projectId}`);
    const project = await pRes.json();

    document.getElementById("recon-official-title").textContent = project.title;
    document.getElementById("recon-official-buyer").textContent = project.buyer;
    document.getElementById("recon-official-contractor").textContent = project.contractor;
    document.getElementById("recon-official-value").textContent = formatCurrency(project.contract_value, project.currency);
    document.getElementById("recon-official-period").textContent = `${formatDate(project.start_date)} to ${formatDate(project.expected_completion_date)}`;
    document.getElementById("recon-official-status").textContent = project.official_status?.toUpperCase();

    // Render Observed Evidence Summary List
    const evidenceSummaryList = document.getElementById("recon-evidence-summary-list");
    evidenceSummaryList.innerHTML = "";
    if (project.evidence_submissions && project.evidence_submissions.length > 0) {
      project.evidence_submissions.forEach(ev => {
        const item = document.createElement("div");
        item.style.padding = "10px 0";
        item.style.borderBottom = "1px solid var(--border-color)";
        item.innerHTML = `
          <div style="display:flex; justify-content:space-between; font-size:0.82rem; font-weight:700;">
            <span>${ev.submitted_by}</span>
            <span class="badge badge-sector">${ev.observation_type.replace('_', ' ').toUpperCase()}</span>
          </div>
          <p style="font-size:0.86rem; margin-top:4px; color:var(--text-main);">${ev.description}</p>
        `;
        evidenceSummaryList.appendChild(item);
      });
    } else {
      evidenceSummaryList.innerHTML = `<p style="color:var(--text-muted); font-size:0.88rem; padding:12px 0;">${t("no_evidence_msg")}</p>`;
    }

    // 2. Trigger AI Reconciliation backend API
    const rRes = await fetch(`/api/reconcile/${projectId}`, { method: "POST" });
    const reconResult = await rRes.json();

    // Render into dedicated container
    const reconTarget = document.getElementById("recon-screen-ai-output");
    renderReconciliationHtml(reconTarget, reconResult);
    fetchStats();

  } catch (err) {
    console.error("Reconciliation failed:", err);
    alert("Failed to execute AI reconciliation. Please check console logs.");
  } finally {
    statusBanner.style.display = "none";
    contentBox.style.display = "block";
  }
}

function renderReconciliationHtml(container, recon) {
  if (!container) return;

  let badge = `<span class="badge badge-consistent" style="font-size:0.88rem; padding:6px 12px;">${t("status_consistent")}</span>`;
  if (recon.status === "discrepancy_flagged") {
    badge = `<span class="badge badge-discrepancy" style="font-size:0.88rem; padding:6px 12px;">${t("status_discrepancy")}</span>`;
  } else if (recon.status === "needs_more_evidence") {
    badge = `<span class="badge badge-needs-evidence" style="font-size:0.88rem; padding:6px 12px;">${t("status_needs_evidence")}</span>`;
  }

  const supportingList = (recon.supporting_points || []).map(p => `<li>${p}</li>`).join("");
  const concerningList = (recon.concerning_points || []).map(p => `<li>${p}</li>`).join("");

  container.innerHTML = `
    <div class="ai-header">
      <div>
        <h3 style="font-size:1.15rem; font-weight:800; color:var(--text-main);">${t("ai_reconciliation_title")}</h3>
        <p style="font-size:0.8rem; color:var(--text-muted); margin-top:2px;">
          Confidence: <strong>${recon.confidence.toUpperCase()}</strong> &bull; Provenance: <strong>${recon.provenance}</strong> &bull; ${formatDate(recon.created_at)}
        </p>
      </div>
      <div>${badge}</div>
    </div>

    <div style="font-size:0.92rem; line-height:1.6; margin-bottom:16px;">
      <h4 style="font-size:0.82rem; text-transform:uppercase; color:var(--text-muted); font-weight:700; margin-bottom:6px;">${t("ai_summary_heading")}</h4>
      <p style="background:#f8fafc; padding:14px; border-radius:var(--radius); border-left:4px solid var(--primary); font-weight:500;">${recon.summary}</p>
    </div>

    <div class="ai-points-grid">
      <div class="point-card supporting">
        <h5>${t("supporting_points_heading")}</h5>
        <ul>${supportingList || "<li>Official contractual scope recorded in NeST portal.</li>"}</ul>
      </div>
      <div class="point-card concerning">
        <h5>${t("concerning_points_heading")}</h5>
        <ul>${concerningList || "<li>No concerning physical discrepancies reported at this time.</li>"}</ul>
      </div>
    </div>

    <div class="recommendation-box">
      <span style="color:var(--text-muted); font-size:0.78rem; text-transform:uppercase; display:block;">${t("recommendation_heading")}:</span>
      ${recon.recommendation}
    </div>

    <div class="disclaimer-box">
      ${t("disclaimer_text")}
    </div>
  `;
}

// --- Screen 5: Human Verification Queue ---
async function loadVerificationQueue() {
  const statusFilter = document.getElementById("queue-review-filter")?.value || "all";
  let url = `/api/verification-queue?status=discrepancy_flagged`;
  if (statusFilter && statusFilter !== "all") {
    url += `&review_status=${statusFilter}`;
  }

  try {
    const res = await fetch(url);
    const items = await res.json();
    renderVerificationQueueTable(items);
  } catch (err) {
    console.error("Error loading verification queue:", err);
  }
}

function renderVerificationQueueTable(items) {
  const tbody = document.getElementById("queue-tbody");
  if (!tbody) return;
  tbody.innerHTML = "";

  if (items.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding:32px; color:var(--text-muted);">${t("no_queue_items")}</td></tr>`;
    return;
  }

  items.forEach(item => {
    const tr = document.createElement("tr");
    const proj = item.project || {};

    let reviewBadge = `<span class="badge" style="background:#fffbeb; color:#b45309; border:1px solid #fde68a;">${t("review_status_pending")}</span>`;
    if (item.human_review_status === "verified") {
      reviewBadge = `<span class="badge badge-discrepancy">${t("review_status_verified")}</span>`;
    } else if (item.human_review_status === "resolved") {
      reviewBadge = `<span class="badge badge-consistent">${t("review_status_resolved")}</span>`;
    } else if (item.human_review_status === "dismissed") {
      reviewBadge = `<span class="badge badge-needs-evidence">${t("review_status_dismissed")}</span>`;
    }

    tr.innerHTML = `
      <td class="project-name-cell">
        <a href="javascript:void(0)" onclick="viewProject('${item.project_id}')">${proj.title || item.project_id}</a>
        <div class="project-ocid">${item.project_id}</div>
      </td>
      <td><strong>${proj.buyer || 'N/A'}</strong></td>
      <td class="value-cell">${formatCurrency(proj.contract_value, proj.currency)}</td>
      <td><span class="badge badge-needs-evidence">${item.confidence.toUpperCase()}</span></td>
      <td>${reviewBadge}</td>
      <td>
        <div style="display:flex; gap:6px; flex-wrap:wrap;">
          <button class="btn btn-danger btn-sm" onclick="openReviewModal(${item.id}, 'verified')">${t("mark_verified_btn")}</button>
          <button class="btn btn-success btn-sm" onclick="openReviewModal(${item.id}, 'resolved')">${t("mark_resolved_btn")}</button>
          <button class="btn btn-secondary btn-sm" onclick="openReviewModal(${item.id}, 'dismissed')">${t("dismiss_btn")}</button>
        </div>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function openReviewModal(reconciliationId, actionType) {
  pendingReviewAction = { reconciliationId, actionType };
  const modal = document.getElementById("review-modal");
  const title = document.getElementById("review-modal-title");
  const instr = document.getElementById("review-modal-instruction");
  const confirmBtn = document.getElementById("review-modal-confirm-btn");

  if (actionType === "verified") {
    title.textContent = "Confirm Discrepancy (Flag for Field Audit)";
    instr.textContent = "You are confirming this discrepancy for formal field investigation by auditors.";
    confirmBtn.className = "btn btn-danger btn-sm";
    confirmBtn.textContent = "Confirm for Investigation";
  } else if (actionType === "resolved") {
    title.textContent = "Mark as Resolved";
    instr.textContent = "Record contractor or procuring entity clarification resolving this issue.";
    confirmBtn.className = "btn btn-success btn-sm";
    confirmBtn.textContent = "Mark Resolved";
  } else {
    title.textContent = "Dismiss Flag";
    instr.textContent = "Dismiss this report if evidence is outdated, duplicate, or irrelevant.";
    confirmBtn.className = "btn btn-secondary btn-sm";
    confirmBtn.textContent = "Dismiss";
  }

  document.getElementById("review-modal-notes").value = "";
  modal.style.display = "flex";
}

function closeReviewModal() {
  document.getElementById("review-modal").style.display = "none";
  pendingReviewAction = null;
}

async function submitReviewAction() {
  if (!pendingReviewAction) return;
  const notes = document.getElementById("review-modal-notes").value.trim();

  try {
    const res = await fetch(`/api/verification-queue/${pendingReviewAction.reconciliationId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        human_review_status: pendingReviewAction.actionType,
        human_notes: notes || "Auditor action applied."
      })
    });
    if (res.ok) {
      closeReviewModal();
      loadVerificationQueue();
      fetchStats();
    }
  } catch (err) {
    console.error("Error updating review status:", err);
  }
}

// --- Initialization ---
document.addEventListener("DOMContentLoaded", () => {
  setLanguage(currentLang);
  fetchAiEngineStatus();
  fetchStats();
  loadProjects();

  // Set today's date as default for evidence date picker
  const dateInput = document.getElementById("evidence-date");
  if (dateInput) {
    dateInput.value = new Date().toISOString().split("T")[0];
  }

  // Event Listeners
  document.getElementById("search-input")?.addEventListener("input", loadProjects);
  document.getElementById("region-filter")?.addEventListener("change", loadProjects);
  document.getElementById("sector-filter")?.addEventListener("change", loadProjects);
  document.getElementById("status-filter")?.addEventListener("change", loadProjects);
  document.getElementById("queue-review-filter")?.addEventListener("change", loadVerificationQueue);
  document.getElementById("evidence-form")?.addEventListener("submit", handleEvidenceSubmit);
});
