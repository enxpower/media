# Decision Log

## Active Decisions

- Decision: Initial Project Context Pack added.
  Reason: Future AI coding sessions need a reliable project baseline instead of relying on chat history.
  Impact: Future sessions should read `CLAUDE.md` and docs files before making changes.

- Decision: DysonX remains Signal-first, not Article-first.
  Reason: The repository README defines Signal as the operating unit for intelligence value.
  Impact: Future work must not convert this repository into a generic article, blog, news, or RSS system.

- Decision: Monitored sources are managed by Notion.
  Reason: Repository governance states that source configuration belongs in Notion, not permanent hardcoded lists.
  Impact: Future source changes should preserve Notion as the source registry unless explicitly approved.

- Decision: Public publishing remains quality-gated.
  Reason: The public Signals pipeline uses strict safety, attribution, copyright, topic, and raw-body gates.
  Impact: Future automation changes must not weaken public output safeguards.

- Decision: No merge or production deployment occurs without explicit owner approval.
  Reason: Existing `AGENTS.md` and README governance require GitHub-first branch and PR work with no unapproved deployment.
  Impact: AI agents must stop before merge or deployment unless directly instructed.
