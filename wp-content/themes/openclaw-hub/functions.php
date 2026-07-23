<?php
/**
 * Openclaw Info Verse Hub (openclaw-hub) — child of openclaw-base.
 *
 * Aggregation-only hub for info-verse.org. Provides the
 * [openclaw_network_feed] shortcode that pulls the latest posts from each of
 * the five subsite REST APIs and renders image + title cards linking out to
 * the real posts. No original post bodies live on the hub.
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

// GA4 measurement ID for the hub (Phase 7 Step 7.3). Undefined = no tracking
// snippet output (see openclaw-base's wp_head hook). Shares the network
// measurement ID with the five pilot subsites so all traffic aggregates into
// one GA4 property; use GA content_group / stream URL filters to split.
define( 'OPENCLAW_GA4_ID', 'G-EMJRNCZR10' );

/**
 * Enqueue the child theme's own style.css. The parent (openclaw-base) only
 * enqueues its own stylesheet by absolute template dir URI, so a block child
 * theme's style.css isn't loaded automatically — WP core doesn't do it for
 * block themes the way it does for classic themes. Depend on 'openclaw-base'
 * so this loads after the parent, letting these rules win on cascade.
 */
add_action( 'wp_enqueue_scripts', function () {
    wp_enqueue_style(
        'openclaw-hub',
        get_stylesheet_directory_uri() . '/style.css',
        [ 'openclaw-base' ],
        wp_get_theme()->get( 'Version' )
    );
}, 20 );

/**
 * Fix wpautop damage in our network feed shortcode's block output.
 *
 * `core/shortcode` blocks in a block theme run `do_shortcode()` on their raw
 * text — but the surrounding render pipeline also runs wpautop on the block
 * result, which inserts `<p>` around inline runs and `<br />` on newlines.
 * When the shortcode returns HTML with block-level children of an `<a>` tag
 * (our grid card layout), wpautop's `<p>` insertion + balancer confuse the
 * DOM: an empty `<p></p>` slips in as the first child of each card `<a>`,
 * stealing grid column 1 and blowing the image out to full width. `<p>` also
 * wraps the visit link.
 *
 * remove_filter('the_content', 'wpautop') doesn't fix this — for block
 * themes, wpautop applies to shortcode block output via a different path.
 * Cleanest fix: strip wpautop's damage post-render on just the shortcode
 * block containing our feed.
 */
add_filter( 'render_block', function ( $block_content, $block ) {
    if ( empty( $block['blockName'] ) || $block['blockName'] !== 'core/shortcode' ) {
        return $block_content;
    }
    if ( strpos( $block_content, 'openclaw-network-feed' ) === false ) {
        return $block_content;
    }
    // Kill empty `<p></p>` and stray `<p>` / `</p>` tags — the shortcode
    // output has ZERO legitimate `<p>` tags of its own except the
    // .openclaw-network-row-blurb one, so we can safely remove wpautop's.
    // First mark the blurb's opening and closing `</p>` with sentinels so
    // the blanket strip below doesn't wipe them, then strip everything
    // else, then swap the sentinels back.
    $block_content = str_replace(
        '<p class="openclaw-network-row-blurb">',
        '###OCH_BLURB_OPEN###',
        $block_content
    );
    // Find the closing </p> that follows the sentinel-opened blurb (up to
    // the next < which is either </p> for our blurb or something wpautop
    // added). We match the shortest run of non-`<` chars, then a `</p>`.
    $block_content = preg_replace(
        '~(###OCH_BLURB_OPEN###[^<]*)</p>~',
        '$1###OCH_BLURB_CLOSE###',
        $block_content
    );
    $block_content = preg_replace( '/<p>\s*/', '', $block_content );
    $block_content = preg_replace( '/\s*<\/p>/', '', $block_content );
    $block_content = preg_replace( '#<br\s*/?>#', '', $block_content );
    $block_content = str_replace(
        [ '###OCH_BLURB_OPEN###', '###OCH_BLURB_CLOSE###' ],
        [ '<p class="openclaw-network-row-blurb">', '</p>' ],
        $block_content
    );
    return $block_content;
}, 10, 2 );

/**
 * The five subsites the hub aggregates, in display order.
 *
 * `label`  = human name shown as the row heading. Matches each subsite's
 *            actual `blogname` option after the 2026-07-22 brand rename to
 *            the "<Topic> Info Verse" pattern.
 * `blurb`  = one-line site description shown in the row header under the
 *            label. Kept short (under ~130 chars) so it fits on one line
 *            at desktop widths and wraps to two on mobile.
 * `origin` = the deployed subsite HTTPS origin, used both for the RSS feed
 *            fetch and to construct the outbound "Visit site" link. Kept
 *            in sync with openclaw/deploy.py::_SLUG_TO_DOMAIN.
 */
function openclaw_hub_subsites(): array {
    return [
        [
            'slug'   => 'techtools',
            'label'  => 'Tech Tools Info Verse',
            'blurb'  => 'Practical SaaS, AI, and productivity writing for founders, freelancers, and operators who live in software.',
            'origin' => 'https://techtools.info-verse.org',
        ],
        [
            'slug'   => 'gardening',
            'label'  => 'Gardening Info Verse',
            'blurb'  => 'Home-gardening editorial for hobbyists — plants, soil, pests, and design, from windowsill to backyard border.',
            'origin' => 'https://gardening.info-verse.org',
        ],
        [
            'slug'   => 'dogs',
            'label'  => 'Dog Info Verse',
            'blurb'  => 'Enthusiast writing on breed history, behavior, health, and training — for real dogs and the people who own them.',
            'origin' => 'https://dogs.info-verse.org',
        ],
        [
            'slug'   => 'boardgames',
            'label'  => 'Boardgames Info Verse',
            'blurb'  => 'Tabletop editorial for players who already own a shelf of games — mechanics, strategy, and the history of the medium.',
            'origin' => 'https://boardgames.info-verse.org',
        ],
        [
            'slug'   => 'coffee',
            'label'  => 'Coffee Info Verse',
            'blurb'  => 'Home-brewing editorial for pour-over converts, espresso hobbyists, and French-press loyalists leveling up their cup.',
            'origin' => 'https://coffee.info-verse.org',
        ],
    ];
}

/**
 * Fetch the latest `$count` posts from a single subsite by RSS.
 *
 * The subsites are static Staatic exports served from GitHub Pages, so the
 * dynamic WP REST collection endpoint (/wp-json/wp/v2/posts) doesn't exist
 * in the export tree — but /feed/ does, and WordPress bakes it out with
 * title + link + pubDate per item. Featured images aren't inline in the
 * feed, so we resolve each post's og:image separately (with its own
 * long-lived transient) via openclaw_hub_fetch_og_image().
 *
 * Returns a list of ['title', 'link', 'image_url'] items. Cached for 6 hours
 * per (origin, count) via a site transient so hub renders don't hammer the
 * subsite feeds on every request.
 *
 * Fail-soft: any network / parse error returns an empty array and logs via
 * error_log(). The caller renders an empty-state stub for that row.
 */
function openclaw_hub_fetch_subsite_posts( string $origin, int $count = 3 ): array {
    $count      = max( 1, min( 12, $count ) );
    $cache_key  = 'openclaw_hub_feed_' . md5( $origin . '|' . $count );
    $cache_ttl  = 6 * HOUR_IN_SECONDS;

    $cached = get_site_transient( $cache_key );
    if ( is_array( $cached ) ) {
        return $cached;
    }

    $url = trailingslashit( $origin ) . 'feed/';
    $res = wp_remote_get( $url, [
        'timeout'     => 8,
        'redirection' => 3,
        'user-agent'  => 'openclaw-hub-feed/1.0',
    ] );

    if ( is_wp_error( $res ) ) {
        error_log( '[openclaw-hub] feed fetch failed for ' . $origin . ': ' . $res->get_error_message() );
        set_site_transient( $cache_key, [], 15 * MINUTE_IN_SECONDS );
        return [];
    }

    $code = (int) wp_remote_retrieve_response_code( $res );
    $body = wp_remote_retrieve_body( $res );
    if ( $code < 200 || $code >= 300 || $body === '' ) {
        error_log( '[openclaw-hub] feed non-200 for ' . $origin . ': HTTP ' . $code );
        set_site_transient( $cache_key, [], 15 * MINUTE_IN_SECONDS );
        return [];
    }

    // Strip XML 1.0 invalid control characters before parsing so a stray
    // byte in one post's <content:encoded> body doesn't torpedo the whole
    // feed. Seen 2026-07-22 on techtools where a 0x19 (END OF MEDIUM) in a
    // generated article body made SimpleXML abort with "PCDATA invalid Char
    // value 25" and return an empty item list.
    $body = preg_replace( '/[\x00-\x08\x0B\x0C\x0E-\x1F]/', '', $body );

    // Suppress libxml warnings from the odd malformed feed; check errors after.
    $prev_use_errors = libxml_use_internal_errors( true );
    $xml = simplexml_load_string( $body );
    libxml_clear_errors();
    libxml_use_internal_errors( $prev_use_errors );

    if ( ! $xml || ! isset( $xml->channel->item ) ) {
        error_log( '[openclaw-hub] feed parse failed for ' . $origin );
        set_site_transient( $cache_key, [], 15 * MINUTE_IN_SECONDS );
        return [];
    }

    $items = [];
    $seen  = 0;
    foreach ( $xml->channel->item as $item ) {
        if ( $seen >= $count ) {
            break;
        }
        $title = (string) $item->title;
        $link  = (string) $item->link;
        if ( $title === '' || $link === '' ) {
            continue;
        }
        $items[] = [
            'title'     => html_entity_decode( wp_strip_all_tags( $title ), ENT_QUOTES, 'UTF-8' ),
            'link'      => $link,
            'image_url' => openclaw_hub_fetch_og_image( $link ),
        ];
        $seen++;
    }

    set_site_transient( $cache_key, $items, $cache_ttl );
    return $items;
}

/**
 * Resolve a post's featured image by scraping <meta property="og:image">
 * from the post page. Cached for 30 days per URL — featured images don't
 * change once a post is published, so the long TTL means at most one lookup
 * per post ever hits the subsite.
 *
 * Fail-soft: any error returns '' (no image), which the card template
 * renders as a plain slate placeholder tile.
 */
function openclaw_hub_fetch_og_image( string $post_url ): string {
    $cache_key = 'openclaw_hub_og_' . md5( $post_url );
    $cached    = get_site_transient( $cache_key );
    if ( is_string( $cached ) ) {
        return $cached;
    }

    $res = wp_remote_get( $post_url, [
        'timeout'     => 8,
        'redirection' => 3,
        'user-agent'  => 'openclaw-hub-feed/1.0',
    ] );

    if ( is_wp_error( $res ) ) {
        set_site_transient( $cache_key, '', HOUR_IN_SECONDS );
        return '';
    }
    $code = (int) wp_remote_retrieve_response_code( $res );
    if ( $code < 200 || $code >= 300 ) {
        set_site_transient( $cache_key, '', HOUR_IN_SECONDS );
        return '';
    }

    $html = wp_remote_retrieve_body( $res );
    // Only need to look at the <head>; cheaper regex if we truncate.
    $head_end = stripos( $html, '</head>' );
    if ( $head_end !== false ) {
        $html = substr( $html, 0, $head_end );
    }

    $image_url = '';
    if ( preg_match( '/<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']/i', $html, $m ) ) {
        $image_url = trim( $m[1] );
    } elseif ( preg_match( '/<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']/i', $html, $m ) ) {
        // meta attributes emitted in reverse order.
        $image_url = trim( $m[1] );
    }

    set_site_transient( $cache_key, $image_url, 30 * DAY_IN_SECONDS );
    return $image_url;
}

/**
 * [openclaw_network_feed count="3"] — renders 5 rows (one per subsite),
 * each with `count` post cards linking directly to the subsite article.
 *
 * Cards intentionally show only the image + title + outbound link — no
 * excerpts, no meta. Per user: "The hub posts shouldn't have any descriptions
 * or anything aside from the cards on the home page. They should just link
 * to the website."
 */
function openclaw_hub_network_feed_shortcode( array|string $atts = [] ): string {
    $atts  = shortcode_atts( [ 'count' => 1 ], is_array( $atts ) ? $atts : [] );
    $count = max( 1, (int) $atts['count'] );

    $subsites = openclaw_hub_subsites();
    ob_start();
    ?>
    <section class="openclaw-network-feed">
        <?php foreach ( $subsites as $site ) :
            $posts = openclaw_hub_fetch_subsite_posts( $site['origin'], $count );
            ?>
            <div class="openclaw-network-row" data-slug="<?php echo esc_attr( $site['slug'] ); ?>">
                <header class="openclaw-network-row-header">
                    <div class="openclaw-network-row-heading">
                        <h2 class="openclaw-network-row-title"><?php echo esc_html( $site['label'] ); ?></h2>
                        <?php if ( ! empty( $site['blurb'] ) ) : ?>
                            <p class="openclaw-network-row-blurb"><?php echo esc_html( $site['blurb'] ); ?></p>
                        <?php endif; ?>
                    </div>
                    <a class="openclaw-network-row-visit" href="<?php echo esc_url( $site['origin'] ); ?>/" rel="noopener">
                        <?php esc_html_e( 'Visit site →', 'openclaw-hub' ); ?>
                    </a>
                </header>

                <?php if ( empty( $posts ) ) : ?>
                    <div class="openclaw-network-row-empty">
                        <?php
                        printf(
                            /* translators: %s: subsite label */
                            esc_html__( 'Feed for %s temporarily unavailable.', 'openclaw-hub' ),
                            esc_html( $site['label'] )
                        );
                        ?>
                    </div>
                <?php else : ?>
                    <div class="openclaw-network-grid">
                        <?php foreach ( $posts as $post ) : ?>
                            <a class="openclaw-network-card" href="<?php echo esc_url( $post['link'] ); ?>" rel="noopener">
                                <div class="openclaw-network-card-image">
                                    <?php if ( $post['image_url'] !== '' ) : ?>
                                        <img
                                            src="<?php echo esc_url( $post['image_url'] ); ?>"
                                            alt=""
                                            decoding="async"
                                            referrerpolicy="no-referrer-when-downgrade"
                                        />
                                    <?php endif; ?>
                                </div>
                                <div class="openclaw-network-card-body">
                                    <h3 class="openclaw-network-card-title"><?php echo esc_html( $post['title'] ); ?></h3>
                                </div>
                            </a>
                        <?php endforeach; ?>
                    </div>
                <?php endif; ?>
            </div>
        <?php endforeach; ?>
    </section>
    <?php
    $out = (string) ob_get_clean();
    // Collapse newlines (and their trailing indentation) to single spaces
    // so WordPress's wpautop filter — which triggers on newlines inside
    // shortcode output — can't insert empty <p></p> nodes into block-level
    // children of block-level parents. Without this, wpautop reads the
    // newlines between our multi-line <img> attributes and injects a
    // paragraph as the first child of each card <a>, stealing grid column 1
    // and exploding the image to full width. Then also collapse `>[ws]<`
    // to `><` so no tag-adjacent whitespace remains for downstream filters.
    $out = (string) preg_replace( '/[\r\n]+\s*/', ' ', $out );
    return (string) preg_replace( '/>\s+</', '><', $out );
}
add_shortcode( 'openclaw_network_feed', 'openclaw_hub_network_feed_shortcode' );

/**
 * Convenience CLI hook: `wp openclaw hub_flush_cache` clears every
 * cached subsite feed so the next page render (or Staatic export) refetches.
 * Called by openclaw.deploy::refresh_hub before triggering the export.
 */
if ( defined( 'WP_CLI' ) && WP_CLI ) {
    WP_CLI::add_command( 'openclaw hub_flush_cache', function () {
        global $wpdb;
        // Wipe every openclaw_hub_feed_ / openclaw_hub_og_ transient. Site
        // transients are stored as _site_transient_<key> in wp_sitemeta on
        // multisite (or wp_options on single-site). Delete directly by
        // meta_key LIKE so we don't need to reconstruct URL-hashed keys.
        $prefixes = [ 'feed_', 'og_' ];
        $deleted  = 0;
        foreach ( $prefixes as $p ) {
            $like_meta   = $wpdb->esc_like( '_site_transient_openclaw_hub_' . $p ) . '%';
            $like_option = $wpdb->esc_like( '_site_transient_openclaw_hub_' . $p ) . '%';
            if ( is_multisite() ) {
                $deleted += (int) $wpdb->query( $wpdb->prepare(
                    "DELETE FROM {$wpdb->sitemeta} WHERE meta_key LIKE %s",
                    $like_meta
                ) );
                $deleted += (int) $wpdb->query( $wpdb->prepare(
                    "DELETE FROM {$wpdb->sitemeta} WHERE meta_key LIKE %s",
                    $wpdb->esc_like( '_site_transient_timeout_openclaw_hub_' . $p ) . '%'
                ) );
            } else {
                $deleted += (int) $wpdb->query( $wpdb->prepare(
                    "DELETE FROM {$wpdb->options} WHERE option_name LIKE %s",
                    $like_option
                ) );
                $deleted += (int) $wpdb->query( $wpdb->prepare(
                    "DELETE FROM {$wpdb->options} WHERE option_name LIKE %s",
                    $wpdb->esc_like( '_site_transient_timeout_openclaw_hub_' . $p ) . '%'
                ) );
            }
        }
        WP_CLI::success( sprintf( 'Cleared %d hub cache row(s).', $deleted ) );
    } );
}
