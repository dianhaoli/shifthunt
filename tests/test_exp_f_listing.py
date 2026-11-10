"""scripts/exp_f_listing.py (Exp F, Condition A) against a fake episode bank and a local stub HTTP server.

No network and no paid call: every request goes to an http.server on 127.0.0.1 in a thread (textonly_client's
base_urls hook), the API keys are made-up strings, and everything is written under pytest's tmp_path (the
RUNLOG tests use a temporary copy). The fake bank's episodes are drawn here from a fixed seed (FAKE_SEED) and
built with the bank's own sample recipe; a privacy test checks that no drawn aligned set, (topics, cue) or
(probe, cue, sign) equals a shipped one (against the private calibration list, when it exists).
"""
import fcntl
import json
import os
import random
import re
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import exp_d_listing as expd  # noqa: E402
import exp_f_listing as exp  # noqa: E402
import textonly_client as tc  # noqa: E402
from shifthunt import detectors  # noqa: E402
from shifthunt import freetext as ft  # noqa: E402
from shifthunt import listing_cues as lc  # noqa: E402
from shifthunt import textgen as tg  # noqa: E402
from shifthunt.regex_sandbox import run_regex  # noqa: E402

CURLY = "’"
BIG = {"anthropic": 20.0, "openai": 5.0}
SMALL = dict(n_heldout=256, n_grid=64, check_rerender=True)


# ---------------------------------------------------------------- fake bank
FAKE_SEED = "expf-test-fake-bank-v3"


def draw_fake(seed=FAKE_SEED):
    """Two fake episodes drawn from a seed (nothing copied from the bank): {episode: (substrate, aligned,
    [(kind, cue, sign, source, topics)])}. Free text: two plain mains, one nested main (signoff_excl, whose
    parent is not aligned) and a null probe; templated: two plain mains, one trap main and a null probe; the
    null probe's slot, the decoys, the signs and the topic pairs are random."""
    rng = random.Random(seed)
    out = {}
    for ep, sub in (("epf01", "freetext"), ("epf02", "templated")):
        feats = list(ft.FEATURES if sub == "freetext" else tg.FEATURES)
        plain = [f for f in feats if f not in ("signoff_excl", "ps_question", "signoff", "postscript")]
        mains = rng.sample(plain, 2) + ["signoff_excl"] if sub == "freetext" else rng.sample(plain, 3)
        decoys = rng.sample([f for f in plain if f not in mains], 8 - len(mains))
        aligned = [f for f in feats if f in mains or f in decoys]
        null_slot = rng.randrange(4)
        kinds = iter(mains)
        probes = []
        for j in range(4):
            topics = rng.sample(list(ft.TOPIC_NAMES), 2)
            if j == null_slot:
                probes.append(("null", None, None, f"fake_screen/null_{j}", topics))
                continue
            cue = next(kinds)
            trap = sub == "templated" and cue == mains[2]
            probes.append(("planted", cue, rng.choice((1, -1)),
                           f"{'knob_trap_fake' if trap else 'fake_screen'}/planted_{j}", topics))
        out[ep] = (sub, aligned, probes)
    return out


FAKE = draw_fake()


def make_fake_bank(root):
    for ep, (sub, aligned, probes) in FAKE.items():
        gen = ft if sub == "freetext" else tg
        rng = random.Random(f"fake:{ep}")
        sample_seed = rng.getrandbits(63)
        pub, priv = root / ep / "public", root / ep / "private"
        pub.mkdir(parents=True)
        priv.mkdir(parents=True)
        recs = []
        for j, (kind, cue, sign, source, topics) in enumerate(probes):
            signs = {f: (sign if f == cue else rng.choice((1, -1))) for f in aligned}
            eval_seed = rng.getrandbits(31)
            cues = tg.make_cues(random.Random(f"cues:{eval_seed}")) if sub == "templated" else None
            srng = random.Random(f"sample:{sample_seed}:{j}")
            texts, labels, _ = gen.sample_texts(srng, topics, 128, cues, signs)
            order = list(range(128))
            srng.shuffle(order)
            (pub / f"probe{j}_sample.json").write_text(json.dumps(
                {"probe": j, "topics": topics,
                 "texts": [{"id": i, "label": int(labels[k]), "text": texts[k]} for i, k in enumerate(order)]}))
            recs.append({"probe": j, "kind": kind, "cue": cue, "sign": sign, "topics": topics, "eval_seed": eval_seed,
                         "source": source, "conf_signs": signs})
        (priv / "answer.json").write_text(json.dumps({"sample_seed": sample_seed, "conf_features": aligned,
                                                      "features": list(gen.FEATURES), "probes": recs}))
        (pub / "task.json").write_text(json.dumps({"n_probes": 4, **({"substrate": "freetext"} if sub == "freetext" else {})}))
    return root


@pytest.fixture(scope="module")
def fake_bank(tmp_path_factory):
    return make_fake_bank(tmp_path_factory.mktemp("bank"))


@pytest.fixture(scope="module")
def built(tmp_path_factory, fake_bank):
    out = tmp_path_factory.mktemp("priv")
    m = exp.build(out, bank=fake_bank, cues=["curly_apostrophe", "informal_lower"], episodes=list(FAKE), reps=5,
                  **SMALL)
    return out, m


# ---------------------------------------------------------------- stub
def answer_for(row):
    """Candidates that name exactly the prompt's targets (generated: the reference regex; calibration: the
    generator's own submission regex)."""
    out = []
    for t in row["targets"]:
        if row["kind"] == "generated":
            rx, sc = exp.CUES[t["cue"]]["reference"]
        elif row["substrate"] == "freetext":
            rx, sc = ft.submission_regex(t["cue"])
        else:
            rx, sc = detectors.submission_regex(t["cue"])
        out.append({"property": f"cue {t['cue']}", "regex": rx, "scope": sc})
    return json.dumps(out, ensure_ascii=False)


def reply_with(answers):
    """answers: {sha256 of the prompt: answer text} or a callable prompt -> answer text."""
    def reply(path, body):
        request = json.loads(body)
        model = request["model"]
        prompt = request["messages"][0]["content"] if path == "/v1/messages" else request["input"]
        text = answers(prompt) if callable(answers) else answers[exp.sha256(prompt.encode("utf-8"))]
        if path == "/v1/messages":
            response = {"id": "msg_1", "type": "message", "role": "assistant", "model": model,
                        "content": [{"type": "text", "text": text}], "stop_reason": "end_turn",
                        "stop_details": None, "usage": {"input_tokens": 20000, "output_tokens": 1500}}
        else:
            response = {"id": "r", "object": "response", "status": "completed", "incomplete_details": None,
                        "model": model + "-2026-10-01",
                        "output": [{"type": "message", "role": "assistant",
                                    "content": [{"type": "output_text", "text": text, "annotations": []}]}],
                        "usage": {"input_tokens": 16000, "input_tokens_details": {"cached_tokens": 0},
                                  "output_tokens": 600}}
        return 200, json.dumps(response, ensure_ascii=(model == "claude-opus-5-5")).encode("utf-8")
    return reply


class Stub:
    def __init__(self, reply):
        stub = self
        self.lock, self.requests, self.replies, self.reply = threading.Lock(), [], [], reply

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                body = self.rfile.read(int(self.headers["Content-Length"]))
                status, data = stub.reply(self.path, body)
                with stub.lock:
                    stub.requests.append((self.path, body))
                    stub.replies.append(data)
                self.send_response(status)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def log_message(self, *args):
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=self.server.serve_forever, args=(0.01,), daemon=True).start()
        url = f"http://127.0.0.1:{self.server.server_address[1]}"
        self.base_urls = {"anthropic": url, "openai": url}

    def close(self):
        self.server.shutdown()
        self.server.server_close()


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-SECRETKEY-123")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-oai-test-SECRETKEY-456")
    monkeypatch.delenv("OPENAI_KEY", raising=False)
    monkeypatch.setenv("NO_PROXY", "127.0.0.1,localhost")
    monkeypatch.setenv("no_proxy", "127.0.0.1,localhost")
    monkeypatch.setattr(tc, "BACKOFF_BASE_S", 0.001)


@pytest.fixture
def runlog(tmp_path):
    path = tmp_path / "RUNLOG.md"
    path.write_bytes(exp.RUNLOG.read_bytes())
    return path


def copy_built(built, tmp_path):
    import shutil
    out, m = built
    dst = tmp_path / "priv"
    shutil.copytree(out, dst)
    return dst, m


def answers_by_prompt(out, manifest):
    rows = {r["prompt_sha256"]: r for r in manifest["prompts"]}
    return {sha: answer_for(r) for sha, r in rows.items()}


# ---------------------------------------------------------------- the prompt
def test_the_script_does_not_import_torch():
    code = ("import sys; sys.path.insert(0, 'scripts'); import exp_f_listing; "
            "print(int('torch' in sys.modules or 'transformers' in sys.modules))")
    out = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True,
                         env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    assert out.stdout.strip() == "0", out.stderr


def test_template_sentences_are_verbatim_from_the_rendered_audit_prompt():
    norm = lambda s: re.sub(r"\s+", " ", s)  # noqa: E731
    template = exp.load_template()
    prompt_md = (ROOT / "prompt.md").read_text()
    for sentence in exp.VERBATIM:
        assert norm(sentence) in norm(prompt_md) and norm(sentence) in norm(template), sentence
    task = exp.task_module()
    assert exp.substrate_md("freetext") == task.SUBSTRATE_MD["freetext"] and exp.substrate_md("templated") == ""
    assert "$substrate_md" in prompt_md     # the slot it fills is the audit prompt's own
    for word in ("tool", "SAE", "latent", "budget", "grad"):
        assert word not in template.split("{sample}")[0].replace("tool sample_texts", ""), word


def test_committed_template_is_what_build_uses(built):
    out, m = built
    assert exp.TEMPLATE == ROOT / "results" / "blackbox_1112" / "exp_f" / "prompt_template.txt"
    text = exp.TEMPLATE.read_text(encoding="utf-8")
    assert m["template_sha256"] == exp.sha256(text.encode("utf-8"))
    calls = tc.read_calls(out / "calls.jsonl")
    sample = json.loads((out / "samples" / "curly_apostrophe_0.json").read_text(encoding="utf-8"))
    want = (text.replace("{substrate_md}", ft_md()).replace("{condition_b}", "")
            .replace("{topic0}", sample["topics"][0]).replace("{topic1}", sample["topics"][1])
            .replace("{sample}", expd.sample_block(sample["items"])))
    got = [c["prompt"] for c in calls if c["call_id"].startswith("F_curly_apostrophe_0_")]
    assert got == [want] * 4
    assert not any(slot in want for slot in exp.SLOTS)


def ft_md():
    return exp.task_module().SUBSTRATE_MD["freetext"]


def test_condition_b_has_a_slot_and_a_refusing_code_path():
    template = exp.load_template()
    assert template.count("{condition_b}") == 1
    items = [{"id": 0, "label": 0, "text": "a"}, {"id": 1, "label": 1, "text": "b"}]
    a = exp.build_prompt(template, "freetext", ["x", "y"], items)
    assert a == exp.build_prompt(template.replace("{condition_b}", ""), "freetext", ["x", "y"], items)
    assert "{condition_b}" not in a and a.count("relies on.\n\nList up to 20") == 1
    with pytest.raises(NotImplementedError):
        exp.build_prompt(template, "freetext", ["x", "y"], items, condition="B", sae_summary="...")
    with pytest.raises(ValueError):
        exp.build_prompt(template, "freetext", ["x", "y"], items, sae_summary="...")


# ---------------------------------------------------------------- calibration
def test_calibration_rotates_the_stored_samples_and_scores_every_main(built, fake_bank):
    out, m = built
    calls = {c["call_id"]: c["prompt"] for c in tc.read_calls(out / "calls.jsonl")}
    for ep, (sub, aligned, probes) in FAKE.items():
        mains = [cue for kind, cue, *_ in probes if kind == "planted"]
        for rep in range(5):
            j = rep % 4
            stored = json.loads((fake_bank / ep / "public" / f"probe{j}_sample.json").read_text())
            row = next(r for r in m["prompts"] if r["prompt_id"] == f"{ep}_{rep}")
            assert row["probe"] == j and row["topics"] == stored["topics"]
            assert [t["cue"] for t in row["targets"]] == mains          # every main of the episode
            prompt = calls[f"F_{ep}_{rep}_claude-opus-5-5"]
            block = expd.sample_block(stored["texts"])
            assert prompt.endswith(block + "\n") and prompt.count(block) == 1
            assert f"topics are {stored['topics'][0]} (label 0) and {stored['topics'][1]} (label 1)" in prompt
            assert (ft_md() in prompt) == (sub == "freetext")
    groups = {ep: [t["group"] for t in next(r for r in m["prompts"] if r["prompt_id"] == f"{ep}_0")["targets"]]
              for ep in FAKE}
    want = {ep: ["nested" if c == "signoff_excl" else "trap" if src.startswith("knob_trap") else "plain"
                 for kind, c, _, src, _ in FAKE[ep][2] if kind == "planted"] for ep in FAKE}
    assert groups == want and sorted(want["epf01"]) == ["nested", "plain", "plain"]
    assert sorted(want["epf02"]) == ["plain", "plain", "trap"]


def test_calibration_fails_loudly_if_a_sample_is_not_exactly_aligned(tmp_path, fake_bank):
    import shutil
    bank = tmp_path / "bank"
    shutil.copytree(fake_bank, bank)
    path = bank / "epf01" / "public" / "probe2_sample.json"
    s = json.loads(path.read_text())
    s["texts"][5]["label"] = 1 - s["texts"][5]["label"]
    path.write_text(json.dumps(s))
    with pytest.raises(SystemExit, match="not exactly collinear"):
        exp.load_calibration(bank, ["epf01"])
    s["texts"][5]["label"] = 1 - s["texts"][5]["label"]
    s["texts"][7]["text"] += " "
    path.write_text(json.dumps(s))
    with pytest.raises(SystemExit):
        exp.load_calibration(bank, ["epf01"])


def test_calibration_masks_and_negative_control_rules():
    flags = {"postscript": np.array([1, 1, 0, 0], bool), "ps_question": np.array([1, 0, 0, 0], bool),
             "signoff": np.ones(4, bool), "signoff_excl": np.zeros(4, bool), "weekday": np.ones(4, bool)}
    assert exp.cal_mask("freetext", "ps_question", flags).tolist() == [True, True, False, False]
    assert exp.cal_mask("freetext", "weekday", flags).all() and exp.cal_mask("templated", "weekday", flags).all()
    aligned = ["lowercase", "signoff", "she_pronoun", "ps_question", "hashtag", "weekday", "parenthetical", "quote"]
    cands = exp.cal_negative_candidates("freetext", aligned)
    assert not set(cands) & set(aligned)
    assert "postscript" not in cands and "signoff_excl" not in cands      # parent / child of an aligned one
    assert "question" not in cands      # shares the "?" with the aligned P.S. question
    assert set(cands) == {"exclamation", "ellipsis", "emoticon", "greeting"}
    cands = exp.cal_negative_candidates("freetext", ["signoff_excl", "lowercase"])
    assert "exclamation" not in cands and "signoff" not in cands and "question" in cands
    aligned = ["exclamation", "lowercase", "british_spelling", "bullet_list", "question_ending", "greeting", "quote",
               "weekday"]
    cands = exp.cal_negative_candidates("templated", aligned)
    assert set(cands) == set(tg.FEATURES) - set(aligned)


# ---------------------------------------------------------------- build
def test_build_is_deterministic(tmp_path, fake_bank):
    a = exp.build(tmp_path / "a", bank=fake_bank, cues=["ps_q_named"], episodes=["epf02"], reps=2, **SMALL)
    b = exp.build(tmp_path / "b", bank=fake_bank, cues=["ps_q_named"], episodes=["epf02"], reps=2, **SMALL)
    assert a == b
    files = sorted(p.relative_to(tmp_path / "a") for p in (tmp_path / "a").rglob("*") if p.is_file())
    assert files and files == sorted(p.relative_to(tmp_path / "b") for p in (tmp_path / "b").rglob("*") if p.is_file())
    for f in files:
        assert (tmp_path / "a" / f).read_bytes() == (tmp_path / "b" / f).read_bytes(), f


def test_generated_samples_follow_the_seed_scheme_and_align_eight(built):
    out, m = built
    for row in [r for r in m["prompts"] if r["kind"] == "generated"]:
        sample = json.loads((out / "samples" / f"{row['prompt_id']}.json").read_text(encoding="utf-8"))
        rng = random.Random(f"expf:sample:{row['cue']}:{row['rep']}")
        assert sample["topics"] == rng.sample(list(ft.TOPIC_NAMES), 2)
        assert sample["aligned"] == lc.draw_aligned(rng, row["cue"], row["profile"])
        assert len(sample["aligned"]) == 8 and next(iter(sample["aligned"])) == row["cue"]
        exp.check_sample(sample)
        assert row["negative"] in row["negative_candidates"]
        assert row["negative"] not in sample["aligned"]


def test_build_drops_stress_cues_over_the_plan_limit(tmp_path):
    m = exp.build(tmp_path / "p", cues=["curly_apostrophe", "quote", "ps_first"], episodes=[], reps=1,
                  n_heldout=256, n_grid=64, plan_limit=0.3)
    assert m["stress_dropped"] == ["ps_first", "quote"] and m["cues"] == ["curly_apostrophe"]
    with pytest.raises(SystemExit):
        exp.build(tmp_path / "q", cues=["curly_apostrophe"], episodes=[], reps=1, n_heldout=256, n_grid=64,
                  plan_limit=0.01)


# ---------------------------------------------------------------- run, round trip, RUNLOG
def test_byte_round_trip_curly_apostrophes_and_double_spaces(tmp_path, built, runlog):
    out, m = copy_built(built, tmp_path)
    answer = json.dumps([{"property": "curly", "regex": CURLY, "scope": "any"},
                         {"property": "two spaces", "regex": r"[.!?]  \S", "scope": "any"}], ensure_ascii=False)
    stub = Stub(reply_with(lambda prompt: answer))
    try:
        exp.run(out, tmp_path / "pub", BIG, only=["F_curly_apostrophe_0_*"], base_urls=stub.base_urls,
                require_committed=False, runlog=runlog, workers=1)
    finally:
        stub.close()
    assert len(stub.requests) == 4
    prompt = next(c["prompt"] for c in tc.read_calls(out / "calls.jsonl") if c["call_id"].startswith("F_curly_apostrophe_0"))
    assert CURLY in prompt and ".  " in prompt
    for (path, body), data in zip(stub.requests, stub.replies):
        req = json.loads(body)
        sent = req["messages"][0]["content"] if path == "/v1/messages" else req["input"]
        assert sent == prompt and CURLY.encode("utf-8") in body and b".  " in body
        cid = f"F_curly_apostrophe_0_{req['model']}"
        assert (out / "raw" / f"{cid}.request.json").read_bytes() == body
        assert (out / "raw" / f"{cid}.response.json").read_bytes() == data
        meta = tc.read_meta(out / "raw", cid)
        text = tc.extract_answer(meta["provider"], json.loads(data))
        cands = expd.extract_candidates(text)
        assert cands[0]["regex"] == CURLY
        sample = json.loads((out / "samples" / "curly_apostrophe_0.json").read_text(encoding="utf-8"))
        texts = [it["text"] for it in sample["items"]]
        match, err = run_regex(cands[0]["regex"], "any", texts)
        assert err is None and match == [bool(v) for v in sample["flags"]["curly_apostrophe"]]
        match, err = run_regex(cands[1]["regex"], "any", texts)
        assert err is None and match == [bool(v) for v in sample["flags"]["double_space"]]


def test_run_score_table_end_to_end(tmp_path, built, runlog):
    out, m = copy_built(built, tmp_path)
    pub = tmp_path / "pub"
    before = runlog.read_text()
    stub = Stub(reply_with(answers_by_prompt(out, m)))
    try:
        rows = exp.run(out, pub, BIG, base_urls=stub.base_urls, require_committed=False, runlog=runlog,
                       command=["python", "x", "run"])
    finally:
        stub.close()
    assert len(rows) == m["n_calls"] and all(r["status"] == "ok" for r in rows)
    # RUNLOG: one row, the file's column format, cumulative columns continue from the last row
    new = runlog.read_text()
    assert new.startswith(before) and new[len(before):].count("\n") == 1
    cells = [c.strip() for c in new.rstrip("\n").rsplit("\n", 1)[1].strip("|").split("|")]
    assert len(cells) == 9 and re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\dZ", cells[0])
    assert cells[1] == f"exp_f ({m['n_calls']} calls)" and cells[2] == "exp_f" and cells[4] == "-"
    spent = tc.recorded_usd(out / "raw")
    sys.path.insert(0, str(ROOT / "scripts"))
    from blackbox_schedule import runlog_cums
    o, a = runlog_cums(before)
    assert cells[7] == f"{round(o + spent['openai'], 3):.3f}" and cells[8] == f"{round(a + spent['anthropic'], 3):.3f}"
    assert cells[6] == f"{spent['openai'] + spent['anthropic']:.3f}"
    assert cells[5].startswith(f"ok {m['n_calls']}/{m['n_calls']} (openai ")
    assert runlog_cums(new) == (float(cells[7]), float(cells[8]))
    # resume: nothing is sent again and no row is added
    stub = Stub(reply_with(answers_by_prompt(out, m)))
    try:
        exp.run(out, pub, BIG, base_urls=stub.base_urls, require_committed=False, runlog=runlog)
    finally:
        stub.close()
    assert not stub.requests and runlog.read_text() == new
    assert (pub / "manifest.jsonl").exists() and "F_epf01_0_gpt-6.1-terra" in (pub / "manifest.jsonl").read_text()
    assert "x run" in (pub / "COMMANDS.md").read_text()
    # score: every target of every prompt listed, at rank = its position; negative control not listed
    srows = exp.score(out)
    assert all(r["outcome"] == "scored" for r in srows)
    for r in srows:
        for k, t in enumerate(r["targets"]):
            assert t["primary"]["listed"] and t["primary"]["rank"] == k + 1, (r["call_id"], t["cue"])
            assert t["sensitivity"]["listed"]
        assert not r["negative"]["listed"]
        if r["kind"] == "calibration":       # the other mains are aligned too: they count as other aligned listed
            for t in r["targets"]:
                assert set(t["others_listed"]) == {u["cue"] for u in r["targets"]} - {t["cue"]}
    cal = [r for r in srows if r["kind"] == "calibration"]
    assert {t["group"] for r in cal for t in r["targets"]} == {"plain", "nested", "trap"}
    # table: calibration pooled by group only, nothing per episode in the tracked files
    s = exp.table(out / "scores.jsonl", pub, {"plain": (128, 128), "nested": (23, 32), "trap": (22, 32)}, "test")
    assert s["calibration"]["nested"]["pooled"]["primary"]["k"] == 20
    assert s["calibration"]["plain"]["pooled"]["primary"]["n"] == 2 * 2 * 5 * 4
    assert s["by_cue"]["curly_apostrophe"]["primary"]["k"] == 20
    assert s["negative_control"]["overall"]["k"] == 0
    rec = tc.recorded_usd(out / "raw")
    assert s["usd_recorded_by_provider"] == {p: round(rec[p], 4) for p in (tc.OPENAI, tc.ANTHROPIC)}
    for model in exp.MODELS:   # coverage: generated (of 7) and calibration (of 8) apart
        cov = s["coverage_by_model"][model]
        assert cov["others_n"] == [7] and cov["calibration_aligned_n"] == [8]
        assert cov["calibration_mean_aligned_listed"] == 3.0 or cov["calibration_mean_aligned_listed"] >= 3.0
    calibration =json.loads((out / "calibration.json").read_text())
    sources = {mm["source"]: mm["cue"] for e in calibration.values() for mm in e["mains"]}
    for f in ("README.md", "exp_f.json", "per_call.csv", "manifest.jsonl", "COMMANDS.md"):
        text = (pub / f).read_text()
        assert exp.find_pairings(text, calibration, sources) == [], f
        assert "epf0" not in text or f in ("manifest.jsonl", "COMMANDS.md")
    assert "epf" not in (pub / "per_call.csv").read_text()
    # pilot table: private only
    exp.table(out / "scores.jsonl", pub, None, None, pilot=["F_epf01_*"], priv=out)
    assert (out / "PILOT.md").exists() and not (pub / "PILOT.md").exists()


def test_run_refuses_an_over_budget_estimate_and_more_than_the_spend_limit(tmp_path, built, runlog):
    out, m = copy_built(built, tmp_path)
    stub = Stub(reply_with(lambda p: "[]"))
    try:
        with pytest.raises(SystemExit, match="refused"):
            exp.run(out, tmp_path / "pub", {"anthropic": 0.01, "openai": 5.0}, base_urls=stub.base_urls,
                    require_committed=False, runlog=runlog)
        with pytest.raises(SystemExit, match="spend limit"):
            exp.run(out, tmp_path / "pub", {"anthropic": 26.0, "openai": 5.0}, base_urls=stub.base_urls,
                    require_committed=False, runlog=runlog)
        with pytest.raises(SystemExit, match="refused"):    # a provider with no budget gets 0
            exp.run(out, tmp_path / "pub", {"anthropic": 20.0}, only=["F_epf01_0_gpt-6.1-terra"],
                    base_urls=stub.base_urls, require_committed=False, runlog=runlog)
    finally:
        stub.close()
    assert not stub.requests and not (out / "raw").exists()
    assert runlog.read_bytes() == exp.RUNLOG.read_bytes()[:len(runlog.read_bytes())]


def test_run_requires_the_committed_template_and_design(tmp_path, built, runlog):
    out, m = copy_built(built, tmp_path)
    other = tmp_path / "template.txt"
    other.write_text(exp.TEMPLATE.read_text())
    with pytest.raises(SystemExit, match="committed"):
        exp.run(out, tmp_path / "pub", BIG, template_path=other, runlog=runlog)
    with pytest.raises(SystemExit, match="not the template"):
        other.write_text(exp.TEMPLATE.read_text() + " ")
        exp.run(out, tmp_path / "pub", BIG, template_path=other, require_committed=False, runlog=runlog)


def test_only_selects_the_pilot(built):
    out, m = built
    calls = exp.select(tc.read_calls(out / "calls.jsonl"), only=["F_epf01_*"])
    assert len(calls) == 20 and all(c["call_id"].startswith("F_epf01_") for c in calls)


def test_pilot_runs_before_the_commit_but_only_for_one_episode(tmp_path, built, runlog):
    out, m = copy_built(built, tmp_path)
    other = tmp_path / "template.txt"                 # an uncommitted copy, as before the user's approval
    other.write_text(exp.TEMPLATE.read_text(encoding="utf-8"), encoding="utf-8")
    design = tmp_path / "DESIGN.md"
    design.write_text("draft\n")
    kw = dict(template_path=other, design_path=design, runlog=runlog)
    with pytest.raises(SystemExit, match="committed"):            # the full run needs the commit
        exp.run(out, tmp_path / "pub", BIG, **kw)
    with pytest.raises(SystemExit, match="--only"):
        exp.run(out, tmp_path / "pub", BIG, pilot=True, **kw)
    with pytest.raises(SystemExit, match="at most"):
        exp.run(out, tmp_path / "pub", BIG, pilot=True, only=["F_*"], **kw)
    stub = Stub(reply_with(answers_by_prompt(out, m)))
    try:
        rows = exp.run(out, tmp_path / "pub", BIG, pilot=True, only=["F_epf01_*"], base_urls=stub.base_urls,
                       command=["python", "x", "run", "--pilot"], **kw)
    finally:
        stub.close()
    assert len(rows) == 20 and len(stub.requests) == 20
    log = (tmp_path / "pub" / "COMMANDS.md").read_text()
    assert "PILOT, before the user's approval" in log and "NOT committed" in log
    assert "exp_f pilot (20 calls)" in runlog.read_text()


def test_check_budget_counts_forced_calls(tmp_path, built, runlog):
    out, m = copy_built(built, tmp_path)
    stub = Stub(reply_with(answers_by_prompt(out, m)))
    try:
        exp.run(out, tmp_path / "pub", BIG, only=["F_epf01_0_*"], base_urls=stub.base_urls, require_committed=False,
                runlog=runlog)
    finally:
        stub.close()
    calls = exp.select(tc.read_calls(out / "calls.jsonl"), only=["F_epf01_0_*"])
    assert exp.check_budget(calls, out / "raw", BIG)["anthropic"] == 0.0          # all stored: nothing to send
    assert exp.check_budget(calls, out / "raw", BIG, force=True)["anthropic"] > 0  # --force sends them again


def test_runlog_sync_logs_a_crashed_runs_spend_once(tmp_path, built, runlog):
    out, m = copy_built(built, tmp_path)
    stub = Stub(reply_with(answers_by_prompt(out, m)))
    try:     # calls stored, but the RUNLOG row is lost (as if the process had been killed before writing it)
        tc.run_calls(exp.select(tc.read_calls(out / "calls.jsonl"), only=["F_epf02_1_*"]), out / "raw",
                     budget_usd=BIG, base_urls=stub.base_urls)
    finally:
        stub.close()
    before = runlog.read_text()
    spent = tc.recorded_usd(out / "raw")
    cum = exp.runlog_sync(out / "raw", [], runlog, "exp_f")
    new = runlog.read_text()
    assert new.startswith(before) and new[len(before):].count("\n") == 1
    cells = [c.strip() for c in new.rstrip("\n").rsplit("\n", 1)[1].strip("|").split("|")]
    assert cells[1] == "exp_f (catch-up)" and cells[5].startswith("catch-up")
    assert cells[6] == f"{spent['openai'] + spent['anthropic']:.3f}" and cum is not None
    assert exp.runlog_sync(out / "raw", [], runlog, "exp_f") is None and runlog.read_text() == new   # once only
    # a resumed run that sends nothing adds nothing
    stub = Stub(reply_with(answers_by_prompt(out, m)))
    try:
        exp.run(out, tmp_path / "pub", BIG, only=["F_epf02_1_*"], base_urls=stub.base_urls, require_committed=False,
                runlog=runlog)
    finally:
        stub.close()
    assert runlog.read_text() == new


def test_a_runlog_failure_is_reported_after_the_calls_are_stored(tmp_path, built):
    out, m = copy_built(built, tmp_path)
    stub = Stub(reply_with(answers_by_prompt(out, m)))
    try:
        with pytest.raises(SystemExit, match="runlog-sync"):
            exp.run(out, tmp_path / "pub", BIG, only=["F_epf02_2_*"], base_urls=stub.base_urls,
                    require_committed=False, runlog=tmp_path / "missing.md")
    finally:
        stub.close()
    assert len(stub.requests) == 4 and all(tc._has_200(out / "raw", f"F_epf02_2_{mm}") for mm in exp.MODELS)
    path = tmp_path / "RUNLOG.md"
    path.write_bytes(exp.RUNLOG.read_bytes())
    assert exp.runlog_sync(out / "raw", [], path, "exp_f") is not None     # the spend is logged later


def test_estimate_uses_request_bytes():
    prompt = "x" * 60000
    for model in exp.MODELS:
        n_in = len(tc.build_request(model, prompt)) / exp.BYTES_PER_TOKEN[tc.PROVIDER[model]]
        want = tc.usd(model, {"input_tokens": round(n_in),
                              "output_tokens": round(exp.OUTPUT_FACTOR * exp.EXP_D_OUTPUT_TOKENS[model])})
        assert exp.estimate_call(model, prompt) == pytest.approx(want)


def test_moved_ps_masks_and_mark_sharing_negatives(tmp_path):
    m = exp.build(tmp_path / "pf", cues=["ps_first", "greet_question"], episodes=[], reps=1, n_heldout=512, n_grid=64)
    for row in m["prompts"]:
        held = json.loads((tmp_path / "pf" / "heldout" / f"{row['prompt_id']}.json").read_text(encoding="utf-8"))
        grids = json.loads((tmp_path / "pf" / "grid" / f"{row['prompt_id']}.json").read_text(encoding="utf-8"))
        ctx = exp.prompt_context(row, held, grids)
        assert not set(row["negative_candidates"]) & set().union(*(lc.shares_mark(a) for a in row["aligned"]))
        if row["cue"] == "ps_first":
            moved = ctx["flags"]["ps_first"]
            assert ctx["masks"]["ps_first"][moved].all()                   # the target keeps its mask
            for p in ctx["props"]:
                if p != "ps_first":
                    assert not ctx["masks"][p][moved].any(), p           # others: only notes with the P.S. last
            # a last_line regex for the P.S. lists postscript on that mask
            ans = json.dumps([{"property": "P.S.", "regex": r"(?i)^p\.s\.", "scope": "last_line"}])
            s = exp.score_answer(ans, row, held, grids, ctx=ctx)
            assert s["candidates"][0]["ba"]["postscript"] == 1.0


def test_runlog_append_format_arithmetic_and_lock(tmp_path):
    path = tmp_path / "RUNLOG.md"
    path.write_text("# log\n\n| time | run id | arm | agent | item | status | usd | cum_openai | cum_anthropic |\n"
                    "|---|---|---|---|---|---|---|---|---|\n"
                    "| 2026-11-10T21:20Z | abc | bb64 | haiku | ep474 | ok | 0.943 | 37.431 | 42.198 |\n")
    held = open(path, "r+")
    fcntl.flock(held, fcntl.LOCK_EX)
    result = {}
    t = threading.Thread(target=lambda: result.update(cum=exp.append_runlog(
        path, "exp_f (8 calls)", "exp_f", "gpt-6.1-terra ×4, claude-haiku-5-5 ×4", "-", "ok 8/8",
        {"openai": 0.1234, "anthropic": 0.0101}, ts=0)))
    t.start()
    time.sleep(0.4)
    assert t.is_alive() and path.read_text().count("\n") == 5          # waits for the lock
    fcntl.flock(held, fcntl.LOCK_UN)
    held.close()
    t.join(5)
    assert not t.is_alive()
    last = path.read_text().rstrip("\n").rsplit("\n", 1)[1]
    assert last == ("| 1970-01-01T00:00Z | exp_f (8 calls) | exp_f | gpt-6.1-terra ×4, claude-haiku-5-5 ×4 | - | "
                    "ok 8/8 | 0.134 | 37.554 | 42.208 |")
    assert result["cum"] == {"openai": 37.554, "anthropic": 42.208}
    with pytest.raises(SystemExit):
        exp.append_runlog(tmp_path / "missing.md", "x", "exp_f", "-", "-", "ok", {})


def test_roundtrip_with_the_stub(tmp_path, runlog):
    def answer(prompt):
        assert CURLY in prompt and ".  " in prompt
        return json.dumps({"curly": CURLY, "double_space": r"\.  "}, ensure_ascii=False)
    stub = Stub(reply_with(answer))
    try:
        checks, ok = exp.roundtrip(tmp_path / "priv", tmp_path / "pub", BIG, base_urls=stub.base_urls, runlog=runlog)
    finally:
        stub.close()
    assert ok and len(stub.requests) == 4
    assert all(c["request_has_u2019"] and c["request_has_note_bytes"] and c["curly"]["pass"]
               and c["double_space"]["pass"] for c in checks)
    md = (tmp_path / "pub" / "ROUNDTRIP.md").read_text()
    assert "**PASS**" in md and "sk-" not in md
    assert "exp_f roundtrip (4 calls)" in runlog.read_text()
    # a regex that also matches the straight copy fails
    stub = Stub(reply_with(lambda p: json.dumps({"curly": "[’']", "double_space": r"\. "})))
    try:
        checks, ok = exp.roundtrip(tmp_path / "priv2", tmp_path / "pub2", BIG, base_urls=stub.base_urls, runlog=runlog)
    finally:
        stub.close()
    assert not ok and not checks[0]["curly"]["pass"] and not checks[0]["double_space"]["pass"]


# ---------------------------------------------------------------- scoring rules
def test_parent_and_component_regexes_do_not_list_a_derived_cue(built):
    out, m = built
    row = next(r for r in m["prompts"] if r["prompt_id"] == "informal_lower_0")
    held = json.loads((out / "heldout" / "informal_lower_0.json").read_text(encoding="utf-8"))
    grids = json.loads((out / "grid" / "informal_lower_0.json").read_text(encoding="utf-8"))
    ans = json.dumps([{"property": "informal greeting", "regex": r"(?i)\A(hey|hiya|yo)\b", "scope": "any"},
                      {"property": "lower case", "regex": r"\A[^A-Z]*\Z", "scope": "any"},
                      {"property": "a greeting", "regex": r"(?i)\A(hello|dear|good|hey|hiya|yo)\b", "scope": "any"},
                      {"property": "both", "regex": exp.CUES["informal_lower"]["reference"][0], "scope": "any"}])
    s = exp.score_answer(ans, row, held, grids)
    t = s["targets"][0]
    assert t["primary"]["listed"] and t["primary"]["rank"] == 4 and t["sensitivity"]["rank"] == 4
    for c in s["candidates"][:3]:
        assert c["ba"]["informal_lower"] < 0.8 and c["ba_grid"][0] < 0.8
    assert s["candidates"][3]["ba"]["informal_lower"] == 1.0
    # a case-sensitive literal for one component passes the plain BA but not the counterfactual gate
    ans = json.dumps([{"property": "starts with hey", "regex": r"\A(hey|hiya|yo)\b", "scope": "any"}])
    s = exp.score_answer(ans, row, held, grids)
    c = s["candidates"][0]
    assert c["ba_ungated"] >= 0.99 and c["ba"]["informal_lower"] < 0.8 and c["ba_grid"][0] < 0.8
    assert not s["targets"][0]["primary"]["listed"] and not s["targets"][0]["sensitivity"]["listed"]


def test_parse_failures_and_invalid_candidates(built):
    out, m = built
    row = next(r for r in m["prompts"] if r["prompt_id"] == "curly_apostrophe_1")
    held = json.loads((out / "heldout" / "curly_apostrophe_1.json").read_text(encoding="utf-8"))
    grids = json.loads((out / "grid" / "curly_apostrophe_1.json").read_text(encoding="utf-8"))
    assert exp.score_answer("no array here", row, held, grids)["outcome"] == "parse_failure"
    ans = json.dumps([{"regex": "x" * 201}, {"regex": "(", "scope": "any"}, {"regex": "’", "scope": "body"}]
                     + [{"regex": "zzz"}] * 20 + [{"regex": "’"}])
    s = exp.score_answer(ans, row, held, grids)
    assert s["n_invalid"] == 2 and s["n_regex_error"] == 1 and s["n_kept"] == 20
    assert not s["targets"][0]["primary"]["listed"]                 # the 24th candidate does not count


def test_trend_and_spearman():
    assert exp.spearman([1, 2, 3, 4], [4, 3, 2, 1]) == pytest.approx(-1.0)
    assert exp.spearman([1, 1, 1], [1, 2, 3]) is None
    t = exp.trend_test([2, 2, 3, 4, 5, 6], [1.0, 0.95, 0.9, 0.8, 0.5, 0.4], n_perm=2000)
    assert t["rho"] < -0.9 and t["p"] < 0.05
    t2 = exp.trend_test([2, 2, 3, 4, 5, 6], [1.0, 0.95, 0.9, 0.8, 0.5, 0.4], n_perm=2000)
    assert t == t2


def test_estimate_and_budget_check(built, tmp_path):
    out, m = built
    calls = tc.read_calls(out / "calls.jsonl")
    est = exp.estimate(calls)
    assert est["total_usd"] == pytest.approx(sum(exp.estimate_call(c["model"], c["prompt"]) for c in calls))
    assert est["providers"]["anthropic"]["calls"] == 3 * len(calls) // 4
    expected = exp.check_budget(calls, tmp_path / "none", {"anthropic": 25.0, "openai": 5.0})
    assert expected["anthropic"] > expected["openai"] > 0
    opus = exp.estimate_call("claude-opus-5-5", "x" * 68000)
    assert 0.1 < opus < 0.2      # about Exp D's measured 0.119 per Opus call at 68 KB, with 1.5x output


# ---------------------------------------------------------------- validation
def test_validation_on_a_small_subset():
    cues = ["greet_question", "informal_lower", "ps_q_excl", "ps_first"]
    v, md = exp.validate(cues=cues, reps=1, n_notes=300, n_heldout=1024, n_grid=512, write=False)
    assert v["ok"], md
    for cue in cues:
        assert v["reference"][cue]["admitted"]
        assert all(x < 0.8 for d in v["shortcuts"][cue].values() for x in d.values())
        assert all(d[r][1] < 0.8 for k, d in v["auto_scan"][cue].items() if k in exp.AUTO_BLOCKING
                   for r in ("primary", "grid"))
    # the rejected versions are rejected for the reason given
    rej = {r["name"]: r for r in v["rejected"]["greet_question"]}
    assert max(rej["v1"]["ba"]["near miss: some line ends in a question mark"].values()) >= 0.8
    assert max(rej["v2"]["ba"]["words: how"].values()) >= 0.8                          # review finding: words
    assert rej["v2"]["ba"]["structure: two sentences in the first line"]["primary"] >= 0.8
    rej = {r["name"]: r for r in v["rejected"]["ps_q_excl"]}
    assert min(rej["v2"]["ba"]['component only: "!" in the P.S. (ps_exclaim\'s reference regex)'].values()) >= 0.99
    assert v["rule_versions"]["greet_question: all notes (L3 as first specified)"]["parent only: a greeting"] >= 0.8
    assert v["rule_versions"]["informal_lower: at least one component, greeting not required"][
        "component only: an informal greeting"] >= 0.8
    # without the counterfactual gate the case-sensitive literal lists the L5 cue; with it, it does not
    lit = "component only, case-sensitive literal: starts with lower-case hey / hiya / yo"
    assert v["rule_versions"]["informal_lower: no counterfactual gate (primary)"][lit] >= 0.99
    assert max(v["shortcuts"]["informal_lower"][lit].values()) < 0.8


# ---------------------------------------------------------------- privacy
def test_find_pairings():
    cal = {"ep999": {"mains": [{"cue": "weekday"}]}}
    assert exp.find_pairings("ep999 weekday\nep999 is fine\nweekday alone", cal) == [(1, "ep999")]
    assert exp.find_pairings("x ft_screen/planted_1 quote", {}, {"ft_screen/planted_1": "quote"}) == [(1, "ft_screen/planted_1")]


TRACKED = ROOT / "results" / "blackbox_1112" / "exp_f"
PRIVATE_CAL = ROOT / "results" / "private_1112" / "exp_f" / "calibration.json"


@pytest.mark.skipif(not PRIVATE_CAL.exists(), reason="no private calibration list (run build first)")
def test_tracked_outputs_pair_no_shipped_episode_or_source_with_its_cue():
    cal = json.loads(PRIVATE_CAL.read_text())
    sources = {m["source"]: m["cue"] for e in cal.values() for m in e["mains"]}
    files = [p for p in TRACKED.rglob("*") if p.is_file()] + [ROOT / "scripts" / "exp_f_listing.py",
                                                              ROOT / "shifthunt" / "listing_cues.py",
                                                              Path(__file__), ROOT / "tests" / "test_listing_cues.py"]
    for path in files:
        hits = exp.find_pairings(path.read_text(encoding="utf-8"), cal, sources)
        assert not hits, f"{path.relative_to(ROOT)}: {len(hits)} line(s) pair a shipped id with its cue"


@pytest.mark.skipif(not PRIVATE_CAL.exists(), reason="no private calibration list (run build first)")
def test_the_fake_bank_copies_nothing_from_the_shipped_episodes():
    """The test fixture is a seeded draw: no aligned set, (topic pair, cue) or (probe index, cue, sign) of it
    equals a shipped one (nothing is printed: the assertion messages name only the fake ids)."""
    cal = json.loads(PRIVATE_CAL.read_text())
    shipped_sets = {frozenset(e["aligned"]) for e in cal.values()}
    shipped_topics = {(frozenset(m["topics"]), m["cue"]) for e in cal.values() for m in e["mains"]}
    shipped_slots = {(m["probe"], m["cue"], m["sign"]) for e in cal.values() for m in e["mains"]}
    hits = []      # booleans only, so a failure prints nothing from the private list
    for ep, (_, aligned, probes) in FAKE.items():
        hits.append((ep, "aligned set", frozenset(aligned) in shipped_sets))
        for j, (kind, cue, sign, _, topics) in enumerate(probes):
            if kind == "planted":
                hits.append((ep, f"probe {j} topics and cue", (frozenset(topics), cue) in shipped_topics))
                hits.append((ep, f"probe {j} slot, cue and sign", (j, cue, sign) in shipped_slots))
    bad = [(ep, what) for ep, what, hit in hits if hit]
    assert bad == [] and not set(FAKE) & set(cal)


def test_committed_validation_report_passes_and_admits_every_cue():
    text = (TRACKED / "VALIDATION.md").read_text(encoding="utf-8")
    assert "Overall: **PASS**." in text
    for cue in exp.CUES:
        row = next(line for line in text.splitlines() if line.startswith(f"| `{cue}` | {exp.CUES[cue]['level']} |"))
        assert row.rstrip().endswith("| yes |"), cue
    shortcut_rows = [line for line in text.split("## Shortcut table")[1].split("## Automatic shortcut scan")[0].splitlines()
                     if line.startswith("| `")]
    assert shortcut_rows and not any("≥ 0.8" in line for line in shortcut_rows)
    auto_rows = [line for line in text.split("## Automatic shortcut scan")[1].split("Equivalent descriptions")[0]
                 .splitlines() if line.startswith("| `")]
    assert auto_rows and not any("**≥ 0.8**" in line for line in auto_rows)
    for cue in exp.CUES:
        if exp.CUES[cue]["level"] in exp.SHORTCUT_LEVELS:
            assert any(line.startswith(f"| `{cue}` |") for line in shortcut_rows), cue
