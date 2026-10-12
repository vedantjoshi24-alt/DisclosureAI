"""Deterministic, offline disclosure statement generation for DisclosureAI."""

from __future__ import annotations

from typing import Iterable

ASSISTANCE_OPTIONS = (
    "Brainstorming",
    "Research",
    "Coding",
    "Editing",
    "Summarization",
    "Other",
)

EXTENT_OPTIONS = ("Limited", "Moderate", "Substantial")

EXTENT_SENTENCES = {
    "Limited": (
        "The extent of AI involvement was limited to the supporting tasks "
        "described above."
    ),
    "Moderate": (
        "The extent of AI involvement was moderate across the described tasks."
    ),
    "Substantial": (
        "The extent of AI involvement was substantial for the described tasks."
    ),
}


def clean_text(value: str) -> str:
    """Trim a value and replace all repeated whitespace with one space."""
    return " ".join((value or "").split())


def natural_list(items: Iterable[str]) -> str:
    """Return a short, deterministic English list."""
    values = list(items)
    if len(values) == 1:
        return values[0]
    if len(values) == 2:
        return f"{values[0]} and {values[1]}"
    return f"{', '.join(values[:-1])}, and {values[-1]}"


def resolved_uses(assistance_types: Iterable[str], other_assistance: str = "") -> list[str]:
    """Replace the generic Other option with the student's provided label."""
    other_label = clean_text(other_assistance)
    uses: list[str] = []
    for assistance_type in assistance_types:
        if assistance_type == "Other":
            uses.append(other_label)
        else:
            uses.append(assistance_type.lower())
    return uses


def validate_inputs(
    project_name: str,
    assistance_types: Iterable[str],
    description: str,
    extent: str,
    other_assistance: str = "",
) -> dict[str, str]:
    """Return field-specific validation errors; an empty dictionary means valid."""
    project = clean_text(project_name)
    description_clean = clean_text(description)
    other_clean = clean_text(other_assistance)
    selected_types = list(assistance_types)
    errors: dict[str, str] = {}

    if not 3 <= len(project) <= 100:
        errors["project_name"] = "Enter an assignment or project name between 3 and 100 characters."
    if not selected_types:
        errors["assistance_types"] = "Select at least one type of AI assistance."
    elif any(item not in ASSISTANCE_OPTIONS for item in selected_types):
        errors["assistance_types"] = "Select assistance types from the available options."
    if "Other" in selected_types and not 2 <= len(other_clean) <= 50:
        errors["other_assistance"] = "Describe the other type of assistance in 2 to 50 characters."
    if not 15 <= len(description_clean) <= 600:
        errors["description"] = "Describe what AI helped with in 15 to 600 characters."
    if extent not in EXTENT_OPTIONS:
        errors["extent"] = "Choose the extent of AI involvement."
    return errors


def generate_disclosure(
    project_name: str,
    assistance_types: Iterable[str],
    description: str,
    extent: str,
    other_assistance: str = "",
) -> str:
    """Generate wording only from the student's supplied information.

    Call ``validate_inputs`` first. This function deliberately makes no claims
    about authorship, verification, accuracy, or institutional policy.
    """
    project = clean_text(project_name)
    description_clean = clean_text(description)
    uses = natural_list(resolved_uses(assistance_types, other_assistance))
    extent_sentence = EXTENT_SENTENCES[extent]
    return (
        f"AI Assistance Disclosure — {project}\n\n"
        f"I used AI assistance for {uses}. Specifically, AI helped with: "
        f"{description_clean} {extent_sentence}"
    )
