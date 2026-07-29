"""Generation-only smoke test for Phase 8 Step 8.1's pre-generation topic pass.

Calls the same functions main.py wires together (`_select_topic_pregen` ->
`propose_topics` -> `find_title_collision`) against a real site's live
catalog, with NO article body generation and NO publish.

Usage: .venv/Scripts/python.exe scripts/smoke-topic-pregen.py --site gardening
"""
import argparse
import logging
import sys
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

from openclaw.config import Config
from openclaw.main import _activate_site, _select_topic_pregen
from openclaw.publisher import get_category_names, get_site_name, list_recent_post_titles

parser = argparse.ArgumentParser()
parser.add_argument("--site", required=True)
args = parser.parse_args()

_activate_site(args.site)
cfg = Config.load()
site_host = urlparse(cfg.WP_BASE_URL).hostname

recent_titles = list_recent_post_titles(limit=1000)
print(f"Loaded {len(recent_titles)} existing title(s) from {site_host}.")

topic = _select_topic_pregen(
    category=None,
    recent_titles=recent_titles,
    wp_categories=tuple(get_category_names()),
    site_name=get_site_name(),
    site_host=site_host,
    trending_signals=None,
)
print("COMMITTED TOPIC:", topic)
