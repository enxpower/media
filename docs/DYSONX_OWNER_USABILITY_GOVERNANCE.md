# DysonX Owner Usability Governance

## 1. Purpose

DysonX must not confuse engineering functionality with product usability.

Engineering checks prove that code runs.

Owner usability checks prove that the product is useful.

Both are required for Owner-facing changes. A page can pass tests and still fail if the Owner cannot quickly understand what matters, compare Signals, make a decision, and give feedback without reading raw JSON or debug-style fields.

## 2. Core Rule

Every Owner-facing PR must answer:

```text
Can the Owner understand, compare, decide, and give feedback within 10 seconds per Signal?
```

If not, the PR is not product-ready even if tests pass.

## 3. Current Strategic Priority

The current strategic priority is:

```text
SignalQualityScore
-> Internal Intelligence Brief
-> Owner Review
-> Owner Feedback
-> Usable Internal Frontend
```

Until the internal frontend is usable, DysonX must not prioritize complex backend intelligence layers over the Owner-facing product loop.

## 4. Big-Step Rule

Bigger PRs are allowed when they move the Owner-facing product forward.

Every bigger PR must include a stricter review phase:

- Big product PR
- Engineering validation
- Owner usability review
- Narrow fix for blocking usability gaps
- Final review
- Merge only if clean

A big PR must not be followed by more broad changes before its usability gaps are fixed.

## 5. Narrow-Fix Rule

When review finds a blocking usability issue, the fix must be narrow.

Examples:

- Add missing score to review cards.
- Improve field label clarity.
- Move raw metadata out of the primary view.
- Fix broken feedback JSON generation.

Non-examples:

- Add persistence while fixing score display.
- Add deployment while fixing field layout.
- Add confidence calibration while fixing UI usability.

## 6. Engineering Checklist

Every PR must still pass:

- constitution guard
- architecture guard
- release guard
- `py_compile` where relevant
- full tests
- `git diff --check`
- no workflow dispatch unless explicitly authorized
- no OpenAI call unless explicitly authorized
- no deployment unless explicitly authorized
- no production secret changes
- no unrelated broad refactor

## 7. Owner Usability Checklist

Every Owner-facing PR must verify that the Owner can answer:

1. What is the top Signal?
2. Why does it matter?
3. What source proves it?
4. What is the score?
5. What is the tier?
6. What is the risk?
7. What is missing?
8. What should I watch next?
9. What decision should I make?
10. Can I give feedback without reading raw JSON?

## 8. Required Signal Card Fields

Every Owner review card must show:

- title
- score
- tier
- source URL
- source authority, if available
- AGI capability affected
- why it matters
- watch next
- risk summary
- missing fields
- recommended action
- owner decision controls

If any of these are missing, the PR must explain why.

## 9. Raw Data Display Rule

Raw technical fields must not dominate the Owner-facing first screen.

Examples of fields that should not be primary:

- `brief_version`
- `generated_for`
- raw `tier_counts` JSON
- `source_score_report` internal path
- internal fixture path
- raw object dumps

These may appear only in secondary or technical details sections.

## 10. Product Usability Failure Examples

Examples of failure:

- Page renders but looks like a debug page.
- Tier counts appear as raw JSON.
- Review queue lacks score.
- Owner cannot tell what to review first.
- Owner must read raw fields to understand the Signal.
- Feedback export exists but is unclear.
- Page says "internal" but looks like public publishing.
- Owner cannot compare two Signals quickly.

## 11. Merge Rule For Owner-Facing PRs

Owner-facing PRs may be merged only when:

- engineering checks pass
- governance posture is preserved
- Owner usability checklist passes
- no blocking usability finding remains
- any required fix has been applied narrowly
- final review confirms clean status

## 12. Prompt Requirement

All future Codex prompts for DysonX Owner-facing work must include this document in the mandatory reading list:

```text
docs/DYSONX_OWNER_USABILITY_GOVERNANCE.md
```

All future prompts must also include the Strategic Priority -- Minimal Usable Owner Intelligence Loop block until the internal frontend is usable and launched.

## 13. Explicit Non-Goals

This governance does not authorize:

- public publishing
- website generation for public Signals
- social distribution
- Knowledge Graph writes
- Prediction Engine
- complex Confidence Calibration
- complex Multi-source Correlation
- deployment automation
- workflow dispatch
- OpenAI calls
- production deployment

No production deployment is authorized by this governance document.
