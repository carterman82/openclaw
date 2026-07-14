"""Phase 3.9 smoke test: prove the local Draw Things image API works.

Usage:
    python scripts/smoke-local-image.py

Reads LOCAL_IMAGE_ENABLED and LOCAL_IMAGE_BASE_URL from .env. Calls
`openclaw.images.generate_local_image` directly (bypassing the full publish
pipeline) with a short fixed test prompt, saves the resulting PNG to
logs/smoke-local-image.png, and prints PASS/FAIL + latency. Run this in
isolation before a full `python -m openclaw post` run, so a hang is easy to
diagnose without a half-finished article run in the way.

Exits 0 on success, 1 on failure.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

# Allow importing openclaw when running from the project root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from openclaw.config import Config  # noqa: E402
from openclaw.images import generate_local_image  # noqa: E402

_TEST_PROMPT = (
    "A single orange tabby cat sitting on a sunlit windowsill, looking outside, "
    "soft natural light, cozy home interior, landscape composition, photographic "
    "style, no text or watermark."
)
_OUTPUT_PATH = Path(__file__).resolve().parent.parent / "logs" / "smoke-local-image.png"


def main() -> int:
    cfg = Config.load()
    if not cfg.LOCAL_IMAGE_ENABLED or not cfg.LOCAL_IMAGE_BASE_URL:
        print(
            "ERROR: LOCAL_IMAGE_ENABLED must be true and LOCAL_IMAGE_BASE_URL set in .env"
        )
        return 1

    print(f"base_url = {cfg.LOCAL_IMAGE_BASE_URL}")
    print(f"prompt   = {_TEST_PROMPT!r}")

    t0 = time.perf_counter()
    image = generate_local_image(_TEST_PROMPT, "orange tabby cat on a sunlit windowsill")
    latency = time.perf_counter() - t0
    print(f"latency  = {latency:.2f}s")

    if image is None:
        print("FAIL: generate_local_image returned None (see WARNING log above).")
        return 1

    _OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    _OUTPUT_PATH.write_bytes(image["image_bytes"])
    print(f"PASS: wrote {len(image['image_bytes'])} bytes to {_OUTPUT_PATH}")
    print("Open the file and confirm it's a landscape, on-topic, uncorrupted image.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
