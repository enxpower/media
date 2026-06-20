const ALLOWED_DECISIONS = [
  "approve_for_future_publish_readiness_review",
  "request_more_sources",
  "request_regeneration",
  "reject",
  "hold",
];

const ALLOWED_PRIORITIES = ["high", "medium", "low"];

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

function list(value) {
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

function requireBrief(brief) {
  if (!brief || typeof brief !== "object") throw new Error("Brief must be a JSON object.");
  if (brief.brief_version !== "internal_intelligence_brief_v1") {
    throw new Error("Brief must be Internal Intelligence Brief V1.");
  }
  if (!Array.isArray(brief.owner_review_queue)) {
    throw new Error("Brief owner_review_queue must be present.");
  }
}

function recordBySignalId(brief) {
  const records = []
    .concat(brief.decision_grade_candidates || [])
    .concat(brief.useful_review_queue || [])
    .concat(brief.blocked_or_low_value || []);
  return new Map(records.map((record) => [record.signal_id, record]));
}

function fieldList(fields) {
  const dl = el("dl", "field-list");
  fields.forEach(([label, value, className]) => {
    const row = el("div", className || "");
    const dt = el("dt", "", `${label}: `);
    const dd = el("dd", "", value || "none");
    row.append(dt, dd);
    dl.appendChild(row);
  });
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

function renderSummary(brief) {
  const summary = document.getElementById("executive-summary");
  clear(summary);
  const metrics = [
    ["Signals reviewed", brief.signals_reviewed],
    ["Blocked count", brief.blocked_count],
    ["Human review", brief.human_review_count],
    ["Correlation hints", brief.correlation_recommended_count],
  ];
  metrics.forEach(([label, value]) => {
    const metric = el("div", "metric");
    metric.append(el("strong", "", value), el("span", "", label));
    summary.appendChild(metric);
  });
  const recommendation = el("div", "metric");
  recommendation.append(el("strong", "", "Recommendation"), el("span", "", brief.overall_recommendation));
  summary.appendChild(recommendation);
  const tiers = el("div", "metric");
  tiers.append(el("strong", "", "Tier counts"), el("span", "", JSON.stringify(brief.tier_counts || {})));
  summary.appendChild(tiers);
}

function renderSignalCard(record) {
  const card = el("article", "signal-card");
  card.appendChild(el("h3", "", text(record.title) || "(untitled signal)"));
  card.appendChild(fieldList([
    ["signal_id", record.signal_id],
    ["source_url", record.source_url],
    ["tier", record.quality_tier],
    ["recommended_action", record.recommended_action],
    ["score", `${record.quality_score_total || 0} / ${record.quality_score_max || 0}`],
    ["risk_flags", list(record.risk_flags || record.critical_risk_flags).join(", "), list(record.risk_flags || record.critical_risk_flags).length ? "risk" : ""],
    ["missing_fields", list(record.missing_fields).join(", ")],
  ]));
  return card;
}

function renderSignalList(id, records, emptyText) {
  const target = document.getElementById(id);
  clear(target);
  if (!records || records.length === 0) {
    target.appendChild(el("p", "muted", emptyText));
    return;
  }
  records.forEach((record) => target.appendChild(renderSignalCard(record)));
}

function selectControl(value, options) {
  const select = document.createElement("select");
  options.forEach((option) => {
    const node = document.createElement("option");
    node.value = option;
    node.textContent = option;
    if (option === value) node.selected = true;
    select.appendChild(node);
  });
  return select;
}

function renderReviewQueue(brief) {
  const target = document.getElementById("owner-review-queue");
  const details = recordBySignalId(brief);
  clear(target);
  brief.owner_review_queue.forEach((item) => {
    const detail = details.get(item.signal_id) || {};
    const card = el("article", "review-card");
    card.dataset.signalId = item.signal_id;
    card.appendChild(el("h3", "", item.title || "(untitled signal)"));
    card.appendChild(fieldList([
      ["signal_id", item.signal_id],
      ["tier", item.tier],
      ["recommended_action", item.action],
      ["source_url", detail.source_url],
      ["risk_flags", list(detail.risk_flags || detail.critical_risk_flags).join(", "), list(detail.risk_flags || detail.critical_risk_flags).length ? "risk" : ""],
      ["missing_fields", list(detail.missing_fields).join(", ")],
    ]));

    const controls = el("div", "review-controls");
    const decisionLabel = el("label", "", "Owner decision");
    decisionLabel.appendChild(selectControl("hold", ALLOWED_DECISIONS));
    decisionLabel.querySelector("select").className = "decision-input";

    const priorityLabel = el("label", "", "Priority");
    priorityLabel.appendChild(selectControl("medium", ALLOWED_PRIORITIES));
    priorityLabel.querySelector("select").className = "priority-input";

    const commentLabel = el("label", "", "Owner comment");
    const comment = document.createElement("input");
    comment.className = "comment-input";
    comment.type = "text";
    comment.placeholder = "Optional owner comment";
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
    note.placeholder = "Optional follow-up note";
    noteLabel.appendChild(note);

    controls.append(decisionLabel, priorityLabel, commentLabel, followLabel, noteLabel);
    card.appendChild(controls);
    target.appendChild(card);
  });
}

function renderBrief(brief, sourceName) {
  requireBrief(brief);
  state.brief = brief;
  state.sourceName = sourceName || state.sourceName;
  renderMetadata(brief);
  renderSummary(brief);
  renderSignalList("decision-grade-candidates", brief.decision_grade_candidates, "No decision-grade candidates yet.");
  renderSignalList("useful-review-queue", brief.useful_review_queue, "No useful Signals requiring review.");
  renderSignalList("blocked-low-value", brief.blocked_or_low_value, "No blocked or low-value Signals.");
  renderReviewQueue(brief);
  setStatus(`Loaded ${state.sourceName}`);
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
    };
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
  if (decisions.has("request_more_sources")) actions.push("Prepare better source evidence for Signals marked request_more_sources.");
  if (decisions.has("request_regeneration")) actions.push("Improve Signal analysis prompt or regenerate selected Signals offline.");
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
  const records = feedbackRecords();
  const report = {
    feedback_version: "owner_review_feedback_v1",
    created_at: new Date().toISOString(),
    reviewer: "Owner",
    review_session_id: `owner-preview-${new Date().toISOString()}`,
    reviewed_at: new Date().toISOString(),
    source_brief: state.sourceName,
    brief_version: state.brief.brief_version,
    signals_reviewed: state.brief.signals_reviewed,
    decisions_recorded: records.length,
    decision_counts: decisionCounts(records),
    follow_up_required_count: records.filter((record) => record.follow_up_required).length,
    feedback_records: records,
    recommended_next_actions: recommendedNextActions(records),
    safety_flags: { ...SAFETY_FLAGS },
  };
  state.feedbackJson = JSON.stringify(report, null, 2);
  document.getElementById("feedback-output").value = state.feedbackJson;
  document.getElementById("download-feedback").disabled = false;
}

function downloadFeedbackJson() {
  if (!state.feedbackJson) return;
  const blob = new Blob([`${state.feedbackJson}\n`], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "dysonx_owner_review_feedback_preview.json";
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
document.getElementById("download-feedback").addEventListener("click", downloadFeedbackJson);

loadFixture().catch(() => {
  setStatus("Open through a local server to auto-load the fixture, or choose a JSON file manually.");
});
