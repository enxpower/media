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

function renderScoreCards(brief) {
  const target = document.getElementById("score-cards");
  clear(target);
  const tierCounts = brief.tier_counts || {};
  const cards = [
    ["Decision-grade", tierCounts["Tier A: Decision-grade Signal"] || 0],
    ["Useful review", tierCounts["Tier B: Useful Signal"] || 0],
    ["Needs work", tierCounts["Tier C: Needs Review"] || 0],
    ["Rejected / blocked", tierCounts["Tier D: Reject / Low-value"] || 0],
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
  const records = brief.blocked_or_low_value || [];
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
      ["Reason", riskSummary(record), risks(record).length ? "risk" : ""],
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

function renderReviewQueue(brief) {
  const target = document.getElementById("owner-review-queue");
  clear(target);
  brief.owner_review_queue.forEach((item, index) => {
    const detail = recordForQueueItem(brief, item);
    const defaultDecision = ownerDecisionDefault(detail);
    const card = el("article", "review-card");
    card.dataset.signalId = item.signal_id;
    card.dataset.ownerConfirmed = "false";
    card.appendChild(el("div", "queue-rank", `#${index + 1}`));
    card.appendChild(el("h3", "", item.title || "(untitled signal)"));
    card.appendChild(el("p", "takeaway", detail.executive_takeaway || "No executive takeaway provided."));
    card.appendChild(el("p", "system-default", "System default decision applied. Owner can override."));
    card.appendChild(fieldList([
      ["Signal ID", item.signal_id],
      ["Auto Decision", autoDecisionLabel(detail)],
      ["Score", scoreText(detail)],
      ["Tier", tierLabel(item.tier || detail.quality_tier)],
      ["Risk summary", riskSummary(detail), risks(detail).length ? "risk" : ""],
      ["Missing fields", compactList(detail.missing_fields)],
      ["Recommended action", humanAction(detail.auto_decision || item.action || detail.recommended_action)],
      ["Source", detail.source_url],
      ["Source authority", detail.source_authority],
      ["AGI capability", detail.agi_capability],
      ["Entities", compactList(detail.entities)],
      ["Why it matters", detail.why_it_matters],
      ["Watch next", detail.watch_next],
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
    comment.rows = 3;
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
    target.appendChild(card);
  });
  wireReviewProgressHandlers();
  updateReviewProgress();
}

function renderBrief(brief, sourceName) {
  requireBrief(brief);
  state.brief = brief;
  state.sourceName = sourceName || state.sourceName;
  document.getElementById("overall-recommendation").textContent =
    brief.overall_recommendation || "Review Signals internally. Do not publish yet.";
  renderScoreCards(brief);
  renderTopSignal(brief);
  renderReviewQueue(brief);
  renderBlocked(brief);
  renderMetadata(brief);
  setStatus(`Loaded ${state.sourceName}`);
  document.getElementById("generate-feedback-top").disabled = false;
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
  return Array.from(document.querySelectorAll(".review-card")).map((card) => {
    const signalId = card.dataset.signalId;
    const item = state.brief.owner_review_queue.find((entry) => entry.signal_id === signalId);
    const ownerDecision = card.querySelector(".decision-input").value;
    return {
      signal_id: signalId,
      title: item.title,
      original_tier: item.tier,
      original_recommended_action: item.action,
      owner_decision: ownerDecision,
      owner_comment: card.querySelector(".comment-input").value,
      priority: card.querySelector(".priority-input").value,
      follow_up_required: card.querySelector(".follow-input").checked,
      follow_up_note: card.querySelector(".follow-note-input").value,
      resulting_status: RESULTING_STATUS_BY_DECISION[ownerDecision],
      next_action: NEXT_ACTION_BY_DECISION[ownerDecision],
      owner_override_allowed: true,
      publication_approved: false,
    };
  });
}

function updateReviewProgress() {
  const cards = Array.from(document.querySelectorAll(".review-card"));
  const reviewed = cards.filter((card) => card.dataset.ownerConfirmed === "true").length;
  const total = cards.length;
  const pending = Math.max(total - reviewed, 0);
  const progress = document.getElementById("review-progress");
  progress.innerHTML = "";
  progress.append(
    el("span", "", `Reviewed: ${reviewed}`),
    el("span", "", `Pending: ${pending}`),
    el("span", "", `Total: ${total}`),
  );
}

function markOwnerConfirmed(event) {
  const card = event.target.closest(".review-card");
  if (!card) return;
  card.dataset.ownerConfirmed = "true";
  const status = card.querySelector(".system-default");
  if (status) status.textContent = "Owner decision confirmed or overridden.";
  updateReviewProgress();
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
    feedback_records: records,
    recommended_next_actions: recommendedNextActions(records),
    safety_flags: { ...SAFETY_FLAGS },
  };
  state.feedbackJson = JSON.stringify(report, null, 2);
  document.getElementById("feedback-output").value = state.feedbackJson;
  document.getElementById("download-feedback").disabled = false;
  document.getElementById("copy-feedback").disabled = false;
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
document.getElementById("download-feedback").addEventListener("click", downloadFeedbackJson);
document.getElementById("copy-feedback").addEventListener("click", () => {
  copyFeedbackJson().catch(() => setExportStatus("Copy failed. Select the JSON text and copy manually."));
});

loadFixture().catch(() => {
  setStatus("Open through a local server to auto-load the fixture, or choose a JSON file manually.");
});
