#!/usr/bin/env python3
"""DysonX social draft metadata V1."""

from __future__ import annotations

from dataclasses import dataclass, asdict


DRAFT_ONLY_STATUS = "draft_only"


@dataclass(frozen=True)
class SocialDraftV1:
    platform: str
    draft_text: str
    link_url: str
    status: str

    def __post_init__(self) -> None:
        if self.status != DRAFT_ONLY_STATUS:
            raise ValueError("SocialDraftV1 status must be draft_only")


def build_social_drafts(title: str, summary: str, link_url: str) -> tuple[SocialDraftV1, ...]:
    short_summary = " ".join(summary.split())
    if len(short_summary) > 140:
        short_summary = short_summary[:139].rstrip() + "..."

    return (
        SocialDraftV1(
            platform="x",
            draft_text=f"{title}\n\n{short_summary}\n\n{link_url}",
            link_url=link_url,
            status=DRAFT_ONLY_STATUS,
        ),
        SocialDraftV1(
            platform="linkedin",
            draft_text=f"{title}\n\n{summary}\n\nRead the Signal: {link_url}",
            link_url=link_url,
            status=DRAFT_ONLY_STATUS,
        ),
    )


def serialize_social_draft(draft: SocialDraftV1) -> dict[str, str]:
    return asdict(draft)
