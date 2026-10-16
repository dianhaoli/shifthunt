"""Generate free-flowing base paragraphs for the free-text substrate (build time, Claude API).

    python scripts/freetext_generate.py --out .cache/freetext/raw.jsonl --per-topic 260 --model claude-haiku-5-5

Each request asks for BATCH paragraphs about one hobby in a canonical form that the deterministic feature
edits in shifthunt/freetext.py rely on (he/him only, present tense, American spelling, no contractions,
numbers as words, no ! ? " ( ) # : ; or digits). freetext.py re-checks every paragraph and drops the
ones that break the form, so this script only asks; it never certifies. The API key is read from the
environment or from a .env file given with --env (never printed or written anywhere).
Appends one JSON line per paragraph {topic, text, req} and one usage line per request to <out>.usage.
"""
import argparse
import json
import os
import random
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from shifthunt import textgen as tg  # noqa: E402

BATCH = 20
THEMES = ["his job", "a coworker", "his sister", "his parents", "the weather", "money worries",
          "a recent move", "his dog", "his health", "a long commute", "his neighborhood", "an old friend",
          "a holiday trip", "his landlord", "school memories", "a broken car", "cooking dinner",
          "his kids", "a noisy flat upstairs", "the news", "a new phone", "his garden shed",
          "a family wedding", "night shifts", "a cold he caught", "his grandfather", "local politics",
          "a part-time course", "saving for a house", "his favorite cafe"]
STYLES = ["matter-of-fact", "wry", "warm", "slightly melancholy", "upbeat", "rambling", "dry",
          "reflective", "chatty", "understated"]
SPELL = ["color", "favorite", "neighbor", "center", "organizes", "realizes", "gray", "theater", "traveled", "flavor",
         "neighborhood", "favorite"]
CONTRACT = ["does not", "do not", "is not", "cannot", "did not", "will not", "it is", "that is", "he is"]
NUMBERS = ["two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "twelve", "twenty"]

PROMPT = """Write {n} different short paragraphs, each about a man whose hobby is {topic}. Make them varied
and natural, like real people writing about someone they know: each paragraph should clearly be about
{topic} (mention at least two concrete things specific to {topic}), but also weave in one or two other
parts of his life, for example: {themes}. Vary the tone ({styles}) and the sentence structure; do not reuse
opening words or phrasings across paragraphs.

Hard rules for EVERY paragraph (they are checked automatically):
- 35 to 50 words, 3 to 5 sentences, one paragraph, plain ASCII.
- Refer to the man only as he/him/his/himself; never give him a name; no I/me/my/we/you.
- Never use the words she, her, hers or herself (other people can appear, e.g. "his sister", but never
  refer back to them with a pronoun).
- Present tense.
- Every sentence ends with a period. No question marks, exclamation marks, quotation marks, parentheses,
  colons, semicolons, dashes, ellipses or hashtags.
- No days of the week, no greetings, no sign-offs, no names of people.
- Do not mention any of these other hobbies: {others}.

Return only a JSON array of {n} strings, in this order, nothing else."""


def load_key(env_path):
    if os.environ.get("ANTHROPIC_API_KEY"):
        return os.environ["ANTHROPIC_API_KEY"]
    for line in Path(env_path).read_text().splitlines():
        k, _, v = line.partition("=")
        if k.strip().removeprefix("export ").strip() == "ANTHROPIC_API_KEY":
            return v.strip().strip('"').strip("'")
    sys.exit("no ANTHROPIC_API_KEY in environment or --env file")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--per-topic", type=int, default=260)
    ap.add_argument("--model", default="claude-haiku-5-5")
    ap.add_argument("--env", default=Path(".env"))
    ap.add_argument("--jobs", type=int, default=6)
    ap.add_argument("--topics", default=",".join(tg.TOPIC_NAMES))
    args = ap.parse_args()
    import anthropic
    client = anthropic.Anthropic(api_key=load_key(args.env), max_retries=4)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    topics = args.topics.split(",")
    reqs = [(t, i) for t in topics for i in range(-(-args.per_topic // BATCH))]
    lock = threading.Lock()
    usage_path = Path(str(args.out) + ".usage")

    def one(req):
        topic, i = req
        rng = random.Random(f"gen:{topic}:{i}")
        prompt = PROMPT.format(n=BATCH, topic=topic, themes=", ".join(rng.sample(THEMES, 6)),
                               styles=", ".join(rng.sample(STYLES, 4)),
                               others=", ".join(t for t in tg.TOPIC_NAMES if t != topic))
        for attempt in range(3):
            msg = client.messages.create(model=args.model, max_tokens=6000, thinking={"type": "disabled"},
                                         messages=[{"role": "user", "content": prompt}])
            text = "".join(b.text for b in msg.content if b.type == "text").strip()
            s, e = text.find("["), text.rfind("]")
            try:
                paras = json.loads(text[s:e + 1])
                assert isinstance(paras, list) and all(isinstance(p, str) for p in paras)
            except Exception:
                paras = None
            with lock:
                with open(usage_path, "a") as f:
                    f.write(json.dumps({"req": f"{topic}:{i}", "attempt": attempt, "model": args.model,
                                        "input": msg.usage.input_tokens, "output": msg.usage.output_tokens,
                                        "ok": paras is not None}) + "\n")
                if paras is not None:
                    with open(args.out, "a") as f:
                        for p in paras:
                            f.write(json.dumps({"topic": topic, "text": p.strip(), "req": i}) + "\n")
                    return len(paras)
        return 0

    with ThreadPoolExecutor(args.jobs) as ex:
        n = sum(ex.map(one, reqs))
    print(f"{n} paragraphs from {len(reqs)} requests")


if __name__ == "__main__":
    main()
