"""Generation-only smoke test for the trending-signal path. No publish."""
import logging
from urllib.parse import urlparse
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

from openclaw.config import Config
from openclaw.generator import generate_article
from openclaw.publisher import (
    list_recent_post_titles,
    list_recent_posts_for_linking,
    get_category_names,
    get_site_name,
)
from openclaw.trends import gather_trending_signals

article = generate_article(
    recent_titles=list_recent_post_titles(),
    categories=get_category_names(),
    site_name=get_site_name(),
    site_host=urlparse(Config.load().WP_BASE_URL).hostname,
    internal_link_candidates=list_recent_posts_for_linking(),
    trending_signals=gather_trending_signals(),
)
print("TITLE:", article["title"])
print("CATEGORY:", article["category"])
print("KEYPHRASE:", article["focus_keyphrase"])
print("SLUG:", article["slug"])
