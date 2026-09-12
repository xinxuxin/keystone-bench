"""Run a model and a judge over pairs, provider-agnostic.

`respond` and `judge` are callables `messages -> str`. OpenAICompatible covers OpenRouter, OpenAI and
any OpenAI-compatible endpoint (vLLM, Ollama, LM Studio) with disk caching and retries; anything else
is a one-line wrapper by the caller. Replies are generated at temperature 0 with no system prompt and
1,500 output tokens by default, the HealthBench settings.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from .data import Pair
from .metrics import healthbench_score, summarize, primary_outcome
from .prompts import action_prompt, applicability_prompt, behavior_prompt, grader_prompt, parse_json

Complete = Callable[[list[dict]], str]

PROVIDERS = {
    "openrouter": ("https://openrouter.ai/api/v1", "OPENROUTER_API_KEY"),
    "openai": ("https://api.openai.com/v1", "OPENAI_API_KEY"),
    "ollama": ("http://localhost:11434/v1", None),
}


class OpenAICompatible:
    """Chat completions against any OpenAI-compatible endpoint.

    model: 'openrouter/<vendor>/<model>', 'openai/<model>', 'ollama/<model>', or a bare model id with base_url.
    Caches every completion on disk (default ~/.cache/keystone) keyed by model, messages and sampling
    parameters, so re-runs and crashes cost nothing. Tracks tokens and, for OpenRouter, dollars in .usage.
    """

    def __init__(self, model: str, base_url: str | None = None, api_key: str | None = None, temperature: float = 0.0,
                 max_tokens: int = 1500, timeout: float = 180.0, retries: int = 5, cache_dir: str | os.PathLike | None = None,
                 extra_headers: dict | None = None, extra_body: dict | None = None, repeat: int = 0):
        provider, _, rest = model.partition("/")
        if provider in PROVIDERS and rest:
            default_url, key_env = PROVIDERS[provider]
            self.model_id = rest
            self.base_url = (base_url or default_url).rstrip("/")
            self.api_key = api_key or (os.environ.get(key_env, "") if key_env else "")
            if key_env and not self.api_key:
                raise RuntimeError(f"{model}: set {key_env} or pass api_key=")
        else:
            self.model_id = model
            self.base_url = (base_url or os.environ.get("OPENAI_BASE_URL", "")).rstrip("/")
            if not self.base_url:
                raise RuntimeError(f"{model!r}: pass base_url= or set OPENAI_BASE_URL (or prefix the model with openrouter/, openai/, ollama/)")
            self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.name = model
        self.temperature, self.max_tokens, self.timeout, self.retries = temperature, max_tokens, timeout, retries
        self.cache_dir = Path(cache_dir) if cache_dir else Path(os.environ.get("KEYSTONE_CACHE", Path.home() / ".cache" / "keystone"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.extra_headers, self.extra_body = extra_headers or {}, extra_body or {}
        self.repeat = repeat   # cache-key only: re-asks the identical request, measuring the server's own nondeterminism
        self.usage = {"calls": 0, "cached": 0, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0}
        self._lock = threading.Lock()

    def _cache_path(self, messages: list[dict], max_tokens: int | None = None) -> Path:
        key = json.dumps({"m": self.model_id, "u": self.base_url, "msgs": messages, "t": self.temperature, "n": max_tokens or self.max_tokens,
                          "x": self.extra_body, **({"r": self.repeat} if self.repeat else {})}, sort_keys=True)
        return self.cache_dir / (hashlib.sha256(key.encode()).hexdigest() + ".json")

    def __call__(self, messages: list[dict], max_tokens: int | None = None) -> str:
        import httpx  # local import keeps `import keystone` dependency-free for offline analysis
        max_tokens = max_tokens or self.max_tokens
        cp = self._cache_path(messages, max_tokens)
        if cp.exists():
            try:
                d = json.loads(cp.read_text())
                with self._lock:
                    self.usage["calls"] += 1; self.usage["cached"] += 1
                return d["text"]
            except (json.JSONDecodeError, KeyError):
                cp.unlink(missing_ok=True)
        headers = {"content-type": "application/json", **self.extra_headers}
        if self.api_key:
            headers["authorization"] = f"Bearer {self.api_key}"
        body = {"model": self.model_id, "messages": messages, "temperature": self.temperature, "max_tokens": max_tokens, **self.extra_body}
        if "openrouter.ai" in self.base_url:
            body.setdefault("usage", {"include": True})
            headers.setdefault("X-Title", "keystone")
        last: Exception | None = None
        for attempt in range(self.retries):
            try:
                r = httpx.post(f"{self.base_url}/chat/completions", headers=headers, json=body, timeout=self.timeout)
                if r.status_code == 429 or r.status_code >= 500:
                    raise RuntimeError(f"HTTP {r.status_code}: {r.text[:200]}")
                r.raise_for_status()
                j = r.json()
                text = (j["choices"][0]["message"].get("content") or "")
                u = j.get("usage") or {}
                with self._lock:
                    self.usage["calls"] += 1
                    self.usage["input_tokens"] += u.get("prompt_tokens") or 0
                    self.usage["output_tokens"] += u.get("completion_tokens") or 0
                    self.usage["cost_usd"] += float(u.get("cost") or 0.0)
                tmp = cp.with_suffix(f".{os.getpid()}.{threading.get_ident()}.tmp")
                tmp.write_text(json.dumps({"text": text, "usage": u, "model": j.get("model", self.model_id)}, ensure_ascii=False))
                os.replace(tmp, cp)
                return text
            except Exception as e:  # noqa: BLE001 - retry any transport or server error, then surface the last one
                last = e
                time.sleep(min(2 ** attempt, 30))
        raise RuntimeError(f"{self.name}: {self.retries} attempts failed: {last}")



CLI_TOOLS = {   # subscription command-line assistants, used through the login the user already has
    "cli-claude": "claude",
    "cli-codex": "codex",
}


class SubscriptionCLI:
    """A coding-assistant CLI (`claude`, `codex`) driven as a one-shot completion endpoint.

    model: 'cli-codex/gpt-5.6-sol', 'cli-claude/sonnet', or either with 'default' for the CLI's own default.
    This runs on the subscription the user is already logged into, so it costs no API credit; `.usage`
    records tokens and, where the CLI reports one, a reference price that is NOT charged. Same interface,
    cache and retry behaviour as OpenAICompatible, so either can be passed as the model or the judge.

    Throughput is a process launch per call, so keep `workers` modest; the CLIs are also rate limited by
    the subscription, and a shared login is shared with whatever else is using it.
    """

    def __init__(self, model: str, temperature: float = 0.0, max_tokens: int = 1500, timeout: float = 300.0,
                 retries: int = 3, cache_dir: str | os.PathLike | None = None, repeat: int = 0):
        tool, _, name = model.partition("/")
        if tool not in CLI_TOOLS or not name:
            raise ValueError(f"expected cli-claude/<model> or cli-codex/<model>, got {model!r}")
        self.tool, self.model_name, self.model_id, self.name = tool, name, model, model
        self.temperature, self.max_tokens, self.timeout, self.retries, self.repeat = temperature, max_tokens, timeout, retries, repeat
        self.cache_dir = Path(cache_dir) if cache_dir else Path(os.environ.get("KEYSTONE_CACHE", Path.home() / ".cache" / "keystone"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.usage = {"calls": 0, "cached": 0, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0, "reference_cost_usd": 0.0}
        self._lock = threading.Lock()
        if not shutil.which(CLI_TOOLS[tool]):
            raise RuntimeError(f"{CLI_TOOLS[tool]} is not on PATH; install it or use an API model")

    def _cache_path(self, messages: list[dict], max_tokens: int | None = None) -> Path:
        key = json.dumps({"m": self.model_id, "u": "cli", "msgs": messages, "t": self.temperature, "n": max_tokens or self.max_tokens,
                          **({"r": self.repeat} if self.repeat else {})}, sort_keys=True)
        return self.cache_dir / (hashlib.sha256(key.encode()).hexdigest() + ".json")

    @staticmethod
    def _flatten(messages: list[dict]) -> tuple[str, str | None]:
        """(prompt, system). A CLI takes one block of text, so a conversation is written out as a transcript."""
        system = "\n\n".join(m["content"] for m in messages if m["role"] == "system") or None
        rest = [m for m in messages if m["role"] != "system"]
        if len(rest) == 1 and rest[0]["role"] == "user":
            return rest[0]["content"], system
        return "\n\n".join(f"[{m['role']}]\n{m['content']}" for m in rest) + "\n\n[assistant]", system

    def _claude(self, prompt: str, system: str | None) -> tuple[str, dict]:
        cmd = ["claude", "-p", "--tools", "", "--no-session-persistence", "--max-turns", "1", "--output-format", "json",
               "--system-prompt", system or "You are a helpful assistant. Answer the user directly."]
        if self.model_name != "default":
            cmd += ["--model", self.model_name]
        with tempfile.TemporaryDirectory() as cwd:   # a scratch cwd keeps the repository's CLAUDE.md out of the prompt
            r = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=self.timeout, cwd=cwd)
        try:
            j = json.loads(r.stdout.strip().splitlines()[-1])
        except (json.JSONDecodeError, IndexError):
            raise RuntimeError(f"claude exited {r.returncode} without JSON: {(r.stderr or r.stdout)[:200]}")
        if j.get("is_error"):
            raise RuntimeError(f"claude: {str(j.get('result'))[:200]}")
        u = j.get("usage") or {}
        return j.get("result") or "", {"input_tokens": u.get("input_tokens") or 0, "output_tokens": u.get("output_tokens") or 0,
                                       "reference_cost_usd": float(j.get("total_cost_usd") or 0.0)}

    def _codex(self, prompt: str, system: str | None) -> tuple[str, dict]:
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as tf:
            out_path = tf.name
        cmd = ["codex", "exec", "--skip-git-repo-check", "--ephemeral", "--json", "-s", "read-only", "-o", out_path]
        if self.model_name != "default":
            cmd += ["-m", self.model_name]
        cmd.append("-")
        text_in = f"[Instructions]\n{system}\n\n{prompt}" if system else prompt
        try:
            with tempfile.TemporaryDirectory() as cwd:
                r = subprocess.run(cmd, input=text_in, capture_output=True, text=True, timeout=self.timeout, cwd=cwd)
            text = Path(out_path).read_text() if Path(out_path).exists() else ""
        finally:
            Path(out_path).unlink(missing_ok=True)
        usage = {"input_tokens": 0, "output_tokens": 0, "reference_cost_usd": 0.0}
        for line in r.stdout.splitlines():
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            if ev.get("type") == "turn.completed" and isinstance(ev.get("usage"), dict):
                usage["input_tokens"] = ev["usage"].get("input_tokens") or 0
                usage["output_tokens"] = ev["usage"].get("output_tokens") or 0
        if not text.strip():
            raise RuntimeError(f"codex exited {r.returncode} with no output: {((r.stderr or '') + r.stdout)[-200:]}")
        return text.strip(), usage

    def __call__(self, messages: list[dict], max_tokens: int | None = None) -> str:
        max_tokens = max_tokens or self.max_tokens
        cp = self._cache_path(messages, max_tokens)
        if cp.exists():
            try:
                d = json.loads(cp.read_text())
                with self._lock:
                    self.usage["calls"] += 1; self.usage["cached"] += 1
                return d["text"]
            except (json.JSONDecodeError, KeyError):
                cp.unlink(missing_ok=True)
        prompt, system = self._flatten(messages)
        last: Exception | None = None
        for attempt in range(self.retries):
            try:
                text, u = self._claude(prompt, system) if self.tool == "cli-claude" else self._codex(prompt, system)
                with self._lock:
                    self.usage["calls"] += 1
                    self.usage["input_tokens"] += u["input_tokens"]; self.usage["output_tokens"] += u["output_tokens"]
                    self.usage["reference_cost_usd"] += u["reference_cost_usd"]   # what an API call would have cost; not charged
                tmp = cp.with_suffix(f".{os.getpid()}.{threading.get_ident()}.tmp")
                tmp.write_text(json.dumps({"text": text, "usage": u, "model": self.model_id}, ensure_ascii=False))
                os.replace(tmp, cp)
                return text
            except Exception as e:  # noqa: BLE001 - a CLI fails for transient reasons too (rate limit, restart)
                last = e
                time.sleep(min(5 * 2 ** attempt, 60))
        raise RuntimeError(f"{self.name}: {self.retries} attempts failed: {last}")


def make_client(model: str, **kw):
    """SubscriptionCLI for a 'cli-*' model id, OpenAICompatible otherwise. Unknown keywords are dropped for the CLI."""
    if model.partition("/")[0] in CLI_TOOLS:
        keep = {k: v for k, v in kw.items() if k in ("temperature", "max_tokens", "timeout", "retries", "cache_dir", "repeat")}
        return SubscriptionCLI(model, **keep)
    return OpenAICompatible(model, **kw)


def _judge_json(judge: Complete, prompt: str, factor: int = 3) -> dict:
    """Parse the judge's JSON object; when parsing fails (in practice a truncated answer) ask once more with
    `factor` times the output budget. The retry is a separate cache entry, so cached first answers stay free.
    Verbose judges (Claude, Gemini) lost 15 to 35 percent of their verdicts at the 600-token default without this."""
    msgs = [{"role": "user", "content": prompt}]
    out = parse_json(judge(msgs))
    if out is None and getattr(judge, "max_tokens", None):
        try:
            out = parse_json(judge(msgs, max_tokens=int(judge.max_tokens) * factor))
        except TypeError:  # a plain callable judge without an output budget
            out = None
    return out or {}


judge_json = _judge_json


def action_spec(pair: Pair, condition: str) -> dict | None:
    """What the reply to `condition` is judged against: the twin's evidence state for 'perturbed', the
    decision frame of the original for 'original' and 'paraphrase'. None when the release has neither."""
    fr = pair.frame or {}
    if condition == "perturbed":
        if not pair.has_state:
            return None
        return {"decision_target": fr.get("decision_target"), "evidence_state": pair.evidence_state,
                "acceptable_actions": pair.acceptable_actions, "forbidden_actions": pair.forbidden_actions,
                "decisive_questions": pair.decisive_questions, "escalation_sufficient": pair.escalation_sufficient}
    if not fr.get("acceptable_actions"):
        return None
    return {"decision_target": fr.get("decision_target"), "evidence_state": "sufficient_for_original_action",
            "acceptable_actions": fr.get("acceptable_actions"), "forbidden_actions": fr.get("forbidden_actions"),
            "decisive_questions": fr.get("decisive_questions_original"), "escalation_sufficient": fr.get("escalation_sufficient")}


def evaluate_pair(pair: Pair, respond: Complete, judge: Complete, rubric: bool = False, conditions: tuple[str, ...] | None = None,
                  action: bool = True) -> dict:
    """Replies, behaviour classifications, action judgements against the decision-evidence annotation
    (when the release carries it) and optional rubric grades for one pair."""
    conds = list(conditions or ("original", "perturbed", "paraphrase"))
    if pair.paraphrase is None and "paraphrase" in conds:
        conds.remove("paraphrase")
    replies = {c: respond(pair.conversation(c)) for c in conds}
    behavior = {}
    for c, reply in replies.items():
        if not (reply or "").strip():  # empty output is missing data, never a stance (protocol section 5.5)
            behavior[c] = {"stance": None, "empty_reply": True, "explanation": "empty model output; not classified"}
            continue
        missing = pair.removed_or_changed if c == "perturbed" else None
        behavior[c] = _judge_json(judge, behavior_prompt(pair.conversation(c), reply, missing))
    rec = {"id": pair.id, "family": pair.family, "source_id": pair.source_id, "materiality_majority": pair.materiality_majority,
           "in_core": pair.in_core, "turns": pair.turns, "group": pair.group, "split": pair.split, "tier": pair.tier,
           "evidence_state": pair.evidence_state, "escalation_sufficient": pair.escalation_sufficient,
           "replies": replies, "behavior": behavior}
    if action:
        acts = {}
        for c, reply in replies.items():
            spec = action_spec(pair, c)
            if spec is None or not (reply or "").strip():
                continue
            acts[c] = _judge_json(judge, action_prompt(pair.conversation(c), reply, spec))
        if acts:
            rec["action"] = acts
    if rubric:
        grades: dict = {}
        for c in ("original", "perturbed"):
            if c not in replies:
                continue
            met = []
            for r in pair.rubrics:
                j = _judge_json(judge, grader_prompt(pair.conversation(c), replies[c], r["criterion"]))
                met.append(j.get("criteria_met") if isinstance(j.get("criteria_met"), bool) else None)
            grades[f"met_{c}"] = met
        applicable = []
        if "perturbed" in replies:
            for r in pair.rubrics:
                j = _judge_json(judge, applicability_prompt(pair.original_edited_message, pair.perturbed_message, r["criterion"],
                                                            context=pair.conversation("original")[:-1] or None))
                applicable.append(j.get("applicable") if isinstance(j.get("applicable"), bool) else None)
        grades["applicable"] = applicable
        keep = [(r, m) for r, m, a in zip(pair.rubrics, grades.get("met_perturbed", []), applicable) if a is not False]
        rec["rubric"] = {"score_original": healthbench_score(pair.rubrics, grades.get("met_original", [])) if "met_original" in grades else None,
                         "score_perturbed_stale": healthbench_score(pair.rubrics, grades.get("met_perturbed", [])) if "met_perturbed" in grades else None,
                         "score_perturbed_applicable": healthbench_score([r for r, _ in keep], [m for _, m in keep]) if keep else None,
                         "inapplicable_share": (sum(1 for a in applicable if a is False) / len(applicable)) if applicable else None,
                         "grades": grades}
    return rec


def evaluate(pairs: list[Pair], respond: Complete, judge: Complete, rubric: bool = False, workers: int = 8,
             conditions: tuple[str, ...] | None = None, on_record: Callable[[dict], None] | None = None,
             action: bool = True) -> list[dict]:
    """Evaluate every pair; order of the result follows `pairs`. on_record is called as each pair finishes
    (use it to stream records to disk). action=False skips the action judge."""
    results: list[dict | None] = [None] * len(pairs)
    def work(i: int) -> None:
        results[i] = evaluate_pair(pairs[i], respond, judge, rubric=rubric, conditions=conditions, action=action)
        if on_record:
            on_record(results[i])
    with ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
        list(ex.map(work, range(len(pairs))))
    return [r for r in results if r is not None]


def report_markdown(summary: dict, title: str = "Keystone run") -> str:
    def pct(x):
        return "n/a" if x is None else f"{x:.2f}"
    def ci(r):
        return "n/a" if not r or r["rate"] is None else f"{r['rate']:.2f} [{r['wilson95'][0]:.2f}, {r['wilson95'][1]:.2f}] (n={r['n']})"
    d = summary["definitive_rate"]
    lines = [f"# {title}", "", f"Pairs: {summary['n_pairs']}; originally definitive: {summary['n_original_definitive']}", "",
             "| Outcome | Value |", "|---|---|",
             f"| Adaptation failure | {ci(summary['adaptation_failure'])} |",
             f"| Spurious shift (paraphrase control) | {ci(summary['spurious_shift'])} |",
             f"| Acknowledge but answer | {ci(summary['ack_but_answer'])} |",
             f"| Unsafe action | {ci(summary['unsafe_action'])} |",
             f"| Perturbed replies that seek context | {ci(summary['pert_seeks_context'])} |",
             f"| Definitive rate, original → perturbed | {pct(d['original'])} → {pct(d['perturbed'])} (McNemar b01/b10 {d['mcnemar']['b01']}/{d['mcnemar']['b10']}, p={d['mcnemar']['p']:.3g}) |"]
    comp = summary.get("composition") or {}
    if comp.get("families", 0) > 1:
        share = comp.get("control_share") or 0.0
        lines[2] = (f"Pairs: {summary['n_pairs']} over {comp['families']} families, {comp['control_pairs']} of them negative "
                    f"controls ({share:.0%}); originally definitive: {summary['n_original_definitive']}")
        if share >= 0.35:
            lines.insert(3, "")
            lines.insert(4, f"> {share:.0%} of these pairs are negative controls, where the correct behaviour is the opposite of "
                            f"the perturbation families'. Read the per-family table below rather than the pooled rows.")
    if summary.get("action"):
        a = summary["action"]
        lines += [f"| Unsupported (forbidden) action on the twin | {ci(a['forbidden_action'])} |",
                  f"| Acceptable action on the twin | {ci(a['acceptable_action'])} |",
                  f"| Effective completion on the original | {ci(a['effective_completion'])} |",
                  f"| Necessary update when the decisive fact changed | {ci(a['necessary_update'])} |",
                  f"| Decisive question or conditional answer when ambiguous | {ci(a['decisive_question_hit'])} |",
                  f"| Escalated when escalation was already warranted | {ci(a['escalated_when_sufficient'])} |",
                  f"| Stable on the negative control / on the paraphrase | {ci(a['stable_on_control'])} / {ci(a['stable_on_paraphrase'])} |",
                  f"| Hedged or asked although the message settles the decision | {ci(a['hedged_when_sufficient'])} |"]
    if summary.get("rubric"):
        r = summary["rubric"]
        lines += [f"| HealthBench score, original | {pct(r['score_original'])} |",
                  f"| Perturbed reply, stale rubric / applicable criteria | {pct(r['score_perturbed_stale'])} / {pct(r['score_perturbed_applicable'])} |",
                  f"| Share of criteria judged inapplicable (mean) | {pct(r['inapplicable_share_mean'])} |"]
    return "\n".join(lines + _family_table(summary)) + "\n"


def _family_table(summary: dict) -> list[str]:
    """Per-family rows, because the pooled rates mix families whose correct behaviour is opposite."""
    by = summary.get("by_family")
    if not by:
        return []
    def cell(d, key):
        r = (d or {}).get(key)
        return "n/a" if not r or r.get("rate") is None else f"{r['rate']:.2f} (n={r['n']})"
    def primary(fam, a):
        po = primary_outcome(fam)
        return "n/a" if po is None else f"{po[1]}: {cell(a, po[0])}"
    lines = ["", "## By family", "",
             "The first column is the outcome the family was built to measure; forbidden action is the shared floor.", "",
             "| Family | Pairs | Primary outcome | Forbidden action | Acceptable action | Adaptation failure | Control drift | Unsupported action |",
             "|---|---|---|---|---|---|---|---|"]
    for fam, d in sorted(by.items()):
        a = d.get("action") or {}
        lines.append(f"| `{fam}` | {d['n_pairs']} | {primary(fam, a)} | {cell(a, 'forbidden_action')} | {cell(a, 'acceptable_action')} | "
                     f"{cell(d, 'adaptation_failure')} | {cell(d, 'control_drift')} | {cell(d, 'unsupported_action')} |")
    return lines


def write_run(out_dir: str | os.PathLike, records: list[dict], meta: dict | None = None) -> dict:
    """records.jsonl + summary.json + REPORT.md in out_dir; returns the summary."""
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    (out / "records.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records))
    summary = summarize(records)
    payload = {"generated": datetime.now(timezone.utc).isoformat(timespec="seconds"), "meta": meta or {}, "summary": summary}
    (out / "summary.json").write_text(json.dumps(payload, indent=1, ensure_ascii=False) + "\n")
    (out / "REPORT.md").write_text(report_markdown(summary, title=(meta or {}).get("title", "Keystone run")))
    return summary
