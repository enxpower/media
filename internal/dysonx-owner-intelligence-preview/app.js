const DECISION_OPTIONS = [
  {
    label: "Approve for later review",
    value: "approve_for_future_publish_readiness_review",
  },
  {
    label: "Need more sources",
    value: "request_more_sources",
  },
  {
    label: "Regenerate analysis",
    value: "request_regeneration",
  },
  {
    label: "Reject",
    value: "reject",
  },
  {
    label: "Hold",
    value: "hold",
  },
];

const ALLOWED_DECISIONS = DECISION_OPTIONS.map((option) => option.value);
const ALLOWED_PRIORITIES = ["high", "medium", "low"];

const AUTO_DECISION_TO_OWNER_DECISION = {
  auto_reject: "reject",
  needs_more_sources: "request_more_sources",
  needs_regeneration: "request_regeneration",
  hold: "hold",
  candidate_for_publish_readiness_review: "approve_for_future_publish_readiness_review",
};

const HUMAN_ACTION_LABELS = {
  candidate_for_human_approval: "Review for later readiness",
  candidate_for_publish_readiness_review: "Candidate for later readiness review",
  needs_human_review: "Needs human review",
  improve_or_regenerate: "Regenerate analysis",
  blocked_by_quality_risk: "Reject / blocked",
  reject_or_regenerate: "Reject or regenerate",
  auto_reject: "Reject automatically",
  needs_more_sources: "Need more sources",
  needs_regeneration: "Regenerate analysis",
  hold: "Hold",
  request_more_sources: "Need more sources",
  request_regeneration: "Regenerate analysis",
  reject: "Reject",
  approve_for_future_publish_readiness_review: "Approve for later review",
};

const RESULTING_STATUS_BY_DECISION = {
  approve_for_future_publish_readiness_review: "owner_approved_for_later_publish_readiness_review_only",
  request_more_sources: "needs_more_sources",
  request_regeneration: "needs_regeneration",
  reject: "owner_rejected",
  hold: "owner_hold",
};

const NEXT_ACTION_BY_DECISION = {
  approve_for_future_publish_readiness_review: "later_publish_readiness_review_required",
  request_more_sources: "collect_or_attach_more_sources",
  request_regeneration: "regenerate_or_improve_signal_analysis",
  reject: "remove_from_current_review_queue",
  hold: "keep_for_later_review",
};

const SAFETY_FLAGS = {
  openai_call_performed: false,
  workflow_dispatched: false,
  publishing_performed: false,
  publication_approved: false,
  publish_readiness_enabled: false,
  public_content_generated: false,
  website_pages_written: false,
  social_posting_performed: false,
  notion_mutation_performed: false,
  live_github_api_used: false,
  article_body_scraping_performed: false,
  raw_provider_response_stored: false,
  knowledge_graph_write_performed: false,
  prediction_engine_performed: false,
  confidence_calibration_performed: false,
  correlation_performed: false,
  deployment_performed: false,
};

const state = {
  brief: null,
  sourceName: "internal/dysonx-owner-intelligence-preview/brief_fixture.json",
  feedbackJson: "",
  ownerDecisionDefaults: new Map(),
};

function text(value) {
  return String(value || "").trim();
}

function arrayValue(value) {
  return Array.isArray(value) ? value.filter(Boolean).map(String) : [];
}

function el(tag, className, content) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (content !== undefined) node.textContent = content;
  return node;
}

function clear(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
}

function setStatus(message) {
  document.getElementById("load-status").textContent = message;
}

function setExportStatus(message) {
  document.getElementById("export-status").textContent = message;
}

function requireBrief(brief) {
  if (!brief || typeof brief !== "object") throw new Error("Brief must be a JSON object.");
  if (brief.brief_version !== "internal_intelligence_brief_v1") {
    throw new Error("Brief must be Internal Intelligence Brief V1.");
  }
  if (!Array.isArray(brief.owner_review_queue)) {
    throw new Error("Brief owner_review_queue must be present.");
  }
}

function recordsBySignalId(brief) {
  const records = []
    .concat(brief.decision_grade_candidates || [])
    .concat(brief.useful_review_queue || [])
    .concat(brief.blocked_or_low_value || []);
  return new Map(records.map((record) => [record.signal_id, record]));
}

function recordForQueueItem(brief, item) {
  const details = recordsBySignalId(brief);
  return { ...(details.get(item.signal_id) || {}), ...item };
}

function tierLabel(tier) {
  if (tier && tier.includes("Tier A")) return "Decision-grade";
  if (tier && tier.includes("Tier B")) return "Useful review";
  if (tier && tier.includes("Tier C")) return "Needs work";
  if (tier && tier.includes("Tier D")) return "Rejected / blocked";
  return tier || "Unscored";
}

function scoreText(record) {
  const total = record.quality_score_total ?? record.score ?? 0;
  const max = record.quality_score_max ?? 65;
  return `${total} / ${max}`;
}

function risks(record) {
  return arrayValue(record.risk_flags || record.critical_risk_flags);
}

function riskSummary(record) {
  return text(record.risk_summary) || (risks(record).length ? risks(record).join(", ") : "No critical risk flags.");
}

function humanAction(value) {
  const key = text(value);
  return HUMAN_ACTION_LABELS[key] || key || "Hold";
}

function autoDecisionValue(record) {
  const value = text(record.auto_decision);
  return AUTO_DECISION_TO_OWNER_DECISION[value] ? value : "hold";
}

function autoDecisionLabel(record) {
  return text(record.decision_label) || humanAction(autoDecisionValue(record));
}

function ownerDecisionDefault(record) {
  return AUTO_DECISION_TO_OWNER_DECISION[autoDecisionValue(record)] || "hold";
}

function shortText(value, maxLength = 180) {
  const content = text(value);
  if (content.length <= maxLength) return content;
  return `${content.slice(0, maxLength - 1).trim()}…`;
}

function isOwnerAttention(record) {
  const decision = autoDecisionValue(record);
  return decision === "candidate_for_publish_readiness_review" || decision === "needs_more_sources";
}

function isBlockedLowValue(record) {
  return autoDecisionValue(record) === "auto_reject"
    || text(record.quality_tier || record.tier).includes("Tier D")
    || risks(record).includes("generic_summary");
}

function allQueueDetails(brief) {
  return brief.owner_review_queue.map((item) => recordForQueueItem(brief, item));
}

function workCounts(brief) {
  const records = allQueueDetails(brief);
  const counts = {
    total: records.length,
    ownerAttention: records.filter(isOwnerAttention).length,
    autoHandled: records.filter((record) => !isOwnerAttention(record)).length,
    candidates: records.filter((record) => autoDecisionValue(record) === "candidate_for_publish_readiness_review").length,
    moreSources: records.filter((record) => autoDecisionValue(record) === "needs_more_sources").length,
    regenerate: records.filter((record) => autoDecisionValue(record) === "needs_regeneration").length,
    hold: records.filter((record) => autoDecisionValue(record) === "hold").length,
    rejected: records.filter((record) => autoDecisionValue(record) === "auto_reject").length,
    overridden: document.querySelectorAll('.review-card[data-owner-overridden="true"]').length,
  };
  counts.readyToExport = counts.total > 0 ? counts.total : 0;
  return counts;
}

function compactList(values) {
  const filtered = arrayValue(values);
  return filtered.length ? filtered.join(", ") : "none";
}

function fieldRow(label, value, className) {
  const row = el("div", className || "");
  row.append(el("dt", "", `${label}: `), el("dd", "", value || "none"));
  return row;
}

function fieldList(fields) {
  const dl = el("dl", "field-list");
  fields.forEach(([label, value, className]) => dl.appendChild(fieldRow(label, value, className)));
  return dl;
}

function renderMetadata(brief) {
  const metadata = document.getElementById("brief-metadata");
  clear(metadata);
  [
    ["brief_version", brief.brief_version],
    ["created_at", brief.created_at],
    ["source_score_report", brief.source_score_report],
    ["signals_reviewed", brief.signals_reviewed],
    ["generated_for", brief.generated_for],
  ].forEach(([label, value]) => {
    metadata.append(el("dt", "", label), el("dd", "", value));
  });
}

function renderWorkSummary(brief) {
  const target = document.getElementById("work-summary");
  clear(target);
  const counts = workCounts(brief);
  const cards = [
    ["Needs Owner Attention", counts.ownerAttention],
    ["Auto-handled", counts.autoHandled],
    ["Candidates", counts.candidates],
    ["More Sources", counts.moreSources],
    ["Regenerate", counts.regenerate],
    ["Hold", counts.hold],
    ["Rejected", counts.rejected],
    ["Overrides", counts.overridden],
    ["Ready to export feedback", counts.readyToExport],
  ];
  cards.forEach(([label, value]) => {
    const card = el("div", "score-card");
    card.append(el("strong", "", value), el("span", "", label));
    target.appendChild(card);
  });
}

function topSignal(brief) {
  const candidates = brief.decision_grade_candidates || [];
  if (candidates.length) return candidates[0];
  return (brief.useful_review_queue || [])[0] || (brief.owner_review_queue || [])[0] || null;
}

function renderTopSignal(brief) {
  const target = document.getElementById("top-signal-card");
  const tier = document.getElementById("top-signal-tier");
  clear(target);
  const signal = topSignal(brief);
  if (!signal) {
    target.appendChild(el("p", "muted", "No Signals available."));
    tier.textContent = "No Signal";
    return;
  }

  tier.textContent = tierLabel(signal.quality_tier || signal.tier);
  target.appendChild(el("h3", "", signal.title || "(untitled signal)"));
  target.appendChild(el("p", "takeaway", signal.executive_takeaway || "No executive takeaway provided."));

  const source = el("p", "source-line");
  source.appendChild(el("strong", "", "Source: "));
  if (signal.source_url) {
    const link = document.createElement("a");
    link.href = signal.source_url;
    link.target = "_blank";
    link.rel = "noreferrer";
    link.textContent = signal.source_url;
    source.appendChild(link);
  } else {
    source.appendChild(document.createTextNode("none"));
  }
  target.appendChild(source);

  target.appendChild(fieldList([
    ["Source authority", signal.source_authority],
    ["AGI capability affected", signal.agi_capability],
    ["Score", scoreText(signal)],
    ["Tier", signal.quality_tier || signal.tier],
    ["Why it matters", signal.why_it_matters],
    ["Watch next", signal.watch_next],
    ["Risk summary", riskSummary(signal), risks(signal).length ? "risk" : ""],
    ["Recommended owner action", humanAction(signal.auto_decision || signal.recommended_action)],
  ]));
}

function renderBlocked(brief) {
  const target = document.getElementById("blocked-low-value");
  clear(target);
  const records = allQueueDetails(brief).filter(isBlockedLowValue);
  if (!records.length) {
    target.appendChild(el("p", "muted", "No blocked or low-value Signals."));
    return;
  }
  records.forEach((record) => {
    const card = el("article", "compact-card");
    card.appendChild(el("h3", "", record.title || "(untitled signal)"));
    card.appendChild(fieldList([
      ["Tier", tierLabel(record.quality_tier || record.tier)],
      ["Auto Decision", autoDecisionLabel(record)],
      ["Score", scoreText(record)],
      ["Reason", shortText(riskSummary(record), 140), risks(record).length ? "risk" : ""],
      ["Missing fields", compactList(record.missing_fields)],
      ["Recommended action", humanAction(record.auto_decision || record.recommended_action)],
    ]));
    target.appendChild(card);
  });
}

function decisionControl(defaultValue) {
  const select = document.createElement("select");
  DECISION_OPTIONS.forEach((option) => {
    const node = document.createElement("option");
    node.value = option.value;
    node.textContent = option.label;
    if (option.value === defaultValue) node.selected = true;
    select.appendChild(node);
  });
  return select;
}

function priorityControl(defaultValue) {
  const select = document.createElement("select");
  ALLOWED_PRIORITIES.forEach((priority) => {
    const node = document.createElement("option");
    node.value = priority;
    node.textContent = priority.charAt(0).toUpperCase() + priority.slice(1);
    if (priority === defaultValue) node.selected = true;
    select.appendChild(node);
  });
  return select;
}

function compactSignalCard(detail, index) {
  const defaultDecision = ownerDecisionDefault(detail);
  const card = el("article", "review-card compact-signal-card");
  card.dataset.signalId = detail.signal_id;
  card.dataset.systemDefaultOwnerDecision = defaultDecision;
  card.dataset.ownerOverridden = "false";
  card.dataset.needsOwnerAttention = isOwnerAttention(detail) ? "true" : "false";
  state.ownerDecisionDefaults.set(detail.signal_id, defaultDecision);
  card.appendChild(el("div", "queue-rank", `#${index + 1}`));
  card.appendChild(el("h3", "", detail.title || "(untitled signal)"));
  card.appendChild(el("p", "takeaway", shortText(detail.executive_takeaway || detail.why_it_matters || "No executive takeaway provided.", 190)));
  card.appendChild(el("p", "system-default", "System default decision applied. Owner can override."));
  card.appendChild(fieldList([
    ["Auto Decision", autoDecisionLabel(detail)],
    ["Score", scoreText(detail)],
    ["Tier", tierLabel(detail.tier || detail.quality_tier)],
    ["Risk summary", shortText(riskSummary(detail), 150), risks(detail).length ? "risk" : ""],
    ["Missing fields", compactList(detail.missing_fields)],
    ["Why it matters", shortText(detail.why_it_matters, 160)],
    ["Watch next", shortText(detail.watch_next, 160)],
  ]));

  const controls = el("div", "review-controls");
  const decisionLabel = el("label", "", "Owner decision");
  const decision = decisionControl(defaultDecision);
  decision.className = "decision-input";
  decisionLabel.appendChild(decision);

  const priorityLabel = el("label", "", "Priority");
  const priority = priorityControl("medium");
  priority.className = "priority-input";
  priorityLabel.appendChild(priority);

  const commentLabel = el("label", "", "Owner comment");
  const comment = document.createElement("textarea");
  comment.className = "comment-input";
  comment.placeholder = "Why this decision?";
  comment.rows = 2;
  commentLabel.appendChild(comment);

  const followLabel = el("label", "checkbox-label", "Follow-up required");
  const follow = document.createElement("input");
  follow.className = "follow-input";
  follow.type = "checkbox";
  followLabel.prepend(follow);

  const noteLabel = el("label", "", "Follow-up note");
  const note = document.createElement("input");
  note.className = "follow-note-input";
  note.type = "text";
  note.placeholder = "What should happen next?";
  noteLabel.appendChild(note);

  controls.append(decisionLabel, priorityLabel, commentLabel, followLabel, noteLabel);
  card.appendChild(controls);

  const details = document.createElement("details");
  details.className = "signal-details";
  const summary = document.createElement("summary");
  summary.textContent = "Show details";
  details.appendChild(summary);
  details.appendChild(fieldList([
    ["Signal ID", detail.signal_id],
    ["Source URL", detail.source_url],
    ["Source authority", detail.source_authority],
    ["AGI capability", detail.agi_capability],
    ["Entities", compactList(detail.entities)],
    ["Full why it matters", detail.why_it_matters],
    ["Full watch next", detail.watch_next],
    ["Recommended action", humanAction(detail.auto_decision || detail.action || detail.recommended_action)],
    ["Raw action", detail.action || detail.recommended_action],
    ["Raw auto decision", detail.auto_decision],
  ]));
  card.appendChild(details);
  return card;
}

function renderReviewQueue(brief) {
  const attentionTarget = document.getElementById("needs-owner-attention");
  const autoTarget = document.getElementById("auto-handled");
  clear(attentionTarget);
  clear(autoTarget);
  state.ownerDecisionDefaults.clear();
  const records = allQueueDetails(brief);
  const attention = records.filter(isOwnerAttention);
  const autoHandled = records.filter((record) => !isOwnerAttention(record) && !isBlockedLowValue(record));
  if (!attention.length) attentionTarget.appendChild(el("p", "muted", "No Signals require Owner attention."));
  if (!autoHandled.length) autoTarget.appendChild(el("p", "muted", "No auto-handled Signals outside blocked summaries."));
  attention.forEach((detail, index) => attentionTarget.appendChild(compactSignalCard(detail, index)));
  autoHandled.forEach((detail, index) => autoTarget.appendChild(compactSignalCard(detail, index)));
  wireReviewProgressHandlers();
  updateWorkflowStatus();
}

function renderBrief(brief, sourceName) {
  requireBrief(brief);
  state.brief = brief;
  state.sourceName = sourceName || state.sourceName;
  document.getElementById("overall-recommendation").textContent =
    brief.overall_recommendation || "Review Signals internally. Do not publish yet.";
  renderWorkSummary(brief);
  renderTopSignal(brief);
  renderReviewQueue(brief);
  renderBlocked(brief);
  renderMetadata(brief);
  setStatus(`Loaded ${state.sourceName}`);
  document.getElementById("generate-feedback-top").disabled = false;
  updateWorkflowStatus();
}

async function loadFixture() {
  const response = await fetch("./brief_fixture.json", { cache: "no-store" });
  if (!response.ok) throw new Error(`Could not load fixture: ${response.status}`);
  const brief = await response.json();
  renderBrief(brief, "internal/dysonx-owner-intelligence-preview/brief_fixture.json");
}

function loadFile(file) {
  const reader = new FileReader();
  reader.onload = () => {
    try {
      renderBrief(JSON.parse(reader.result), file.name);
    } catch (error) {
      setStatus(error.message);
    }
  };
  reader.readAsText(file);
}

function feedbackRecords() {
  return allQueueDetails(state.brief).map((detail) => {
    const signalId = detail.signal_id;
    const item = state.brief.owner_review_queue.find((entry) => entry.signal_id === signalId);
    const card = document.querySelector(`.review-card[data-signal-id="${CSS.escape(signalId)}"]`);
    const defaultDecision = card?.dataset.systemDefaultOwnerDecision || ownerDecisionDefault(detail);
    const ownerDecision = card?.querySelector(".decision-input").value || defaultDecision;
    const ownerOverridden = ownerDecision !== defaultDecision;
    return {
      signal_id: signalId,
      title: item.title || detail.title,
      auto_decision: autoDecisionValue(detail),
      system_default_owner_decision: defaultDecision,
      selected_owner_decision: ownerDecision,
      owner_overridden: ownerOverridden,
      original_tier: item.tier || detail.tier || detail.quality_tier,
      original_recommended_action: item.action || detail.recommended_action,
      owner_decision: ownerDecision,
      owner_comment: card?.querySelector(".comment-input").value || "",
      priority: card?.querySelector(".priority-input").value || "low",
      follow_up_required: card?.querySelector(".follow-input").checked || false,
      follow_up_note: card?.querySelector(".follow-note-input").value || "",
      resulting_status: RESULTING_STATUS_BY_DECISION[ownerDecision],
      next_action: NEXT_ACTION_BY_DECISION[ownerDecision],
      owner_override_allowed: true,
      publish_readiness_candidate: Boolean(detail.publish_readiness_candidate),
      publication_approved: false,
    };
  });
}

function updateWorkflowStatus() {
  const cards = Array.from(document.querySelectorAll(".review-card"));
  const overridden = cards.filter((card) => card.dataset.ownerOverridden === "true").length;
  const total = state.brief ? allQueueDetails(state.brief).length : cards.length;
  const systemDecided = total;
  const ownerAttention = state.brief ? workCounts(state.brief).ownerAttention : 0;
  const progress = document.getElementById("workflow-status");
  progress.innerHTML = "";
  progress.append(
    el("span", "", `System-decided: ${systemDecided}`),
    el("span", "", `Owner-overridden: ${overridden}`),
    el("span", "", `Needs Owner attention: ${ownerAttention}`),
    el("span", "", `Total Signals: ${total}`),
  );
  const exportSummary = document.getElementById("export-action-summary");
  exportSummary.innerHTML = "";
  exportSummary.append(
    el("span", "", `System-decided: ${systemDecided}`),
    el("span", "", `Owner-overridden: ${overridden}`),
    el("span", "", `Needs Owner attention: ${ownerAttention}`),
  );
  if (state.brief) renderWorkSummary(state.brief);
}

function markOwnerConfirmed(event) {
  const card = event.target.closest(".review-card");
  if (!card) return;
  const decision = card.querySelector(".decision-input").value;
  const defaultDecision = card.dataset.systemDefaultOwnerDecision;
  const overridden = decision !== defaultDecision;
  card.dataset.ownerOverridden = overridden ? "true" : "false";
  const status = card.querySelector(".system-default");
  if (status) status.textContent = overridden ? "Owner override" : "System default decision applied. Owner can override.";
  updateWorkflowStatus();
}

function wireReviewProgressHandlers() {
  document.querySelectorAll(".review-card select, .review-card textarea, .review-card input").forEach((input) => {
    input.addEventListener("change", markOwnerConfirmed);
    input.addEventListener("input", markOwnerConfirmed);
  });
}

function decisionCounts(records) {
  const counts = Object.fromEntries(ALLOWED_DECISIONS.map((decision) => [decision, 0]));
  records.forEach((record) => {
    counts[record.owner_decision] += 1;
  });
  return counts;
}

function recommendedNextActions(records) {
  const decisions = new Set(records.map((record) => record.owner_decision));
  const actions = [];
  if (decisions.has("request_more_sources")) actions.push("Prepare better source evidence for Signals marked Need more sources.");
  if (decisions.has("request_regeneration")) actions.push("Regenerate or improve selected Signal analysis offline.");
  if (decisions.has("hold")) actions.push("Keep held Signals in the next internal brief or owner review queue.");
  if (decisions.has("approve_for_future_publish_readiness_review")) {
    actions.push("Future publish-readiness review is required; do not publish automatically.");
  }
  if (decisions.has("reject")) actions.push("Remove rejected Signals from the current owner review queue.");
  actions.push("Do not publish yet.");
  return actions;
}

function generateFeedbackJson() {
  if (!state.brief) {
    setStatus("Load a brief before generating feedback.");
    return;
  }
  const now = new Date().toISOString();
  const records = feedbackRecords();
  const report = {
    feedback_version: "owner_review_feedback_v1",
    created_at: now,
    reviewer: "Owner",
    review_session_id: `owner-console-${now}`,
    reviewed_at: now,
    source_brief: state.sourceName,
    brief_version: state.brief.brief_version,
    signals_reviewed: state.brief.signals_reviewed,
    decisions_recorded: records.length,
    decision_counts: decisionCounts(records),
    follow_up_required_count: records.filter((record) => record.follow_up_required).length,
    publish_readiness_enabled: false,
    publication_approved: false,
    safety_statement: "This is not publication approval.",
    feedback_records: records,
    recommended_next_actions: recommendedNextActions(records),
    safety_flags: { ...SAFETY_FLAGS },
  };
  state.feedbackJson = JSON.stringify(report, null, 2);
  document.getElementById("feedback-output").value = state.feedbackJson;
  document.getElementById("download-feedback").disabled = false;
  document.getElementById("copy-feedback").disabled = false;
  document.getElementById("download-feedback-sticky").disabled = false;
  document.getElementById("copy-feedback-sticky").disabled = false;
  setExportStatus("Feedback JSON generated locally. This is not publishing approval.");
}

async function copyFeedbackJson() {
  if (!state.feedbackJson) return;
  await navigator.clipboard.writeText(state.feedbackJson);
  setExportStatus("Feedback JSON copied.");
}

function downloadFeedbackJson() {
  if (!state.feedbackJson) return;
  const blob = new Blob([`${state.feedbackJson}\n`], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "dysonx_owner_review_feedback_console.json";
  link.click();
  URL.revokeObjectURL(url);
}

document.getElementById("load-fixture").addEventListener("click", () => {
  loadFixture().catch((error) => setStatus(error.message));
});

document.getElementById("brief-file").addEventListener("change", (event) => {
  const [file] = event.target.files;
  if (file) loadFile(file);
});

document.getElementById("generate-feedback").addEventListener("click", generateFeedbackJson);
document.getElementById("generate-feedback-top").addEventListener("click", generateFeedbackJson);
document.getElementById("generate-feedback-sticky").addEventListener("click", generateFeedbackJson);
document.getElementById("download-feedback").addEventListener("click", downloadFeedbackJson);
document.getElementById("download-feedback-sticky").addEventListener("click", downloadFeedbackJson);
document.getElementById("copy-feedback").addEventListener("click", () => {
  copyFeedbackJson().catch(() => setExportStatus("Copy failed. Select the JSON text and copy manually."));
});
document.getElementById("copy-feedback-sticky").addEventListener("click", () => {
  copyFeedbackJson().catch(() => setExportStatus("Copy failed. Select the JSON text and copy manually."));
});

loadFixture().catch(() => {
  setStatus("Open through a local server to auto-load the fixture, or choose a JSON file manually.");
});
