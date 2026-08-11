"""Load and validate survey.yaml.

Every other tool reads the instrument through here, so validation is strict:
a config that parses is a config the rest of the repo can trust.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]

PROVIDERS = ("tally", "google-forms", "paper")
CONFIDENCE_TIERS = ("high", "medium", "low")
QUANTIFIERS = (
    "a recurring theme",
    "appears more than once",
    "limited evidence",
    "a single statement",
    "contested across the material",
)


class ConfigError(ValueError):
    """survey.yaml is missing something, or holds something impossible."""


@dataclass(frozen=True)
class Submission:
    provider: str
    form_id: str | None
    form_url: str | None
    field_label: str
    block_header: str


@dataclass(frozen=True)
class Anonymity:
    expected_respondents: int
    min_cell_size: int


@dataclass(frozen=True)
class Survey:
    name: str
    title: str
    audience: str
    duration_minutes: int
    submission: Submission
    anonymity: Anonymity
    questions: tuple[str, ...]
    facets: dict[str, tuple[str, ...]]
    stoplist: tuple[str, ...]

    @property
    def facet_names(self) -> tuple[str, ...]:
        return tuple(self.facets)

    @property
    def statement_keys(self) -> tuple[str, ...]:
        """Every key a statement record may carry."""
        return ("statement", "confidence", *self.facet_names)


def _require(mapping: dict[str, Any], key: str, where: str) -> Any:
    if key not in mapping or mapping[key] is None:
        raise ConfigError(f"{where}: missing required key {key!r}")
    return mapping[key]


def _require_str(mapping: dict[str, Any], key: str, where: str) -> str:
    value = _require(mapping, key, where)
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{where}: {key!r} must be a non-empty string")
    return value


def _require_int(mapping: dict[str, Any], key: str, where: str, minimum: int) -> int:
    value = _require(mapping, key, where)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigError(f"{where}: {key!r} must be an integer")
    if value < minimum:
        raise ConfigError(f"{where}: {key!r} must be at least {minimum}, got {value}")
    return value


def _submission(raw: dict[str, Any]) -> Submission:
    where = "submission"
    if not isinstance(raw, dict):
        raise ConfigError("submission: must be a mapping")
    provider = _require_str(raw, "provider", where)
    if provider not in PROVIDERS:
        raise ConfigError(
            f"submission: provider {provider!r} is not one of {', '.join(PROVIDERS)}"
        )
    return Submission(
        provider=provider,
        form_id=raw.get("form_id"),
        form_url=raw.get("form_url"),
        field_label=_require_str(raw, "field_label", where),
        block_header=_require_str(raw, "block_header", where),
    )


def _anonymity(raw: dict[str, Any]) -> Anonymity:
    where = "anonymity"
    if not isinstance(raw, dict):
        raise ConfigError("anonymity: must be a mapping")
    return Anonymity(
        expected_respondents=_require_int(raw, "expected_respondents", where, 1),
        min_cell_size=_require_int(raw, "min_cell_size", where, 1),
    )


def _questions(raw: Any) -> tuple[str, ...]:
    if not isinstance(raw, list) or not raw:
        raise ConfigError("questions: must be a non-empty list")
    for item in raw:
        if not isinstance(item, str) or not item.strip():
            raise ConfigError(f"questions: {item!r} is not a non-empty string")
    return tuple(raw)


def _facets(raw: Any) -> dict[str, tuple[str, ...]]:
    if not isinstance(raw, dict) or not raw:
        raise ConfigError("facets: must be a non-empty mapping")
    out: dict[str, tuple[str, ...]] = {}
    for name, values in raw.items():
        if not isinstance(values, list) or not values:
            raise ConfigError(f"facets: {name!r} must be a non-empty list")
        for value in values:
            if not isinstance(value, str) or not value.strip():
                raise ConfigError(f"facets: {name!r} holds {value!r}, not a string")
        if "unspecified" not in values:
            raise ConfigError(
                f"facets: {name!r} must include 'unspecified' so an ambiguous "
                "statement is never resolved by guessing"
            )
        out[str(name)] = tuple(values)
    return out


def _stoplist(raw: Any) -> tuple[str, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise ConfigError("stoplist: must be a list of strings, or absent")
    for item in raw:
        if not isinstance(item, str) or not item.strip():
            raise ConfigError(f"stoplist: {item!r} is not a non-empty string")
    return tuple(raw)


def load_survey(path: Path | None = None) -> Survey:
    path = path or ROOT / "survey.yaml"
    if not path.exists():
        raise ConfigError(f"no survey config at {path}")
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ConfigError(f"{path}: expected a mapping at the top level")
    where = str(path)
    return Survey(
        name=_require_str(raw, "name", where),
        title=_require_str(raw, "title", where),
        audience=_require_str(raw, "audience", where),
        duration_minutes=_require_int(raw, "duration_minutes", where, 1),
        submission=_submission(_require(raw, "submission", where)),
        anonymity=_anonymity(_require(raw, "anonymity", where)),
        questions=_questions(_require(raw, "questions", where)),
        facets=_facets(_require(raw, "facets", where)),
        stoplist=_stoplist(raw.get("stoplist")),
    )
