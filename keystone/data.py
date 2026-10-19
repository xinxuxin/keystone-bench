"""Loading the released files in dist/ as paired items.

The release is plain JSONL in HealthBench's schema; this module only joins the (family, condition)
files on the source id so that each item comes back as one Pair with its original, perturbed and
paraphrase conversations side by side.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

BASE_FAMILIES = ("missing_evidence", "conflicting_evidence", "demographic_shift", "salient_distractor")
# alternative_evidence: the removed fact put back with a value that supports a different action, so that one
# decision is seen in three evidence states (original: A, missing: ask, alternative: B). Released from 0.4.0.
# 0.5.0 hard families: demographic_control (an attribute that must NOT change the advice; negative control),
# buried_red_flag (a casually mentioned red flag; the correct action becomes urgent evaluation),
# missing_evidence_early (the load-bearing fact removed from an earlier turn of a multi-turn conversation)
# 0.7.0 additional family: alternative_evidence_hard (one value the decision rests on moved just across a named clinical
# threshold, so that the correct action changes; scored as a necessary update)
FAMILIES = BASE_FAMILIES + ("alternative_evidence", "demographic_control", "buried_red_flag", "missing_evidence_early",
                            "alternative_evidence_hard")
CONDITIONS = ("original", "perturbed", "paraphrase")
LAYERS = ("primary", "strict", "core", "all", "quick")
SPLITS = ("dev", "test", "all")
EVIDENCE_STATES = ("sufficient_for_original_action", "insufficient_ambiguous", "sufficient_for_alternative_action",
                   "sufficient_for_escalation", "contradiction_unresolved")


def find_dist(path: str | os.PathLike | None = None) -> Path:
    """Locate the release directory: explicit argument, then $KEYSTONE_DIST, then the repository
    layout next to this package, then ./dist."""
    candidates = []
    if path:
        candidates.append(Path(path))
    if os.environ.get("KEYSTONE_DIST"):
        candidates.append(Path(os.environ["KEYSTONE_DIST"]))
    candidates.append(Path(__file__).resolve().parent.parent / "dist")
    candidates.append(Path.cwd() / "dist")
    # where `keystone build` writes when Keystone was installed rather than cloned
    candidates.append(Path(os.environ.get("KEYSTONE_CACHE", Path.home() / ".cache" / "keystone")) / "dist")
    for c in candidates:
        if (c / "MANIFEST.json").exists():
            return c
    raise FileNotFoundError("Keystone release directory not found. Run `keystone build` to rebuild it from HealthBench, "
                            "or pass dist=... or set KEYSTONE_DIST to a directory containing MANIFEST.json")


def load_rows(path: Path) -> list[dict]:
    return [json.loads(l) for l in Path(path).read_text().splitlines() if l.strip()]


@dataclass
class Pair:
    """One source conversation under one perturbation family."""
    id: str
    family: str
    source_id: str
    original: list[dict]
    perturbed: list[dict]
    paraphrase: list[dict] | None
    rubrics: list[dict]
    removed_or_changed: str | None
    expected_safe_behavior: str | None
    materiality_majority: int | None
    in_core: bool
    turns: int
    group: str | None = None
    in_strict: bool = False
    rubric_dependent_criteria: list[int] | None = None
    example_tags: list[str] = field(default_factory=list)
    meta: dict = field(default_factory=dict)
    # decision-evidence layer (0.4.0): what the modified message supports and what a safe reply may do
    evidence_state: str | None = None
    alternative_action: str | None = None
    acceptable_actions: list[str] | None = None
    forbidden_actions: list[dict] | None = None
    decisive_questions: list[str] | None = None
    absent_is_not_negative: str | None = None
    escalation_sufficient: bool | None = None
    frame: dict | None = None            # the decision frame of the ORIGINAL message (per source)
    split: str | None = None             # dev / test, by source
    in_quick: bool = False
    state_consistent: bool | None = None # the annotated state agrees with what the family's edit is designed to do
    acts_as_control: bool = False        # demographic twin whose attribute does not bear on the decision
    in_primary: bool = False             # strict, state-consistent, and the second reviewer did not disagree
    edited_turn: int = -1                # index of the edited turn in the message list; the last user turn unless the family edits an earlier one
    tier: str | None = None              # silver: model-drafted and model-reviewed; gold: clinician-confirmed
    revision: int = 1                    # 2 for a twin rewritten in a later release (the twin it replaced is in deprecated_twins.jsonl)
    # action lists, version 2 (0.7.0): the lists above are the revised ones; the version-1 lists are kept beside them
    lists_version: int | None = None     # 2 where the lists went through the second-vendor review, None for version 1
    acceptable_actions_v1: list[str] | None = None
    forbidden_actions_v1: list[dict] | None = None
    decisive_questions_v1: list[str] | None = None
    # alternative_evidence_hard (0.7.0): the value moved across a named threshold
    hard_mode: str | None = None         # threshold_cross
    hard_outcome: str | None = None      # the outcome the twin is scored on (necessary_update)
    old_value: str | None = None         # the value in the source conversation
    new_value: str | None = None         # the value in the twin
    threshold: str | None = None         # the threshold the change crosses
    threshold_value: float | None = None
    threshold_unit: str | None = None
    threshold_source: str | None = None  # the label or guideline the threshold comes from
    old_side: str | None = None          # what the threshold implies on the source's side of it
    new_side: str | None = None          # ... and on the twin's
    value_kind: str | None = None        # dose, lab_value, vital_sign, weight, gestational_age, duration_time, age, other

    @property
    def has_state(self) -> bool:
        return bool(self.acceptable_actions)

    @property
    def last_user_message(self) -> str:
        return _last_user(self.original)

    @property
    def perturbed_message(self) -> str:
        """The edited turn's text (the last user message unless the twin edits an earlier turn)."""
        if 0 <= self.edited_turn < len(self.perturbed) - 1:
            return self.perturbed[self.edited_turn]["content"]
        return _last_user(self.perturbed)

    @property
    def original_edited_message(self) -> str:
        if 0 <= self.edited_turn < len(self.original) - 1:
            return self.original[self.edited_turn]["content"]
        return _last_user(self.original)

    def conversation(self, condition: str) -> list[dict]:
        if condition == "original":
            return self.original
        if condition == "perturbed":
            return self.perturbed
        if condition == "paraphrase":
            if self.paraphrase is None:
                raise KeyError(f"{self.id} has no released paraphrase control")
            return self.paraphrase
        raise KeyError(condition)


def _last_user(messages: list[dict]) -> str:
    for m in reversed(messages):
        if m["role"] == "user":
            return m["content"]
    return ""


V1_LISTS = ("acceptable_actions_v1", "forbidden_actions_v1", "decisive_questions_v1")
HARD_FIELDS = ("hard_mode", "hard_outcome", "old_value", "new_value", "threshold", "threshold_value", "threshold_unit",
               "threshold_source", "old_side", "new_side", "value_kind")
_V1: dict = {}


def load_v1_lists(dist: str | os.PathLike | None = None) -> dict[tuple[str, str], dict]:
    """The version-1 action lists of the twins whose lists were revised, keyed by (source id, family). They live only in
    the full twin records, so they are read once per release directory; empty before 0.7.0."""
    p = find_dist(dist) / "keystone_twins.jsonl"
    key = (str(p), p.stat().st_mtime_ns if p.exists() else None)
    if key not in _V1:
        out = {}
        if p.exists():
            for line in p.open():
                if '"lists_version": 2' not in line:
                    continue
                t = json.loads(line)
                if t.get("lists_version") == 2:
                    out[(t["prompt_id"], t["family"])] = {k: t.get(k) for k in V1_LISTS}
        _V1.clear()
        _V1[key] = out
    return _V1[key]


def load_frames(dist: str | os.PathLike | None = None) -> dict[str, dict]:
    """Decision frames of the original messages, keyed by source id; empty before 0.4.0."""
    p = find_dist(dist) / "decision_frames.jsonl"
    return {r["prompt_id"]: r["frame"] for r in load_rows(p)} if p.exists() else {}


def load_pairs(family: str, layer: str = "core", dist: str | os.PathLike | None = None,
               limit: int | None = None, require_paraphrase: bool = False, split: str = "all") -> list[Pair]:
    """Pairs for one family. layer='core' keeps twins whose median materiality is 3 (1 for the
    negative control) and that carry no mechanical defect; layer='strict' further requires that the edit
    is tied to the rubric (at least one criterion depends on it; none for the negative control) and that
    the two reviewer models did not both reject the twin; layer='primary' further requires that the annotated
    evidence state agrees with the family's design and that the second reviewer did not disagree with it (the
    layer the headline numbers use from 0.4.0); layer='quick' is the fixed 40-per-family subset of strict twins
    with a control; layer='all' keeps every released twin. split='dev'|'test' selects the
    by-source split. A family absent from the release (older versions) yields an empty list."""
    if family not in FAMILIES:
        raise ValueError(f"family must be one of {FAMILIES}, got {family!r}")
    if layer not in LAYERS:
        raise ValueError(f"layer must be one of {LAYERS}")
    if split not in SPLITS:
        raise ValueError(f"split must be one of {SPLITS}")
    d = find_dist(dist) / "healthbench_style"
    if not (d / f"{family}__perturbed.jsonl").exists():
        return []
    frames = load_frames(dist)
    v1 = load_v1_lists(dist)
    orig = {r["keystone"]["source_prompt_id"]: r for r in load_rows(d / f"{family}__original.jsonl")}
    pert = {r["keystone"]["source_prompt_id"]: r for r in load_rows(d / f"{family}__perturbed.jsonl")}
    pp = d / f"{family}__paraphrase.jsonl"
    para = {r["keystone"]["source_prompt_id"]: r for r in load_rows(pp)} if pp.exists() else {}
    out: list[Pair] = []
    for sid, p in pert.items():
        mv = p["keystone"]
        if layer == "core" and not mv.get("in_core"):
            continue
        if layer == "strict" and not mv.get("in_strict"):
            continue
        if layer == "quick" and not mv.get("in_quick"):
            continue
        if layer == "primary" and not mv.get("in_primary"):
            continue
        if split != "all" and mv.get("split") != split:
            continue
        if require_paraphrase and sid not in para:
            continue
        o = orig[sid]
        out.append(Pair(id=f"{sid}::{family}", family=family, source_id=sid, original=o["prompt"], perturbed=p["prompt"],
                        paraphrase=para[sid]["prompt"] if sid in para else None, rubrics=o["rubrics"],
                        removed_or_changed=mv.get("removed_or_changed"), expected_safe_behavior=mv.get("expected_safe_behavior"),
                        materiality_majority=mv.get("materiality_majority"), in_core=bool(mv.get("in_core")),
                        turns=int(mv.get("turns") or len(o["prompt"])), group=mv.get("group"), example_tags=o["example_tags"], meta=mv,
                        in_strict=bool(mv.get("in_strict")), rubric_dependent_criteria=mv.get("rubric_dependent_criteria"),
                        evidence_state=mv.get("evidence_state"), alternative_action=mv.get("alternative_action"),
                        acceptable_actions=mv.get("acceptable_actions"), forbidden_actions=mv.get("forbidden_actions"),
                        decisive_questions=mv.get("decisive_questions"), absent_is_not_negative=mv.get("absent_is_not_negative"),
                        escalation_sufficient=mv.get("escalation_sufficient"), frame=frames.get(sid),
                        split=mv.get("split"), in_quick=bool(mv.get("in_quick")), tier=mv.get("tier"),
                        state_consistent=mv.get("state_consistent"), acts_as_control=bool(mv.get("acts_as_control")),
                        in_primary=bool(mv.get("in_primary")), edited_turn=mv.get("edited_turn") if isinstance(mv.get("edited_turn"), int) else -1,
                        revision=int(mv.get("revision") or 1), lists_version=mv.get("lists_version"),
                        **v1.get((sid, family), {}), **{k: mv.get(k) for k in HARD_FIELDS}))
        if limit and len(out) >= limit:
            break
    return out


def load_reference(dist: str | os.PathLike | None = None) -> list[dict]:
    """The not-enough-context reference conversations, unchanged HealthBench rows."""
    return load_rows(find_dist(dist) / "healthbench_style" / "reference__natural_missing.jsonl")


def load_manifest(dist: str | os.PathLike | None = None) -> dict:
    return json.loads((find_dist(dist) / "MANIFEST.json").read_text())
