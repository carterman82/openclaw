#!/usr/bin/env bash
# create-hub-pages.sh — bootstraps the About / Privacy / Contact pages on the
# hub subsite (blog_id 7). Idempotent: existing pages with the same slug are
# skipped. Uses `wp-cli` directly since the hub doesn't run the openclaw
# agent and therefore has no HUB_WP_* application password.
set -euo pipefail

URL=hub.localhost:8088
CONTACT_EMAIL=info.verse.real@gmail.com

wp_run() { docker compose run --rm wpcli "$@"; }

page_exists() {
    local slug="$1"
    wp_run post list --post_type=page --name="$slug" --format=count --url="$URL" 2>/dev/null | tail -n 1
}

create_page() {
    local slug="$1"; local title="$2"; local content="$3"
    if [ "$(page_exists "$slug")" != "0" ]; then
        echo "[skip] /$slug/ already exists"
        return
    fi
    wp_run post create \
        --post_type=page \
        --post_status=publish \
        --post_title="$title" \
        --post_name="$slug" \
        --post_content="$content" \
        --url="$URL" >/dev/null
    echo "[create] /$slug/"
}

ABOUT='<p>Info Verse is a network of independent, single-topic editorial sites. Each site in the network covers one subject in depth rather than many subjects shallowly — articles are researched and written to be genuinely useful to someone dealing with the specific problem in front of them, not to hit a keyword quota.</p><p>This hub aggregates the latest work from every site in the network. Follow the cards on the home page to read individual articles.</p><p>Have a correction, a topic suggestion, or feedback? See the <a href="/contact/">Contact</a> page.</p>'

PRIVACY='<p>This Privacy Policy explains what data the Info Verse network collects from visitors and how it is used. It applies to info-verse.org and every subsite in the network.</p><h2>Analytics</h2><p>We use Google Analytics (GA4) to understand how visitors use the network — which pages are read, how people arrive, and general audience trends. Google Analytics uses cookies and similar technologies to collect this information. No personally identifying information is collected by us through this process. See <a href="https://policies.google.com/privacy" rel="noopener" target="_blank">Google&#8217;s Privacy Policy</a> for details.</p><h2>Advertising</h2><p>Sites in the network may display ads served by Google AdSense. Google and its partners may use cookies to serve ads based on a visitor&#8217;s prior visits to this and other websites. You can opt out of personalized advertising at <a href="https://adssettings.google.com" rel="noopener" target="_blank">Google Ads Settings</a>.</p><h2>Cookies</h2><p>Cookies set by the analytics and advertising services described above are used to distinguish visitors and, where applicable, personalize ads. You can disable cookies through your browser settings.</p><h2>Third-Party Links</h2><p>The hub links out to articles on the network subsites and, from those articles, to external sources. We are not responsible for the content or privacy practices of external sites.</p><h2>Data We Don&#8217;t Collect</h2><p>We do not require account registration to read this network, and we do not sell visitor data to third parties.</p><h2>Contact</h2><p>Questions about this policy can be sent to <a href="mailto:'"$CONTACT_EMAIL"'">'"$CONTACT_EMAIL"'</a>.</p>'

CONTACT='<p>Corrections, topic suggestions, or general feedback about anything in the Info Verse network? Send it to <a href="mailto:'"$CONTACT_EMAIL"'">'"$CONTACT_EMAIL"'</a>.</p><p>One inbox covers every site in the network. We read every message, though we can&#8217;t guarantee a reply to every one.</p>'

create_page "about"   "About"          "$ABOUT"
create_page "privacy" "Privacy Policy" "$PRIVACY"
create_page "contact" "Contact"        "$CONTACT"
