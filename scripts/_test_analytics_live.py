import logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

from dotenv import load_dotenv
load_dotenv()

from openclaw import analytics

host = "catfancast.com"
cache_path = analytics._cache_path(host)
print("Cache path:", cache_path)
if cache_path.exists():
    cache_path.unlink()
    print("Deleted existing cache to force a live fetch attempt.")

result = analytics.gather_analytics_signals(host, site_url="https://catfancast.com/")
print("RESULT:", result)

msg = analytics.build_analytics_message(result)
print("ANALYTICS MESSAGE INJECTED INTO PROMPT (empty means nothing is injected):")
print(repr(msg))
