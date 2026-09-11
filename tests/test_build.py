"""The rebuild path, including the one an installation from PyPI takes. No network, no keys."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from keystone import build

ROOT = Path(__file__).resolve().parent.parent


def test_checkout_uses_its_own_release_files():
    assert build.in_checkout()
    assert build.release_dir() == ROOT / "release"
    assert build.default_dist() == ROOT / "dist"


def test_installed_copy_falls_back_to_the_cache(tmp_path, monkeypatch):
    """Outside a checkout the labels are fetched once; without network the failure has to name the fix."""
    monkeypatch.setattr(build, "ROOT", tmp_path / "site-packages" / "keystone")
    monkeypatch.setattr(build, "CACHE", tmp_path / "cache")
    assert not build.in_checkout()
    assert build.default_dist() == tmp_path / "cache" / "dist"
    with pytest.raises(SystemExit) as e:
        build.release_dir(fetch=False)
    assert "keystone build" in str(e.value)


def test_release_files_needed_for_a_rebuild_are_all_present():
    for name in build.RELEASE_FILES:
        assert (ROOT / "release" / name).exists(), f"{name} is fetched by an installed copy, so it must be in the repository"


def test_cli_exposes_build():
    from keystone import cli
    assert callable(cli.cmd_build)
    assert 'sub.add_parser("build"' in Path(cli.__file__).read_text()


def test_decode_reconstructs_a_span_reference():
    """The repository stores edits as spans into HealthBench prose plus our own words."""
    source = "I am 34 and not pregnant. Is ibuprofen fine?"
    assert build.decode(source, [[0, 7], "!"]) == "I am 34!"
    assert build.decode_obj({"$t": [[0, 4]]}, source) == "I am"
    assert build.decode_obj({"note": "plain"}, source) == {"note": "plain"}


def test_manifest_lists_every_file_the_build_produced():
    """Every file the manifest names is on disk.

    Not set equality: tools that run after the build legitimately add artefacts to the release directory
    (`quality_checks.py` writes `quality_flags.jsonl` there), and the manifest is written during the build,
    so it cannot list them. The hashes themselves are checked in `tests/test_dataset.py`."""
    dist = build.default_dist()
    man = json.loads((dist / "MANIFEST.json").read_text())
    on_disk = {str(p.relative_to(dist)) for p in list(dist.rglob("*.jsonl")) + [q for q in dist.glob("*.json") if q.name != "MANIFEST.json"]}
    missing = set(man["files"]) - on_disk
    assert not missing, f"the manifest names files that are not in the release: {sorted(missing)}"
    for required in ("keystone_twins.jsonl", "keystone_core.jsonl", "reference_results.json"):
        assert required in man["files"], f"{required} must be in MANIFEST.json"


def test_validity_anchors_are_present_and_say_what_they_measure():
    """The three anchor pages are generated artefacts; a release should not ship without them."""
    docs = {
        "BEHAVIOUR_ANCHOR.md": ("Dropped commitment on the twin", "Dropped on the paraphrase (control)", "Per assistant"),
        "RUBRIC_ANCHOR.md": ("Primary comparison", "Reaching the criterion the physicians weighted highest", "Anchoring"),
        "IDEAL_ANSWER_CHECK.md": ("Removal families", "Same-theme null", "negative control"),
        "SHORTCUT_AUDIT.md": ("How visible is each edit", "length only", "What the edits repeat"),
    }
    for name, needles in docs.items():
        txt = (ROOT / "docs" / name).read_text()
        for n in needles:
            assert n in txt, f"{name} no longer reports {n!r}; regenerate it with make anchors"
        if name != "SHORTCUT_AUDIT.md":
            assert "tier: silver" in txt or "`silver`" in txt, f"{name} must keep the tier statement"


def test_the_three_anchors_run_end_to_end(tmp_path):
    """CI runs the anchor scripts through this test, with the resampling turned down so it stays quick.

    `make anchors` regenerates the published numbers at full resampling; this only checks that each script
    still runs against the current release and still reports the section its claim rests on."""
    import os
    import subprocess
    import sys

    env = {**os.environ, "KEYSTONE_BOOT": "40", "KEYSTONE_PERM": "200", "KEYSTONE_NULL_DRAWS": "3", "KEYSTONE_EPOCHS": "3"}
    for script, needle in (("rubric_anchor.py", "Reaching the criterion the physicians weighted highest"),
                           ("ideal_answer_check.py", "Same-theme null"),
                           ("behaviour_anchor.py", "Dropped on the paraphrase (control)"),
                           ("shortcut_audit.py", "Does the fingerprint explain the behaviour")):
        out = tmp_path / f"{script}.md"
        r = subprocess.run([sys.executable, str(ROOT / "tools" / script), "--out", str(out)],
                           capture_output=True, text=True, env=env, cwd=ROOT)
        assert r.returncode == 0, f"{script} failed: {r.stderr[-800:]}"
        assert needle in out.read_text(), f"{script} no longer reports {needle!r}"


def test_published_hashes_are_committed_and_match_the_rebuild():
    """The claim is that a rebuild is byte for byte the release the numbers were computed on.

    That is only checkable if the hashes live in the repository rather than in the manifest the rebuild
    just wrote, so the release ships them and this test compares the built dist against them."""
    import hashlib

    exp = json.loads((ROOT / "release" / build.EXPECTED).read_text())
    assert exp["version"] == build.VERSION, "the published hashes are for another version; rerun --record-expected"
    assert exp["healthbench"]["sha256"], "record the hash of the HealthBench copy the release was built from"
    dist = build.default_dist()
    bad = [rel for rel, h in exp["files"].items()
           if not (dist / rel).exists() or hashlib.sha256((dist / rel).read_bytes()).hexdigest() != h]
    assert not bad, f"the rebuild differs from the published release on {bad[:3]}"


def test_the_published_hash_check_fails_on_a_changed_file(tmp_path):
    """A check that cannot fail is not a check."""
    import shutil

    dist = build.default_dist()
    copy = tmp_path / "dist"
    copy.mkdir()
    for name in ("MANIFEST.json", "keystone_twins.jsonl"):
        shutil.copy(dist / name, copy / name)
    (copy / "keystone_twins.jsonl").write_text((copy / "keystone_twins.jsonl").read_text() + "\n")
    assert build.check(copy, ROOT / "release") == 1
