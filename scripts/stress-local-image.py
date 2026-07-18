"""Stress test for the local Draw Things (Flux) image endpoint.

Runs `openclaw.images.generate_local_image` against a battery of prompts
covering the shapes production actually sends: short/long, various
subject matter, quotes/apostrophes/em-dashes, unicode, empty negative
edge cases. Records latency + success/failure per prompt, saves every
image to `logs/stress-local-image/`, and prints a summary at the end.

Usage:
    python scripts/stress-local-image.py --site gardening
    python scripts/stress-local-image.py --site dogs -n 3

Exits 0 if every attempt returned a valid image; 1 if any failed.
"""

from __future__ import annotations

import argparse
import os
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from openclaw.main import _activate_site  # noqa: E402
from openclaw.config import Config  # noqa: E402
from openclaw.images import generate_local_image  # noqa: E402

_OUTPUT_DIR = Path(__file__).resolve().parent.parent / "logs" / "stress-local-image"

# Prompts intentionally cover the failure surface production actually hits:
# real editorial prompts with punctuation, long compound sentences,
# apostrophes (the failing 2026-07-15 run had one), unicode, and a
# minimal one-liner to isolate steps/latency from prompt complexity.
_PROMPTS: list[tuple[str, str]] = [
    (
        "minimal-baseline",
        "A single ripe tomato on a wooden cutting board, natural window light, landscape.",
    ),
    (
        "editorial-cover-quotes",
        'Create a cinematic 16:9 cover photograph for an editorial article titled '
        '"The pH Problem: Why Your Soil Test\'s Most Important Number Is the One '
        'You\'re Ignoring." Close-up of a paper soil test report on a rustic garden '
        'workbench, a bag of agricultural lime and a rusted garden trowel beside it, '
        'shallow depth of field, warm afternoon light, editorial magazine style, '
        'muted earth palette.',
    ),
    (
        "long-descriptive",
        "Editorial 16:9 landscape photograph in the style of a New York Times magazine "
        "feature: a raised cedar planter box on a small suburban patio at golden hour, "
        "overflowing with tomatoes, basil, and marigolds. A galvanized watering can "
        "sits on the flagstone in the foreground; blurred wooden fence and climbing "
        "roses in the background. Warm side light rakes across the leaves, natural "
        "atmosphere, no people, no text, no logos.",
    ),
    (
        "unicode-and-emdash",
        "A pair of terracotta pots — one with rosemary, one with thyme — arranged "
        "on a sun-warmed stone windowsill overlooking a Provençal courtyard. Soft "
        "diffused morning light, muted olive and ochre palette, landscape framing.",
    ),
    (
        "abstract-concept",
        "A conceptual landscape image representing the invisible life of soil: a "
        "cross-section view of dark, healthy garden soil showing intertwined roots, "
        "earthworms, and fine mycelial threads, dramatic lighting from above, "
        "photorealistic, editorial nature-magazine composition.",
    ),
    (
        "portrait-subject-landscape-frame",
        "A weathered gardener's hands cupping a small pile of finished compost, "
        "shot from above in a landscape 16:9 frame, soft overcast light, blurred "
        "garden beds in the background, warm documentary tone.",
    ),
    (
        "very-short",
        "healthy vegetable garden at dawn",
    ),
    (
        "high-detail-tools",
        "Overhead flat-lay of gardening tools on weathered wood: pruning shears, "
        "twine, terracotta seed pots, a small notebook and pencil, scattered seed "
        "packets, natural window light from the left, editorial 16:9 crop.",
    ),
]


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--site", required=True,
        help="Site slug for env-var activation (e.g. 'gardening'). Only LOCAL_IMAGE_* "
             "vars are actually used, but Config.load() still requires WP_*.",
    )
    p.add_argument(
        "-n", "--iterations", type=int, default=len(_PROMPTS),
        help=f"How many prompts to run (default {len(_PROMPTS)}, the full battery). "
             f"Runs the first N from the prompt list.",
    )
    p.add_argument(
        "--repeat", type=int, default=1,
        help="Run the whole selected battery this many times (default 1). "
             "Use >1 for deeper stress testing.",
    )
    return p.parse_args()


def _fmt_seconds(s: float) -> str:
    return f"{s:.1f}s"


def main() -> int:
    args = _parse_args()
    _activate_site(args.site)
    cfg = Config.load()
    if not cfg.LOCAL_IMAGE_ENABLED or not cfg.LOCAL_IMAGE_BASE_URL:
        print("ERROR: LOCAL_IMAGE_ENABLED must be true and LOCAL_IMAGE_BASE_URL set in .env")
        return 1

    prompts = _PROMPTS[: max(1, min(args.iterations, len(_PROMPTS)))]
    total_runs = len(prompts) * args.repeat

    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    # Clear previous run so success/failure counts by file count are meaningful.
    for p in _OUTPUT_DIR.glob("*.png"):
        p.unlink()

    print(f"base_url    = {cfg.LOCAL_IMAGE_BASE_URL}")
    print(f"battery     = {len(prompts)} prompts × {args.repeat} repeat = {total_runs} runs")
    print(f"output dir  = {_OUTPUT_DIR}")
    print("-" * 72)

    results: list[tuple[str, int, bool, float, int]] = []
    for rep in range(1, args.repeat + 1):
        for idx, (label, prompt) in enumerate(prompts, start=1):
            run_no = (rep - 1) * len(prompts) + idx
            print(
                f"[{run_no}/{total_runs}] rep={rep} label={label!r} "
                f"prompt_len={len(prompt)}",
                flush=True,
            )
            t0 = time.perf_counter()
            image = generate_local_image(prompt, f"{label} test")
            elapsed = time.perf_counter() - t0
            if image is None:
                print(f"    FAIL after {_fmt_seconds(elapsed)}")
                results.append((label, rep, False, elapsed, 0))
                continue
            out_path = _OUTPUT_DIR / f"{run_no:02d}-rep{rep}-{label}.png"
            out_path.write_bytes(image["image_bytes"])
            size_kb = len(image["image_bytes"]) // 1024
            print(f"    OK   {_fmt_seconds(elapsed)}  {size_kb} KB  -> {out_path.name}")
            results.append((label, rep, True, elapsed, len(image["image_bytes"])))

    print("-" * 72)
    successes = [r for r in results if r[2]]
    failures = [r for r in results if not r[2]]
    latencies = [r[3] for r in successes]
    print(f"total       : {len(results)}")
    print(f"success     : {len(successes)}  ({len(successes) / len(results) * 100:.0f}%)")
    print(f"failure     : {len(failures)}")
    if latencies:
        latencies.sort()
        p50 = statistics.median(latencies)
        p95 = latencies[int(len(latencies) * 0.95) - 1] if len(latencies) >= 20 else latencies[-1]
        print(
            f"latency     : min={_fmt_seconds(min(latencies))}  "
            f"p50={_fmt_seconds(p50)}  "
            f"p95={_fmt_seconds(p95)}  "
            f"max={_fmt_seconds(max(latencies))}"
        )
    if failures:
        print("failures:")
        for label, rep, _, elapsed, _size in failures:
            print(f"  - rep={rep} label={label!r} after {_fmt_seconds(elapsed)}")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
