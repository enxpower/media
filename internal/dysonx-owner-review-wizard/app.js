const WIZARD_STORAGE_KEY = "dysonx.ownerReviewWizard.v1";
const WIZARD_VERSION = "v1";
const FIXTURE_URL = "../dysonx-owner-intelligence-preview/brief_fixture.json";

const SCREEN_START = "start";
const SCREEN_ATTENTION = "attention";
const SCREEN_AUTO_HANDLED = "auto_handled";
const SCREEN_SAVE = "save_review";
const SCREEN_GENERATE = "generate_feedback";
const SCREEN_DOWNLOAD = "download_outputs";
const SCREEN_COMPLETE = "complete";

const OWNER_DECISIONS = [
  { value: "approve_for_future_publish_readiness_review", label: "Approve for later readiness review" },
  { value: "request_more_sources", label: "Request more sources" },
  { value: "request_regeneration", label: "Request regeneration" },
  { value: "hold", label: "Hold" },
  { value: "reject", label: "Reject" },
];

const PRIORITIES = ["high", "medium", "low"];

const AUTO_DECISION_DEFAULTS = {
  auto_reject: "reject",
  needs_more_sources: "request_more_sources",
  needs_regeneration: "request_regeneration",
  hold: "hold",
  candidate_for_publish_readiness_review: "approve_for_future_publish_readiness_review",
};

const state = {
  brief: null,
  savedSession: null,
  session: null,
  changeMode: false,
  showHandledDetails: false,
};

const screen = document.getElementById("wizard-screen");
const progress = document.getElementById("wizard-progress");

function createSession() {
  const now = new Date().toISOString();
  return {
    wizard_session_id: `dysonx-wizard-${timestampId(now)}`,
    current_screen: SCREEN_START,
    attention_index: 0,
    attention_item_statuses: {},
    selected_owner_decisions: {},
    priority_values: {},
    owner_comments: {},
    follow_up_required: {},
    follow_up_notes: {},
    owner_overridden: {},
    auto_handled_accepted: false,
    internal_review_saved: false,
    feedback_generated: false,
    feedback_downloaded: false,
    feedback_json: null,
    session_created_at: now,
    session_updated_at: now,
  };
}

function timestampId(value) {
  return value.replace(/[-:]/g, "").replace(/\..+$/, "").replace("T", "-");
}

function saveSession() {
  if (!state.session) return;
  state.session.session_updated_at = new Date().toISOString();
  localStorage.setItem(WIZARD_STORAGE_KEY, JSON.stringify(state.session));
}

function readSavedSession() {
  try {
    const raw = localStorage.getItem(WIZARD_STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch (error) {
    return null;
  }
}

function clearWizardSession() {
  localStorage.removeItem(WIZARD_STORAGE_KEY);
  state.savedSession = null;
  state.session = createSession();
  state.changeMode = false;
  state.showHandledDetails = false;
  render();
}

function startReview(clearExisting = false) {
  if (clearExisting) {
    localStorage.removeItem(WIZARD_STORAGE_KEY);
  }
  state.session = createSession();
  state.session.current_screen = SCREEN_ATTENTION;
  state.session.attention_index = 0;
  initializeDefaults();
  saveSession();
  render();
}

function resumeSavedReview() {
  state.session = normalizeSession(state.savedSession || createSession());
  state.savedSession = null;
  state.changeMode = false;
  state.showHandledDetails = false;
  initializeDefaults();
  render();
}

function normalizeSession(session) {
  return {
    ...createSession(),
    ...session,
    attention_item_statuses: session.attention_item_statuses || {},
    selected_owner_decisions: session.selected_owner_decisions || {},
    priority_values: session.priority_values || {},
    owner_comments: session.owner_comments || {},
    follow_up_required: session.follow_up_required || {},
    follow_up_notes: session.follow_up_notes || {},
    owner_overridden: session.owner_overridden || {},
  };
}

function initializeDefaults() {
  if (!state.brief || !state.session) return;
  allSignals().forEach((signal) => {
    const id = signal.signal_id;
    const defaultDecision = systemDefaultDecision(signal);
    if (!state.session.selected_owner_decisions[id]) {
      state.session.selected_owner_decisions[id] = defaultDecision;
    }
    if (!state.session.priority_values[id]) {
      state.session.priority_values[id] = isAttentionSignal(signal) ? "high" : "medium";
    }
    if (state.session.owner_comments[id] === undefined) {
      state.session.owner_comments[id] = "";
    }
    if (state.session.follow_up_required[id] === undefined) {
      state.session.follow_up_required[id] = false;
    }
    if (state.session.follow_up_notes[id] === undefined) {
      state.session.follow_up_notes[id] = "";
    }
    state.session.owner_overridden[id] = state.session.selected_owner_decisions[id] !== defaultDecision;
  });
}

function allSignals() {
  return [
    ...(state.brief?.decision_grade_candidates || []),
    ...(state.brief?.useful_review_queue || []),
    ...(state.brief?.blocked_or_low_value || []),
  ];
}

function attentionSignals() {
  return allSignals().filter(isAttentionSignal).slice(0, 2);
}

function autoHandledSignals() {
  const attentionIds = new Set(attentionSignals().map((signal) => signal.signal_id));
  return allSignals().filter((signal) => !attentionIds.has(signal.signal_id));
}

function isAttentionSignal(signal) {
  return ["candidate_for_publish_readiness_review", "needs_more_sources"].includes(signal.auto_decision);
}

function systemDefaultDecision(signal) {
  return AUTO_DECISION_DEFAULTS[signal.auto_decision] || "hold";
}

function decisionLabel(value) {
  return OWNER_DECISIONS.find((item) => item.value === value)?.label || value;
}

function screenSteps() {
  return [
    { id: SCREEN_START, label: "Start" },
    { id: SCREEN_ATTENTION, label: "Attention" },
    { id: SCREEN_AUTO_HANDLED, label: "System-handled" },
    { id: SCREEN_SAVE, label: "Save" },
    { id: SCREEN_GENERATE, label: "Generate" },
    { id: SCREEN_DOWNLOAD, label: "Download" },
    { id: SCREEN_COMPLETE, label: "Complete" },
  ];
}

function renderProgress() {
  const current = state.session?.current_screen || SCREEN_START;
  const currentIndex = screenSteps().findIndex((step) => step.id === current);
  progress.innerHTML = "";
  screenSteps().forEach((step, index) => {
    const item = document.createElement("div");
    item.className = "progress-step";
    if (index < currentIndex) item.classList.add("complete");
    if (step.id === current) item.classList.add("current");
    item.textContent = index < currentIndex ? `✓ ${step.label}` : step.label;
    progress.appendChild(item);
  });
}

function render() {
  if (!state.brief) {
    screen.innerHTML = `<p class="error">Unable to load Owner Review Wizard fixture.</p>`;
    return;
  }
  if (!state.session) {
    state.savedSession = readSavedSession();
    state.session = createSession();
  }
  renderProgress();
  const current = state.savedSession ? SCREEN_START : state.session.current_screen;
  const renderers = {
    [SCREEN_START]: renderStartScreen,
    [SCREEN_ATTENTION]: renderAttentionScreen,
    [SCREEN_AUTO_HANDLED]: renderAutoHandledScreen,
    [SCREEN_SAVE]: renderSaveScreen,
    [SCREEN_GENERATE]: renderGenerateScreen,
    [SCREEN_DOWNLOAD]: renderDownloadScreen,
    [SCREEN_COMPLETE]: renderCompleteScreen,
  };
  screen.innerHTML = "";
  screen.appendChild((renderers[current] || renderStartScreen)());
}

function renderStartScreen() {
  const wrapper = div("start-screen");
  if (state.savedSession) {
    wrapper.append(
      kicker("Saved browser session found"),
      heading("DysonX Owner Review Wizard"),
      paragraph("Resume the saved local review or start a clean review. Starting new clears only this browser's saved review state.", "subtitle"),
      buttonRow([
        primaryButton("Resume Saved Review", resumeSavedReview),
        secondaryButton("Start New Review", () => startReview(true)),
      ]),
    );
    return wrapper;
  }
  wrapper.append(
    heading("DysonX Owner Review Wizard", "h1", "wizard-title"),
    paragraph("Review only the few Signals that need Owner attention. The system handles the rest.", "subtitle"),
    safetyList(),
    buttonRow([
      primaryButton("Start Review", () => startReview(false)),
      linkButton("Open Advanced Console", "../dysonx-owner-intelligence-preview/?v=advanced-console"),
    ]),
    paragraph("This will not publish anything.", "status-note"),
  );
  return wrapper;
}

function renderAttentionScreen() {
  const items = attentionSignals();
  const index = Math.min(state.session.attention_index, items.length - 1);
  const signal = items[index];
  if (!signal) {
    state.session.current_screen = SCREEN_AUTO_HANDLED;
    saveSession();
    return renderAutoHandledScreen();
  }
  const wrapper = div("attention-screen");
  wrapper.append(
    kicker(`Review ${index + 1} of ${items.length}`),
    heading(signal.title, "h2"),
    paragraph("Accept the system recommendation, or change the decision if strategic judgment is needed.", "instruction"),
    signalSummary(signal),
  );

  if (state.changeMode) {
    wrapper.append(decisionForm(signal));
    wrapper.append(buttonRow([
      primaryButton("Save decision and continue", () => saveDecisionAndContinue(signal)),
      secondaryButton("Cancel change", () => {
        state.changeMode = false;
        render();
      }),
    ]));
  } else {
    wrapper.append(buttonRow([
      primaryButton("Accept system recommendation", () => acceptAttentionSignal(signal)),
      secondaryButton("Change decision", () => {
        state.changeMode = true;
        render();
      }),
      smallButton("Skip for now", () => skipAttentionSignal(signal)),
    ]));
  }
  wrapper.append(detailsFor(signal));
  return wrapper;
}

function renderAutoHandledScreen() {
  const handled = autoHandledSignals();
  const counts = countAutoHandled(handled);
  const wrapper = div("auto-handled-screen");
  wrapper.append(
    kicker("System-handled Signals"),
    heading(`The system already handled ${handled.length} Signals.`, "h2"),
    paragraph("You do not need to review these unless you disagree.", "instruction"),
    countRow([
      ["Hold", counts.hold],
      ["Regenerate", counts.needs_regeneration],
      ["Reject", counts.auto_reject],
    ]),
    buttonRow([
      primaryButton("Accept system-handled Signals", acceptSystemHandledSignals),
      secondaryButton("Review system-handled details", () => {
        state.showHandledDetails = !state.showHandledDetails;
        render();
      }),
    ]),
  );
  if (state.showHandledDetails) {
    wrapper.append(handledDetails(handled));
  }
  return wrapper;
}

function renderSaveScreen() {
  const overrides = ownerOverrideCount();
  const wrapper = div("save-review-screen");
  wrapper.append(
    kicker("Save internal review"),
    heading("Ready to save your internal review.", "h2"),
    summaryGrid([
      ["Owner attention reviewed", `${attentionDoneCount()} / ${attentionSignals().length}`],
      ["System-handled accepted", state.session.auto_handled_accepted ? String(autoHandledSignals().length) : "0"],
      ["Overrides", String(overrides)],
      ["Publication approval", "No"],
    ]),
    buttonRow([
      primaryButton("Save Internal Review", saveInternalReview),
      secondaryButton("Back", () => {
        state.session.current_screen = SCREEN_AUTO_HANDLED;
        saveSession();
        render();
      }),
    ]),
  );
  return wrapper;
}

function renderGenerateScreen() {
  const wrapper = div("generate-feedback-screen");
  wrapper.append(
    kicker("Generate feedback"),
    heading("Internal review saved.", "h2"),
    paragraph("Now generate Owner Feedback JSON for downstream processing.", "instruction"),
    buttonRow([
      primaryButton("Generate Owner Feedback JSON", generateFeedbackAndContinue),
      secondaryButton("Back", () => {
        state.session.current_screen = SCREEN_SAVE;
        saveSession();
        render();
      }),
    ]),
  );
  return wrapper;
}

function renderDownloadScreen() {
  const wrapper = div("download-outputs-screen");
  wrapper.append(
    kicker("Download outputs"),
    heading("Feedback generated.", "h2"),
    paragraph("These files are internal. No public publishing occurred.", "instruction"),
    buttonRow([
      primaryButton("Download Owner Feedback JSON", () => {
        downloadJson("dysonx_owner_feedback_wizard_v1.json", buildFeedbackJson());
        state.session.feedback_downloaded = true;
        state.session.current_screen = SCREEN_COMPLETE;
        saveSession();
        render();
      }),
      secondaryButton("Download Review Session JSON", () => downloadJson("dysonx_owner_review_wizard_session_v1.json", state.session)),
      secondaryButton("Copy Feedback JSON", copyFeedbackJson),
    ]),
  );
  return wrapper;
}

function renderCompleteScreen() {
  const wrapper = div("complete-screen");
  wrapper.append(
    completionPanel(),
    safetyList(),
    buttonRow([
      primaryButton("Start New Review", () => startReview(true)),
      linkButton("Open Advanced Console", "../dysonx-owner-intelligence-preview/?v=advanced-console"),
    ]),
  );
  return wrapper;
}

function signalSummary(signal) {
  const card = div("signal-card");
  card.append(
    paragraph(signal.why_it_matters || "No why-it-matters field available.", "two-line"),
    metaRow([
      ["System recommendation", signal.decision_label || systemDefaultDecision(signal)],
      ["Score / Tier", `${signal.score ?? signal.quality_score_total} / ${signal.tier || signal.quality_tier}`],
      ["Risk summary", signal.risk_summary || "No risk summary"],
      ["Missing fields", signal.missing_fields?.length ? signal.missing_fields.join(", ") : "None"],
    ]),
  );
  return card;
}

function decisionForm(signal) {
  const id = signal.signal_id;
  const form = div("decision-form");
  form.append(
    field("Owner decision", selectInput("owner-decision", OWNER_DECISIONS, state.session.selected_owner_decisions[id])),
    field("Priority", selectInput("priority", PRIORITIES.map((value) => ({ value, label: value })), state.session.priority_values[id])),
    field("Optional comment", textareaInput("owner-comment", state.session.owner_comments[id] || "")),
    checkboxInput("follow-up-required", "Follow-up required", Boolean(state.session.follow_up_required[id])),
    field("Optional follow-up note", textareaInput("follow-up-note", state.session.follow_up_notes[id] || "")),
  );
  return form;
}

function acceptAttentionSignal(signal) {
  const id = signal.signal_id;
  state.session.selected_owner_decisions[id] = systemDefaultDecision(signal);
  state.session.owner_overridden[id] = false;
  state.session.attention_item_statuses[id] = "accepted";
  state.session.follow_up_required[id] = false;
  advanceAttention();
}

function saveDecisionAndContinue(signal) {
  const id = signal.signal_id;
  const decision = document.getElementById("owner-decision").value;
  state.session.selected_owner_decisions[id] = decision;
  state.session.priority_values[id] = document.getElementById("priority").value;
  state.session.owner_comments[id] = document.getElementById("owner-comment").value;
  state.session.follow_up_required[id] = document.getElementById("follow-up-required").checked;
  state.session.follow_up_notes[id] = document.getElementById("follow-up-note").value;
  state.session.owner_overridden[id] = decision !== systemDefaultDecision(signal);
  state.session.attention_item_statuses[id] = "changed";
  advanceAttention();
}

function skipAttentionSignal(signal) {
  const id = signal.signal_id;
  state.session.selected_owner_decisions[id] = systemDefaultDecision(signal);
  state.session.owner_overridden[id] = false;
  state.session.attention_item_statuses[id] = "skipped";
  state.session.follow_up_required[id] = true;
  state.session.follow_up_notes[id] = state.session.follow_up_notes[id] || "Skipped by Owner for later follow-up.";
  advanceAttention();
}

function advanceAttention() {
  const next = state.session.attention_index + 1;
  state.changeMode = false;
  if (next >= attentionSignals().length) {
    state.session.current_screen = SCREEN_AUTO_HANDLED;
  } else {
    state.session.attention_index = next;
  }
  saveSession();
  render();
}

function acceptSystemHandledSignals() {
  state.session.auto_handled_accepted = true;
  state.session.current_screen = SCREEN_SAVE;
  saveSession();
  render();
}

function saveInternalReview() {
  state.session.internal_review_saved = true;
  state.session.current_screen = SCREEN_GENERATE;
  saveSession();
  render();
}

function generateFeedbackAndContinue() {
  state.session.feedback_generated = true;
  state.session.feedback_json = buildFeedbackJson();
  state.session.current_screen = SCREEN_DOWNLOAD;
  saveSession();
  render();
}

function buildFeedbackJson() {
  const records = allSignals().map((signal) => {
    const id = signal.signal_id;
    const status = state.session.attention_item_statuses[id] || (isAttentionSignal(signal) ? "pending" : "system_handled");
    return {
      signal_id: id,
      title: signal.title,
      auto_decision: signal.auto_decision,
      system_default_owner_decision: systemDefaultDecision(signal),
      selected_owner_decision: state.session.selected_owner_decisions[id] || systemDefaultDecision(signal),
      owner_overridden: Boolean(state.session.owner_overridden[id]),
      owner_review_status: status,
      priority: state.session.priority_values[id] || "medium",
      owner_comment: state.session.owner_comments[id] || "",
      follow_up_required: Boolean(state.session.follow_up_required[id]),
      follow_up_note: state.session.follow_up_notes[id] || "",
      publish_readiness_candidate: Boolean(signal.publish_readiness_candidate),
      publication_approved: false,
    };
  });
  return {
    wizard_session_id: state.session.wizard_session_id,
    owner_review_wizard_version: WIZARD_VERSION,
    created_at: state.session.session_created_at,
    updated_at: new Date().toISOString(),
    source_brief_title: state.brief.overall_recommendation || "DysonX internal intelligence brief",
    internal_review_complete: state.session.feedback_downloaded || state.session.current_screen === SCREEN_COMPLETE,
    auto_handled_accepted: Boolean(state.session.auto_handled_accepted),
    total_signals: allSignals().length,
    owner_attention_reviewed: attentionDoneCount(),
    owner_overridden_count: ownerOverrideCount(),
    records,
    auto_decision_is_not_publication_approval: true,
    owner_feedback_is_not_publication_approval: true,
    review_session_is_not_publication_approval: true,
    wizard_review_is_not_publication_approval: true,
    publication_approved: false,
  };
}

function downloadJson(filename, data) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

async function copyFeedbackJson() {
  const payload = JSON.stringify(buildFeedbackJson(), null, 2);
  await navigator.clipboard.writeText(payload);
}

function countAutoHandled(signals) {
  return signals.reduce((counts, signal) => {
    counts[signal.auto_decision] = (counts[signal.auto_decision] || 0) + 1;
    return counts;
  }, { hold: 0, needs_regeneration: 0, auto_reject: 0 });
}

function attentionDoneCount() {
  return attentionSignals().filter((signal) => state.session.attention_item_statuses[signal.signal_id]).length;
}

function ownerOverrideCount() {
  return Object.values(state.session.owner_overridden || {}).filter(Boolean).length;
}

function safetyList() {
  const list = document.createElement("ul");
  list.className = "safety-list";
  [
    "No public publishing",
    "Not publication approval",
    "No deployment",
    "No OpenAI call",
    "Local browser review only",
  ].forEach((text) => {
    const item = document.createElement("li");
    item.textContent = text;
    list.appendChild(item);
  });
  return list;
}

function completionPanel() {
  const panel = div("completion-panel");
  panel.append(
    heading("Internal Review Complete", "h1"),
    paragraph("No public publishing occurred.", "instruction"),
    generatedList(["Owner Feedback JSON", "Review Session JSON"]),
    paragraph("Next future stage: Publish Readiness Gate V1", "status-note"),
  );
  return panel;
}

function detailsFor(signal) {
  const details = document.createElement("details");
  const summary = document.createElement("summary");
  summary.textContent = "View details";
  const panel = div("details-panel");
  panel.innerHTML = `
    <p><strong>Signal ID:</strong> ${escapeHtml(signal.signal_id)}</p>
    <p><strong>Source:</strong> ${escapeHtml(signal.source_url || "No source URL")}</p>
    <p><strong>Capability:</strong> ${escapeHtml(signal.agi_capability || "Unclear")}</p>
    <p><strong>Entities:</strong> ${escapeHtml((signal.entities || []).join(", "))}</p>
    <p><strong>Watch next:</strong> ${escapeHtml(signal.watch_next || "No watch-next field")}</p>
  `;
  details.append(summary, panel);
  return details;
}

function handledDetails(signals) {
  const wrapper = div("handled-list");
  signals.forEach((signal) => {
    const item = div("handled-item");
    item.innerHTML = `<strong>${escapeHtml(signal.title)}</strong><p>${escapeHtml(signal.decision_label || signal.auto_decision)} · ${escapeHtml(signal.risk_summary || "")}</p>`;
    wrapper.appendChild(item);
  });
  return wrapper;
}

function metaRow(items) {
  const row = div("signal-meta");
  items.forEach(([label, value]) => {
    const item = div("pill");
    item.innerHTML = `<strong>${escapeHtml(label)}</strong>${escapeHtml(String(value))}`;
    row.appendChild(item);
  });
  return row;
}

function summaryGrid(items) {
  const grid = div("summary-grid");
  items.forEach(([label, value]) => {
    const item = div("metric");
    item.innerHTML = `<strong>${escapeHtml(label)}</strong>${escapeHtml(value)}`;
    grid.appendChild(item);
  });
  return grid;
}

function countRow(items) {
  const row = div("handled-counts");
  items.forEach(([label, value]) => {
    const item = div("metric");
    item.innerHTML = `<strong>${escapeHtml(label)}</strong>${escapeHtml(String(value))}`;
    row.appendChild(item);
  });
  return row;
}

function generatedList(items) {
  const list = document.createElement("ul");
  list.className = "generated-list";
  items.forEach((text) => {
    const item = document.createElement("li");
    item.textContent = text;
    list.appendChild(item);
  });
  return list;
}

function buttonRow(buttons) {
  const row = div("button-row");
  buttons.forEach((button) => row.appendChild(button));
  return row;
}

function primaryButton(text, onClick) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "primary-action";
  button.dataset.primaryAction = "true";
  button.textContent = text;
  button.addEventListener("click", onClick);
  return button;
}

function secondaryButton(text, onClick) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "secondary-action";
  button.dataset.secondaryAction = "true";
  button.textContent = text;
  button.addEventListener("click", onClick);
  return button;
}

function smallButton(text, onClick) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "small-action";
  button.dataset.secondaryAction = "true";
  button.textContent = text;
  button.addEventListener("click", onClick);
  return button;
}

function linkButton(text, href) {
  const link = document.createElement("a");
  link.className = "secondary-action";
  link.dataset.secondaryAction = "true";
  link.href = href;
  link.textContent = text;
  return link;
}

function field(label, input) {
  const row = div("form-row");
  const labelEl = document.createElement("label");
  labelEl.textContent = label;
  labelEl.htmlFor = input.id;
  row.append(labelEl, input);
  return row;
}

function selectInput(id, options, value) {
  const select = document.createElement("select");
  select.id = id;
  options.forEach((option) => {
    const item = document.createElement("option");
    item.value = option.value;
    item.textContent = option.label;
    if (option.value === value) item.selected = true;
    select.appendChild(item);
  });
  return select;
}

function textareaInput(id, value) {
  const textarea = document.createElement("textarea");
  textarea.id = id;
  textarea.value = value;
  return textarea;
}

function checkboxInput(id, label, checked) {
  const row = document.createElement("label");
  row.className = "checkbox-row";
  const input = document.createElement("input");
  input.type = "checkbox";
  input.id = id;
  input.checked = checked;
  row.append(input, document.createTextNode(label));
  return row;
}

function heading(text, level = "h2", id = "") {
  const el = document.createElement(level);
  el.textContent = text;
  if (id) el.id = id;
  return el;
}

function kicker(text) {
  return paragraph(text, "screen-kicker");
}

function paragraph(text, className = "") {
  const p = document.createElement("p");
  p.textContent = text;
  if (className) p.className = className;
  return p;
}

function div(className) {
  const el = document.createElement("div");
  if (className) el.className = className;
  return el;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

fetch(FIXTURE_URL)
  .then((response) => response.json())
  .then((brief) => {
    state.brief = brief;
    state.savedSession = readSavedSession();
    state.session = createSession();
    render();
  })
  .catch(() => {
    screen.innerHTML = `<p class="error">Unable to load Owner Review Wizard fixture.</p>`;
  });
