# DysonX Signal Quality Framework V1

## 1. Status

This is a documentation-only framework created after the V1 OpenAI orchestrator smoke milestone.

It defines quality standards for DysonX Signals only. It does not implement scoring, auditing, confidence calibration, multi-source correlation, human approval, publish readiness, publishing, Knowledge Graph writes, Prediction Engine work, workflow changes, OpenAI calls, or deployment.

## 2. Why This Framework Exists

DysonX has proven that the Intelligence Core MVP pipeline can run from source store through collector, RawItem, SignalCandidate, OpenAI IntelligenceSignal, ranking, QualityReview, PublishPackage metadata, and final audit report.

The next risk is intelligence quality drift. Once the system can generate IntelligenceSignals, the critical question becomes:

What makes a Signal valuable enough to preserve, rank, review, reuse, and eventually publish?

Engineering must not move from "pipeline works" to "publish pages" without first defining quality. This framework establishes the standard that future audit, scoring, confidence, correlation, approval, and publish-readiness layers should enforce.

## 3. Signal Is the Intelligence Core

Signal is the primary object in DysonX, not Article.

PublishPackage is only a downstream consumer of Signal intelligence. It must not become the product core.

A Signal is valuable only if it strengthens one or more of:

- AGI capability tracking
- company trackers
- person trackers
- model trackers
- research trackers
- policy trackers
- source authority memory
- knowledge graph
- reports
- prediction and future review workflows
- decision usefulness

## 4. Required Signal Questions

Every DysonX Signal must answer:

- What happened?
- What is the original source?
- How authoritative is the source?
- Why does it matter?
- What changed compared with prior context?
- Which AGI capability does it affect?
- Which companies, people, models, papers, projects, policies, or entities are involved?
- What should be watched next?
- What uncertainty remains?

High-quality Signals should also answer:

- Does this reveal a trend, trajectory, or inflection point?
- Does it connect to prior Signals?
- Does it strengthen a tracker or future Knowledge Graph edge?
- Does it create a future verification point?
- Does it help a decision-maker decide what to monitor or do next?

## 5. Low-Quality Signal Definition

Low-quality Signals are outputs that are mainly:

- news repetition
- generic summaries
- fact restatement without interpretation
- weak or missing source attribution
- weak source authority reasoning
- weak AGI capability mapping
- no causal reasoning
- no entity or relationship value
- no tracker value
- no Watch Next value
- no decision value
- no future review value
- SEO-style content
- article-like prose instead of structured intelligence
- unsupported claims
- overconfident conclusions
- duplicate Signals without new value

Low-quality Signals should be blocked from publish readiness and should not be reused as authoritative intelligence.

## 6. High-Quality Signal Definition

High-quality Signals provide:

- information density
- source authority clarity
- reasoning depth
- AGI capability relevance
- novelty
- causal or strategic interpretation
- entity and relationship value
- trend or trajectory insight
- tracker reuse value
- decision usefulness
- specific Watch Next guidance
- uncertainty labeling
- future verification or prediction value
- reusable knowledge graph value

A high-quality Signal should make the reader understand not only what happened, but why it changes the map of AI / AGI capability, company direction, research trajectory, policy posture, or future monitoring priorities.

## 7. Signal Quality Dimensions V1

Each dimension uses a suggested score range of 0-5, where 0 means absent or harmful and 5 means strong, specific, and reusable.

### Information Density

Definition: The amount of relevant intelligence value carried per unit of output.

What good looks like: The Signal is compact, specific, and rich in useful context, not padded with generic explanation.

What bad looks like: The Signal is verbose, repetitive, or mostly obvious background.

Suggested score range: 0-5.

### Source Attribution

Definition: The clarity and traceability of the original source behind the Signal.

What good looks like: The Signal includes a precise original source URL and makes clear what evidence came from that source.

What bad looks like: The Signal cites vague sources, lacks attribution, or blurs original and secondhand evidence.

Suggested score range: 0-5.

### Source Authority

Definition: The strength and relevance of the source for the claim being made.

What good looks like: The Signal explains whether the source is first-party, official, technical, regulatory, research-grade, or otherwise authoritative.

What bad looks like: The Signal treats weak, promotional, secondhand, or unsourced material as equally authoritative.

Suggested score range: 0-5.

### Reasoning Depth

Definition: The quality of interpretation connecting facts to implications.

What good looks like: The Signal explains cause, consequence, tradeoff, or strategic meaning with evidence-aware reasoning.

What bad looks like: The Signal only restates facts or makes unsupported conclusions.

Suggested score range: 0-5.

### Novelty

Definition: The degree to which the Signal adds new information, interpretation, or relationship value.

What good looks like: The Signal identifies a new event, new evidence, new connection, or meaningful change from prior context.

What bad looks like: The Signal duplicates existing coverage without adding value.

Suggested score range: 0-5.

### AGI Capability Relevance

Definition: The strength of the Signal's connection to one or more AGI capability areas.

What good looks like: The Signal maps clearly to capabilities such as reasoning, planning, memory, world models, agents, robotics, multimodal systems, tool use, safety, compute, infrastructure, evaluation, or alignment.

What bad looks like: The Signal uses broad AI language without explaining AGI capability impact.

Suggested score range: 0-5.

### Entity / Relationship Value

Definition: The usefulness of the Signal for identifying entities and relationships.

What good looks like: The Signal names relevant companies, people, models, papers, projects, policies, products, or organizations and explains meaningful relationships between them.

What bad looks like: The Signal has no durable entity value or lists names without explaining relationships.

Suggested score range: 0-5.

### Tracker Reuse Value

Definition: The degree to which the Signal can strengthen a company, person, model, research, policy, capability, or source tracker.

What good looks like: The Signal would update a tracker with a meaningful state change, pattern, milestone, or evidence point.

What bad looks like: The Signal is too generic or temporary to improve any tracker.

Suggested score range: 0-5.

### Actionability

Definition: The degree to which the Signal helps a decision-maker decide what to monitor, compare, investigate, or do next.

What good looks like: The Signal supports concrete monitoring, evaluation, investment, research, product, policy, or strategy decisions.

What bad looks like: The Signal is interesting but does not change any decision or monitoring priority.

Suggested score range: 0-5.

### Watch Next Specificity

Definition: The specificity and usefulness of the Signal's forward-looking monitoring guidance.

What good looks like: Watch Next identifies concrete future evidence, milestones, sources, releases, benchmarks, regulatory actions, or company moves to monitor.

What bad looks like: Watch Next is generic, obvious, or absent.

Suggested score range: 0-5.

### Prediction / Future Review Value

Definition: The degree to which the Signal creates a future verification point or supports prediction review.

What good looks like: The Signal captures claims, milestones, dates, commitments, risks, or implied trajectories that can later be checked.

What bad looks like: The Signal cannot support future review because it has no testable claim or durable implication.

Suggested score range: 0-5.

### Confidence Support

Definition: The evidence basis behind the Signal's confidence level.

What good looks like: Confidence is grounded in source authority, evidence completeness, claim specificity, cross-source support, and explicit uncertainty.

What bad looks like: Confidence reflects model tone or unsupported certainty.

Suggested score range: 0-5.

### Anti-Garbage Risk

Definition: The risk that the Signal is generic, duplicated, unsupported, SEO-like, article-like, or otherwise low-value.

What good looks like: The Signal has low anti-garbage risk because it is specific, attributed, structured, decision-useful, and evidence-aware.

What bad looks like: The Signal reads like a rewritten article, generic AI summary, or SEO content.

Suggested score range: 0-5, where 0 means severe garbage risk and 5 means minimal garbage risk.

## 8. Quality Tier Definitions

### Tier A: Decision-grade Signal

Tier A Signals have:

- strong source
- high information density
- clear AGI capability impact
- strong reasoning
- strong tracker, graph, or report reuse value
- specific Watch Next
- explicit uncertainty
- future review value

Tier A is the target quality level for future publish-ready Signals.

### Tier B: Useful Signal

Tier B Signals are valid and useful. They have a good source and some reasoning and AGI relevance, but may need stronger correlation, confidence support, or human review before publication.

Explicitly approved Tier B Signals may become publish-ready in future workflows, but only when the approval is recorded.

### Tier C: Needs Review

Tier C Signals are potentially relevant but have thin reasoning, weak attribution, weak novelty, unclear AGI relevance, or insufficient confidence support.

Tier C should not be publish-ready without human review or improved analysis.

### Tier D: Reject / Low-value

Tier D Signals are generic, duplicated, unsupported, article-like, SEO-like, based on weak sources, or lacking decision value.

Tier D should not become publish-ready.

Only Tier A or explicitly approved Tier B should ever become publish-ready in future publishing workflows.

## 9. Confidence Calibration Principle

Confidence must not mean model self-confidence only.

Future confidence calibration must consider:

- model confidence
- source authority
- evidence completeness
- claim specificity
- cross-source support
- contradiction risk
- uncertainty labeling
- freshness / source age
- whether the Signal is first-source or secondhand
- whether claims are directly supported or inferred

This PR does not implement calibration code.

## 10. Relationship to Existing Pipeline

This framework sits conceptually in the V1 pipeline as:

`Source store -> Collector -> RawItem -> SignalCandidate -> OpenAI IntelligenceSignal -> Signal Quality Framework -> Ranking -> QualityReview -> PublishPackage metadata -> Final audit report`

This framework does not replace Ranking.

It does not replace QualityReview.

It defines the quality standard that future audit, scoring, ranking, review, approval, and publish-readiness layers should enforce.

PublishPackage remains downstream metadata and must not become the product core. Signal quality is the intelligence core.

## 11. Recommended Next PRs

Recommended next PRs after this framework:

1. docs/audit: define OpenAI Output Quality Audit V1
2. feat/audit: add OpenAI output quality audit script
3. feat: add SignalQualityScore V1
4. feat: add Confidence Calibration V1
5. feat: add Multi-source Correlation V1
6. feat: add Human Approval Gate V1
7. feat: add Publish Readiness Gate V1

Publishing should come only after these layers are stable, reviewed, and governed.

## 12. Explicit Non-Goals

This PR does not:

- implement scoring code
- implement audit code
- modify existing pipeline code
- change workflows
- dispatch workflows
- call OpenAI
- add scheduled automation
- publish content
- generate website pages
- add social posting
- write Knowledge Graph records
- implement Prediction Engine
- modify Notion
- use live GitHub API
- scrape article bodies
- change deployment
- merge

No production deployment is authorized by this framework.
