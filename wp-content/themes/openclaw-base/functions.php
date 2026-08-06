<?php
/**
 * Openclaw Base — parent theme functions.
 *
 * Registers image sizes, image-size names for the editor, block patterns, the
 * [openclaw_related_posts] and [openclaw_explore_categories] shortcodes, and
 * hooks the_content to auto-inject a table of contents on articles with 3+ H2s.
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

/**
 * Theme setup: image sizes + editor styles.
 */
function openclaw_base_setup(): void {
    add_theme_support( 'post-thumbnails' );
    add_theme_support( 'title-tag' );
    add_theme_support( 'responsive-embeds' );
    add_theme_support( 'html5', [ 'search-form', 'comment-form', 'comment-list', 'gallery', 'caption', 'style', 'script' ] );
    add_theme_support( 'custom-logo', [
        'height'      => 96,
        'width'       => 320,
        'flex-height' => true,
        'flex-width'  => true,
    ] );

    // 16:9 sizes across the board.
    add_image_size( 'openclaw-hero',  1600, 900, true );
    add_image_size( 'openclaw-card',   480, 270, true );
    add_image_size( 'openclaw-thumb',  240, 135, true );

    add_editor_style( 'style.css' );
}
add_action( 'after_setup_theme', 'openclaw_base_setup' );

/**
 * Expose the custom image sizes to the block editor size dropdown.
 */
function openclaw_base_image_size_names( array $sizes ): array {
    return array_merge( $sizes, [
        'openclaw-hero'  => __( 'Openclaw Hero (16:9)', 'openclaw-base' ),
        'openclaw-card'  => __( 'Openclaw Card (16:9)', 'openclaw-base' ),
        'openclaw-thumb' => __( 'Openclaw Thumb (16:9)', 'openclaw-base' ),
    ] );
}
add_filter( 'image_size_names_choose', 'openclaw_base_image_size_names' );

/**
 * Front-end asset loading. Parent style is enqueued here; child themes stack via
 * wp_get_theme()->get_stylesheet_uri() automatically.
 */
function openclaw_base_enqueue(): void {
    wp_enqueue_style(
        'openclaw-base',
        get_template_directory_uri() . '/style.css',
        [],
        wp_get_theme( 'openclaw-base' )->get( 'Version' )
    );

    // Google Fonts: child themes override the CSS font-family strings in their
    // own theme.json, and can swap the Google Fonts stylesheet URL entirely by
    // hooking the `openclaw_base_google_fonts_url` filter from their functions.php.
    // The default pair (Inter Tight + Space Grotesk) covers openclaw-techtools
    // and any child that doesn't set the filter.
    $fonts_url = apply_filters(
        'openclaw_base_google_fonts_url',
        'https://fonts.googleapis.com/css2?family=Inter+Tight:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap'
    );
    wp_enqueue_style( 'openclaw-base-fonts', $fonts_url, [], null );
}
add_action( 'wp_enqueue_scripts', 'openclaw_base_enqueue' );

/**
 * GA4 measurement snippet. Child themes define OPENCLAW_GA4_ID with their own
 * per-subsite property ID; a child theme that doesn't define it just gets no
 * output — no error, no fallback tracking ID.
 */
function openclaw_base_ga4_snippet(): void {
    if ( ! defined( 'OPENCLAW_GA4_ID' ) || ! OPENCLAW_GA4_ID ) {
        return;
    }
    $id = esc_js( OPENCLAW_GA4_ID );
    ?>
<script async src="https://www.googletagmanager.com/gtag/js?id=<?php echo esc_attr( $id ); ?>"></script>
<script>
window.dataLayer = window.dataLayer || [];
function gtag(){dataLayer.push(arguments);}
gtag('js', new Date());
gtag('config', '<?php echo $id; ?>');
</script>
    <?php
}
add_action( 'wp_head', 'openclaw_base_ga4_snippet', 1 );

/**
 * AdSense verification / Auto Ads script. One publisher ID covers the whole
 * account, so — unlike OPENCLAW_GA4_ID — OPENCLAW_ADSENSE_ID is defined once
 * here in the parent theme rather than per child theme. Undefined = no
 * output, same fail-soft pattern as the GA4 snippet.
 *
 * Emits both the async loader script AND the <meta name="google-adsense-account">
 * ownership-verification tag. AdSense's application review checks for the meta
 * tag specifically; the loader script is what runs ads once approved.
 */
define( 'OPENCLAW_ADSENSE_ID', 'ca-pub-5175472694671499' );

function openclaw_base_adsense_snippet(): void {
    if ( ! defined( 'OPENCLAW_ADSENSE_ID' ) || ! OPENCLAW_ADSENSE_ID ) {
        return;
    }
    $id = esc_attr( OPENCLAW_ADSENSE_ID );
    ?>
<meta name="google-adsense-account" content="<?php echo $id; ?>">
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=<?php echo $id; ?>" crossorigin="anonymous"></script>
    <?php
}
add_action( 'wp_head', 'openclaw_base_adsense_snippet', 1 );

/**
 * Google Search Console site-ownership verification. Each subdomain must be
 * added to GSC as its own property; when a child theme defines
 * OPENCLAW_GSC_VERIFICATION with the verification token from GSC, this action
 * emits the matching <meta> tag. Undefined = no output. Prefer the DNS TXT
 * record method at the registrar when possible (one record verifies every
 * subdomain); this constant is the per-subsite fallback.
 */
function openclaw_base_gsc_verification_snippet(): void {
    if ( ! defined( 'OPENCLAW_GSC_VERIFICATION' ) || ! OPENCLAW_GSC_VERIFICATION ) {
        return;
    }
    $token = esc_attr( OPENCLAW_GSC_VERIFICATION );
    ?>
<meta name="google-site-verification" content="<?php echo $token; ?>">
    <?php
}
add_action( 'wp_head', 'openclaw_base_gsc_verification_snippet', 1 );

/**
 * Social media OG / meta tags.
 *
 * Each child theme defines OPENCLAW_SOCIAL_PROFILES — an associative array of
 * ['platform_handle' => 'full_url']. This function emits the matching <meta>
 * tags in <head>:
 *   - twitter:site       → @handle (from X URL)
 *   - og:profile:url     → Facebook profile
 *   - al:android/url     → Android deep-link (if android:// present)
 *   - al:ios:url         → iOS deep-link (if ios:// present)
 *   - og:url / og:title  → current page (always emitted)
 *
 * Undefined constant = no output, same fail-soft pattern as GA4 / AdSense.
 */
function openclaw_social_meta_tags(): void {
    $profiles = defined( 'OPENCLAW_SOCIAL_PROFILES' ) ? OPENCLAW_SOCIAL_PROFILES : [];
    if ( empty( $profiles ) ) {
        return;
    }

    // Standard Open Graph required tags.
    ?>
<meta property="og:url" content="<?php echo esc_attr( esc_url( home_url( add_filter( 'request_uri', '__return_empty_string' ) ) ) ); ?>">
<meta property="og:title" content="<?php echo esc_attr( wp_get_document_title() ); ?>">
    <?php

    // Platform-specific tags.
    foreach ( $profiles as $handle => $url ) {
        if ( stripos( $handle, 'x.com' ) !== false || stripos( $handle, 'twitter.com' ) !== false ) {
            $screen_name = trim( $handle, '@' );
            $screen_name = str_replace( [ 'https://x.com/', 'https://twitter.com/' ], '', $screen_name );
            ?>
<meta name="twitter:site" content="@<?php echo esc_attr( $screen_name ); ?>">
            <?php
        }
        if ( stripos( $handle, 'facebook.com' ) !== false ) {
            ?>
<meta property="og:profile:url" content="<?php echo esc_attr( $url ); ?>">
            <?php
        }
        if ( stripos( $handle, 'android://' ) === 0 ) {
            ?>
<meta property="al:android:url" content="<?php echo esc_attr( $url ); ?>">
            <?php
        }
        if ( stripos( $handle, 'ios://' ) === 0 ) {
            ?>
<meta property="al:ios:url" content="<?php echo esc_attr( $url ); ?>">
            <?php
        }
    }
    ?>
<!-- /openclaw social meta tags -->
    <?php
}
add_action( 'wp_head', 'openclaw_social_meta_tags', 2 );

/**
 * [openclaw_social_links] — renders social media icon links with inline SVGs.
 *
 * Usage (in footer HTML):
 *   [openclaw_social_links]
 *
 * Each child theme defines OPENCLAW_SOCIAL_PROFILES — an associative array
 * mapping platform identifiers to full URLs. The shortcode reads the constant
 * and renders a <div class="openclaw-social-links"> with inline SVG icons.
 *
 * Supported platform handles (for SVG selection):
 *   x.com / twitter.com, facebook.com, instagram.com, linkedin.com,
 *   reddit.com, bluesky.social, youtube.com, tiktok.com
 */
function openclaw_social_links_shortcode( array|string $atts = [] ): string {
    $profiles = defined( 'OPENCLAW_SOCIAL_PROFILES' ) ? OPENCLAW_SOCIAL_PROFILES : [];
    if ( empty( $profiles ) ) {
        return '';
    }

    ob_start();
    ?>
<div class="openclaw-social-links" aria-label="Social media">
    <?php foreach ( $profiles as $handle => $url ) : ?>
        <a href="<?php echo esc_url( $url ); ?>" rel="noopener" target="_blank" aria-label="<?php echo esc_attr( openclaw_social_label( $handle ) ); ?>">
            <?php echo openclaw_social_svg( $handle ); ?>
        </a>
    <?php endforeach; ?>
</div>
    <?php
    return (string) ob_get_clean();
}
add_shortcode( 'openclaw_social_links', 'openclaw_social_links_shortcode' );

/**
 * Return a human-readable label for a social platform handle.
 */
function openclaw_social_label( string $handle ): string {
    if ( stripos( $handle, 'x.com' ) !== false || stripos( $handle, 'twitter.com' ) !== false ) return 'Follow on X';
    if ( stripos( $handle, 'facebook.com' ) !== false ) return 'Follow on Facebook';
    if ( stripos( $handle, 'instagram.com' ) !== false ) return 'Follow on Instagram';
    if ( stripos( $handle, 'linkedin.com' ) !== false ) return 'Follow on LinkedIn';
    if ( stripos( $handle, 'reddit.com' ) !== false ) return 'Visit Reddit';
    if ( stripos( $handle, 'bluesky.social' ) !== false ) return 'Follow on Bluesky';
    if ( stripos( $handle, 'youtube.com' ) !== false ) return 'Subscribe on YouTube';
    if ( stripos( $handle, 'tiktok.com' ) !== false ) return 'Follow on TikTok';
    return 'Social link';
}

/**
 * Return inline SVG for a social platform handle.
 */
function openclaw_social_svg( string $handle ): string {
    // X (Twitter)
    if ( stripos( $handle, 'x.com' ) !== false || stripos( $handle, 'twitter.com' ) !== false ) {
        return '<svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M14.16 1.9l2.18.48-4.72 5.4L16 14.1h-5.6l-4.32-5.8L.42 14.1H.06l5.04-5.8L.1 1.9h5.72l3.9 5.22zm-.92 11.52h1.72L4.82 2.98H2.98z"/></svg>';
    }
    // Facebook
    if ( stripos( $handle, 'facebook.com' ) !== false ) {
        return '<svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><circle cx="8" cy="8" r="7.25" fill="#1877F2"/><path d="M9.2 9.5h1.8l.25-2h-2.05v-1.3c0-.6.14-1 .9-1h1.05V3.2a7.5 7.5 0 00-1.5-.15c-1.5 0-2.5.9-2.5 2.6v1.4H5.3v2h1.55v6.15c.5.07 1 .1 1.5.1V9.5z" fill="#fff"/></svg>';
    }
    // Instagram
    if ( stripos( $handle, 'instagram.com' ) !== false ) {
        return '<svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><rect x="1.5" y="1.5" width="13" height="13" rx="3.5" fill="none" stroke="currentColor" stroke-width="1.5"/><circle cx="8" cy="8" r="3.2" fill="none" stroke="currentColor" stroke-width="1.5"/><circle cx="12.2" cy="3.8" r="1" fill="currentColor"/></svg>';
    }
    // LinkedIn
    if ( stripos( $handle, 'linkedin.com' ) !== false ) {
        return '<svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><rect x="1.5" y="1.5" width="13" height="13" rx="2" fill="#0A66C2"/><text x="8" y="11.5" text-anchor="middle" fill="#fff" font-size="8" font-weight="bold" font-family="sans-serif">in</text></svg>';
    }
    // Reddit
    if ( stripos( $handle, 'reddit.com' ) !== false ) {
        return '<svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><circle cx="8" cy="8" r="6.5" fill="#FF4500"/><circle cx="8" cy="7.5" r="4.5" fill="#FF4500"/><circle cx="6.2" cy="6.5" r="1.2" fill="#fff"/><circle cx="9.8" cy="6.5" r="1.2" fill="#fff"/><path d="M5.5 9.5c0 0 1 1.5 2.5 1.5s2.5-1.5 2.5-1.5" fill="none" stroke="#fff" stroke-width=".8"/></svg>';
    }
    // Bluesky
    if ( stripos( $handle, 'bluesky.social' ) !== false ) {
        return '<svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M8 1.2C5.5 1.2 3 2 2.2 4.5c-.3 1-.2 2 .1 2.8.4.9 1 1.5 1.5 1.8-.2.5-.5 1.2-.3 2.1.2.8 1 1.3 2 1.3h1c.8 0 1.3-.3 1.6-.7.3-.4.4-.9.4-1.4 0-.3 0-.5-.1-.7.5-.3 1.2-.9 1.5-1.8.3-.8.4-1.8.1-2.8C13 2 10.5 1.2 8 1.2z"/></svg>';
    }
    // YouTube
    if ( stripos( $handle, 'youtube.com' ) !== false ) {
        return '<svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><rect x="1.5" y="2.5" width="13" height="11" rx="3" fill="#FF0000"/><polygon points="6.5,5 6.5,11 11,8" fill="#fff"/></svg>';
    }
    // TikTok (default fallback)
    return '<svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M8 2v4.5a2.5 2.5 0 11-2.5 2.5V7a4 4 0 104 4v-2.5a5.5 5.5 0 01-5.5 5.5v2.5A8 8 0 118 2z"/></svg>';
}

/**
 * Register block-pattern category so parent patterns group under one heading in
 * the inserter.
 */
function openclaw_base_pattern_category(): void {
    if ( ! function_exists( 'register_block_pattern_category' ) ) {
        return;
    }
    register_block_pattern_category( 'openclaw', [ 'label' => __( 'Openclaw', 'openclaw-base' ) ] );
}
add_action( 'init', 'openclaw_base_pattern_category' );

/**
 * [openclaw_related_posts count="3"] — same-category posts first, then same-tag
 * fill, then most-recent to top up. Skips the current post. Rendered as a
 * 3-col grid of thumbnail cards. Excluded on non-single or when nothing to
 * relate to.
 */
/**
 * [openclaw_byline] — editorial byline for the single-post template.
 *
 * Outputs "By <a href="/about/">{Site Name} Editors</a> · Published <time>
 * · Reviewed <time>". Site name comes from get_bloginfo('name') so the
 * byline self-adapts per subsite ("Rootstock Editors", "Kennelside Editors",
 * etc.) without any per-child-theme configuration.
 *
 * Reviewed date comes from _openclaw_last_reviewed post meta (registered by
 * mu-plugin openclaw-register-editorial-meta.php, which also seeds it from
 * the publish date on first publish). If the meta is somehow missing or
 * matches the publish date, the "Reviewed" chunk is suppressed to avoid
 * showing "Published X · Reviewed X" as visual duplication.
 */
function openclaw_byline_shortcode( array|string $atts = [] ): string {
    if ( ! is_singular( 'post' ) ) {
        return '';
    }
    $post_id = (int) get_the_ID();
    if ( ! $post_id ) {
        return '';
    }

    // Prefer an explicit brand name (set by scripts/create-legal-pages.py from
    // the same SITE_INFO used by the About/Fact-Checking copy). Falls back to
    // the site's blogname on any site that hasn't been branded yet.
    $brand      = get_option( 'openclaw_brand', '' );
    if ( '' === $brand ) {
        $brand = get_bloginfo( 'name' );
    }
    $byline     = trim( $brand ) . ' Editors';
    $about_url  = esc_url( home_url( '/about/' ) );

    $published_iso     = get_the_date( 'c', $post_id );
    $published_display = get_the_date( '', $post_id );
    $published_ymd     = get_the_date( 'Y-m-d', $post_id );

    $reviewed_raw = get_post_meta( $post_id, '_openclaw_last_reviewed', true );
    $reviewed_chunk = '';
    if ( ! empty( $reviewed_raw ) && $reviewed_raw !== $published_ymd ) {
        $reviewed_ts       = strtotime( $reviewed_raw );
        $reviewed_iso      = $reviewed_ts ? date( 'c', $reviewed_ts ) : esc_attr( $reviewed_raw );
        $reviewed_display  = $reviewed_ts ? date_i18n( get_option( 'date_format' ), $reviewed_ts ) : esc_html( $reviewed_raw );
        $reviewed_chunk = sprintf(
            ' · Reviewed <time datetime="%s">%s</time>',
            esc_attr( $reviewed_iso ),
            esc_html( $reviewed_display )
        );
    }

    // Editorial-series chip (Step 8.12). Renders next to the byline when the
    // post has an openclaw_series term assigned. Silent when the taxonomy is
    // unassigned so the byline degrades cleanly on pre-8.12 posts.
    $series_chunk = '';
    $series_terms = get_the_terms( $post_id, 'openclaw_series' );
    if ( ! is_wp_error( $series_terms ) && ! empty( $series_terms ) ) {
        $series_term = $series_terms[0];
        $series_link = get_term_link( $series_term );
        if ( ! is_wp_error( $series_link ) ) {
            $series_chunk = sprintf(
                ' <a class="openclaw-series-chip" href="%s">%s</a>',
                esc_url( $series_link ),
                esc_html( $series_term->name )
            );
        }
    }

    return sprintf(
        '<div class="openclaw-byline">By <a href="%s" rel="author">%s</a> · Published <time datetime="%s">%s</time>%s%s</div>',
        $about_url,
        esc_html( $byline ),
        esc_attr( $published_iso ),
        esc_html( $published_display ),
        $reviewed_chunk,
        $series_chunk
    );
}
add_shortcode( 'openclaw_byline', 'openclaw_byline_shortcode' );

function openclaw_related_posts_shortcode( array|string $atts = [] ): string {
    $atts = shortcode_atts( [ 'count' => 3 ], is_array( $atts ) ? $atts : [] );
    $count = max( 1, (int) $atts['count'] );

    if ( ! is_singular( 'post' ) ) {
        return '';
    }
    $current_id = (int) get_the_ID();
    if ( ! $current_id ) {
        return '';
    }

    $category_ids = wp_get_post_categories( $current_id );
    $tag_ids      = wp_get_post_tags( $current_id, [ 'fields' => 'ids' ] );
    $series_terms = get_the_terms( $current_id, 'openclaw_series' );
    $series_ids   = ( ! is_wp_error( $series_terms ) && ! empty( $series_terms ) )
        ? wp_list_pluck( $series_terms, 'term_id' )
        : [];
    $found_ids    = [];

    // Priority 1 (Step 8.12): same editorial series.
    if ( $series_ids ) {
        $q = new WP_Query( [
            'post_type'      => 'post',
            'post_status'    => 'publish',
            'posts_per_page' => $count,
            'post__not_in'   => [ $current_id ],
            'tax_query'      => [ [
                'taxonomy' => 'openclaw_series',
                'field'    => 'term_id',
                'terms'    => $series_ids,
            ] ],
            'orderby'        => 'date',
            'order'          => 'DESC',
            'fields'         => 'ids',
            'no_found_rows'  => true,
        ] );
        $found_ids = $q->posts;
    }

    // Priority 2: fill with same-category posts.
    if ( count( $found_ids ) < $count && $category_ids ) {
        $need = $count - count( $found_ids );
        $q = new WP_Query( [
            'post_type'      => 'post',
            'post_status'    => 'publish',
            'posts_per_page' => $need,
            'post__not_in'   => array_merge( [ $current_id ], $found_ids ),
            'category__in'   => $category_ids,
            'orderby'        => 'date',
            'order'          => 'DESC',
            'fields'         => 'ids',
            'no_found_rows'  => true,
        ] );
        $found_ids = array_merge( $found_ids, $q->posts );
    }

    // Priority 3: fill with same-tag posts.
    if ( count( $found_ids ) < $count && $tag_ids ) {
        $need = $count - count( $found_ids );
        $q = new WP_Query( [
            'post_type'      => 'post',
            'post_status'    => 'publish',
            'posts_per_page' => $need,
            'post__not_in'   => array_merge( [ $current_id ], $found_ids ),
            'tag__in'        => $tag_ids,
            'orderby'        => 'date',
            'order'          => 'DESC',
            'fields'         => 'ids',
            'no_found_rows'  => true,
        ] );
        $found_ids = array_merge( $found_ids, $q->posts );
    }

    // Priority 4: top up with most-recent.
    if ( count( $found_ids ) < $count ) {
        $need = $count - count( $found_ids );
        $q = new WP_Query( [
            'post_type'      => 'post',
            'post_status'    => 'publish',
            'posts_per_page' => $need,
            'post__not_in'   => array_merge( [ $current_id ], $found_ids ),
            'orderby'        => 'date',
            'order'          => 'DESC',
            'fields'         => 'ids',
            'no_found_rows'  => true,
        ] );
        $found_ids = array_merge( $found_ids, $q->posts );
    }

    if ( empty( $found_ids ) ) {
        return '';
    }

    ob_start();
    ?>
    <section class="openclaw-related">
        <h2 class="openclaw-related-heading"><?php esc_html_e( 'More from this site', 'openclaw-base' ); ?></h2>
        <div class="openclaw-related-grid">
            <?php foreach ( $found_ids as $pid ) : ?>
                <a class="openclaw-related-card" href="<?php echo esc_url( get_permalink( $pid ) ); ?>">
                    <?php if ( has_post_thumbnail( $pid ) ) : ?>
                        <?php echo get_the_post_thumbnail( $pid, 'openclaw-card', [ 'loading' => 'lazy' ] ); ?>
                    <?php endif; ?>
                    <h4><?php echo esc_html( get_the_title( $pid ) ); ?></h4>
                </a>
            <?php endforeach; ?>
        </div>
    </section>
    <?php
    return (string) ob_get_clean();
}
add_shortcode( 'openclaw_related_posts', 'openclaw_related_posts_shortcode' );

/**
 * [openclaw_explore_categories count="6" exclude="uncategorized,guides-tutorials"]
 * Renders a grid of category tiles for the home page. Ordered by post count
 * desc so the highest-signal categories surface first. Excludes any category
 * slug in the exclude= list.
 */
function openclaw_explore_categories_shortcode( array|string $atts = [] ): string {
    $atts = shortcode_atts( [
        'count'   => 6,
        'exclude' => 'uncategorized,guides-tutorials',
    ], is_array( $atts ) ? $atts : [] );

    $exclude_slugs = array_filter( array_map( 'trim', explode( ',', (string) $atts['exclude'] ) ) );
    $exclude_ids   = [];
    foreach ( $exclude_slugs as $slug ) {
        $term = get_term_by( 'slug', $slug, 'category' );
        if ( $term && ! is_wp_error( $term ) ) {
            $exclude_ids[] = (int) $term->term_id;
        }
    }

    $terms = get_terms( [
        'taxonomy'   => 'category',
        'hide_empty' => true,
        'exclude'    => $exclude_ids,
        'orderby'    => 'count',
        'order'      => 'DESC',
        'number'     => max( 1, (int) $atts['count'] ),
    ] );
    if ( is_wp_error( $terms ) || empty( $terms ) ) {
        return '';
    }

    ob_start();
    ?>
    <section class="openclaw-explore">
        <h2 class="openclaw-related-heading"><?php esc_html_e( 'Explore', 'openclaw-base' ); ?></h2>
        <div class="openclaw-explore-grid">
            <?php foreach ( $terms as $term ) : ?>
                <a class="openclaw-explore-tile" href="<?php echo esc_url( get_term_link( $term ) ); ?>">
                    <span class="openclaw-explore-tile-name"><?php echo esc_html( $term->name ); ?></span>
                    <span class="openclaw-explore-tile-count">
                        <?php echo esc_html( sprintf( _n( '%d article', '%d articles', (int) $term->count, 'openclaw-base' ), (int) $term->count ) ); ?>
                    </span>
                    <span class="openclaw-explore-tile-underline" aria-hidden="true"></span>
                </a>
            <?php endforeach; ?>
        </div>
        <style>
            .openclaw-explore { margin: 48px 0; }
            .openclaw-explore-grid {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 16px;
            }
            @media (max-width: 900px) { .openclaw-explore-grid { grid-template-columns: repeat(2, 1fr); } }
            @media (max-width: 500px) { .openclaw-explore-grid { grid-template-columns: 1fr; } }
        </style>
    </section>
    <?php
    return (string) ob_get_clean();
}
add_shortcode( 'openclaw_explore_categories', 'openclaw_explore_categories_shortcode' );

/**
 * Auto-inject a table of contents on singular posts with 3+ H2s.
 *
 * - Adds `id="openclaw-h2-<slug>"` to each H2 that lacks one.
 * - Prepends a <nav class="openclaw-toc"> ordered list of anchor links before
 *   the first H2.
 * - Skippable per post via post_meta `_openclaw_disable_toc = 1`.
 */
function openclaw_auto_toc( string $content ): string {
    if ( ! is_singular( 'post' ) || ! in_the_loop() || ! is_main_query() ) {
        return $content;
    }
    if ( (string) get_post_meta( get_the_ID(), '_openclaw_disable_toc', true ) === '1' ) {
        return $content;
    }
    if ( ! preg_match_all( '/<h2\b([^>]*)>(.*?)<\/h2>/is', $content, $matches, PREG_OFFSET_CAPTURE ) ) {
        return $content;
    }
    if ( count( $matches[0] ) < 3 ) {
        return $content;
    }

    $used_ids = [];
    $toc_items = [];
    $offset = 0;

    // Walk matches in order, mutating $content in-place and building the TOC.
    foreach ( $matches[0] as $i => $full ) {
        $full_tag_original = $full[0];
        $attrs             = $matches[1][ $i ][0];
        $inner             = $matches[2][ $i ][0];
        $text              = trim( html_entity_decode( wp_strip_all_tags( $inner ), ENT_QUOTES ) );

        if ( $text === '' ) {
            continue;
        }

        // Existing id="..."?
        $id = '';
        if ( preg_match( '/\bid\s*=\s*"([^"]+)"/i', $attrs, $m ) ) {
            $id = $m[1];
        } elseif ( preg_match( "/\bid\s*=\s*'([^']+)'/i", $attrs, $m ) ) {
            $id = $m[1];
        }
        if ( $id === '' ) {
            $base = sanitize_title( $text );
            if ( $base === '' ) {
                $base = 'section';
            }
            $slug  = $base;
            $n     = 2;
            while ( isset( $used_ids[ $slug ] ) ) {
                $slug = $base . '-' . $n;
                $n++;
            }
            $id = 'openclaw-h2-' . $slug;

            // Splice id="..." into the opening tag.
            $new_tag = '<h2' . rtrim( $attrs ) . ' id="' . esc_attr( $id ) . '">' . $inner . '</h2>';
            $pos     = $full[1] + $offset;
            $content = substr_replace( $content, $new_tag, $pos, strlen( $full_tag_original ) );
            $offset += strlen( $new_tag ) - strlen( $full_tag_original );
        }
        $used_ids[ $id ] = true;
        $toc_items[]     = [ 'id' => $id, 'text' => $text ];
    }

    if ( count( $toc_items ) < 3 ) {
        return $content;
    }

    $toc_html  = '<nav class="openclaw-toc" aria-label="' . esc_attr__( 'Table of contents', 'openclaw-base' ) . '">';
    $toc_html .= '<p class="openclaw-toc-title">' . esc_html__( 'Contents', 'openclaw-base' ) . '</p>';
    $toc_html .= '<ol>';
    foreach ( $toc_items as $item ) {
        $toc_html .= '<li><a href="#' . esc_attr( $item['id'] ) . '">' . esc_html( $item['text'] ) . '</a></li>';
    }
    $toc_html .= '</ol></nav>';

    // Prepend before the first H2 in the mutated content.
    if ( preg_match( '/<h2\b/i', $content, $m, PREG_OFFSET_CAPTURE ) ) {
        $content = substr_replace( $content, $toc_html, $m[0][1], 0 );
    }

    return $content;
}
add_filter( 'the_content', 'openclaw_auto_toc', 20 );

/**
 * Auto-inject one in-content ad slot near the midpoint of the post, at a
 * <p> boundary — word-count based so it never lands inside a list or code
 * block. Skips short posts (< 6 paragraphs) where a mid-content slot would
 * sit awkwardly close to the top or bottom. Runs after the TOC filter
 * (priority 20) so its <ol>/<li> markup is never mistaken for a paragraph.
 */
function openclaw_auto_ad_slot_mid_content( string $content ): string {
    if ( ! is_singular( 'post' ) || ! in_the_loop() || ! is_main_query() ) {
        return $content;
    }
    if ( ! preg_match_all( '/<p\b[^>]*>.*?<\/p>/is', $content, $matches, PREG_OFFSET_CAPTURE ) ) {
        return $content;
    }
    $paragraphs = $matches[0];
    if ( count( $paragraphs ) < 6 ) {
        return $content;
    }

    $word_counts = array_map(
        static fn( array $p ): int => str_word_count( wp_strip_all_tags( $p[0] ) ),
        $paragraphs
    );
    $total_words = array_sum( $word_counts );
    if ( $total_words === 0 ) {
        return $content;
    }

    $target  = $total_words / 2;
    $running = 0;
    $insert_after_index = count( $paragraphs ) - 1;
    foreach ( $word_counts as $i => $w ) {
        $running += $w;
        if ( $running >= $target ) {
            $insert_after_index = $i;
            break;
        }
    }

    $slot = "\n" . '<div class="openclaw-ad-slot openclaw-ad-slot--in-content" data-slot-id="post-mid"></div>' . "\n";
    $insert_pos = $paragraphs[ $insert_after_index ][1] + strlen( $paragraphs[ $insert_after_index ][0] );
    return substr_replace( $content, $slot, $insert_pos, 0 );
}
add_filter( 'the_content', 'openclaw_auto_ad_slot_mid_content', 21 );

/**
 * [openclaw_share_bar] — social sharing bar rendered after the article body.
 *
 * Outputs X, Facebook, Reddit, LinkedIn share links + a "Copy link" button.
 * Uses current post title and URL. The copy-link button uses a minimal inline
 * navigator.clipboard.writeText call — no external JS dependency.
 */
function openclaw_share_bar_shortcode( array|string $atts = [] ): string {
    if ( ! is_singular( 'post' ) ) {
        return '';
    }
    $title = get_the_title();
    $url   = get_permalink();
    if ( ! $title || ! $url ) {
        return '';
    }
    $encoded_title = rawurlencode( $title );
    $encoded_url   = rawurlencode( $url );
    ob_start();
    ?>
    <div class="openclaw-share-bar">
        <span>Share:</span>
        <a href="https://twitter.com/intent/tweet?text=<?php echo $encoded_title; ?>&url=<?php echo $encoded_url; ?>" rel="noopener" target="_blank" aria-label="Share on X">X</a>
        <a href="https://www.facebook.com/sharer/sharer.php?u=<?php echo $encoded_url; ?>" rel="noopener" target="_blank" aria-label="Share on Facebook">FB</a>
        <a href="https://www.reddit.com/submit?url=<?php echo $encoded_url; ?>&title=<?php echo $encoded_title; ?>" rel="noopener" target="_blank" aria-label="Share on Reddit">Reddit</a>
        <a href="https://www.linkedin.com/sharing/share-offsite/?url=<?php echo $encoded_url; ?>" rel="noopener" target="_blank" aria-label="Share on LinkedIn">in</a>
        <button onclick="navigator.clipboard.writeText('<?php echo esc_attr( $url ); ?>')" aria-label="Copy link">Copy link</button>
    </div>
    <?php
    return (string) ob_get_clean();
}
add_shortcode( 'openclaw_share_bar', 'openclaw_share_bar_shortcode' );

/**
 * [openclaw_network_crosslink] — "From other Info Verse sites" sidebar.
 *
 * Fetches the latest post from each of the five subsite RSS feeds and renders
 * them as a compact list of links. Fail-soft: if a subsite feed is unreachable,
 * skip it silently. Uses the same RSS-fetching approach as
 * openclaw_hub_fetch_subsite_posts() in the hub theme.
 */
function openclaw_network_crosslink_shortcode( array|string $atts = [] ): string {
    if ( ! is_singular( 'post' ) ) {
        return '';
    }

    $subsite_origins = [
        'https://techtools.info-verse.org',
        'https://gardening.info-verse.org',
        'https://dogs.info-verse.org',
        'https://boardgames.info-verse.org',
        'https://coffee.info-verse.org',
        // Local development.
        'http://techtools.localhost:8088',
        'http://gardening.localhost:8088',
        'http://dogs.localhost:8088',
        'http://boardgames.localhost:8088',
        'http://coffee.localhost:8088',
    ];

    $all_posts = [];
    foreach ( $subsite_origins as $origin ) {
        // Skip our own site.
        $current_origin = esc_url( home_url() );
        if ( str_starts_with( $current_origin, $origin ) ) {
            continue;
        }

        // Try REST API first (works on live WordPress and local dev).
        $api_url = trailingslashit( $origin ) . 'wp-json/wp/v2/posts?per_page=1&orderby=date&filter[ignore_sticky_posts]=true';
        $res     = wp_remote_get( $api_url, [
            'timeout'   => 5,
            'redirection' => 0,
        ] );

        if ( ! is_wp_error( $res ) ) {
            $code = (int) wp_remote_retrieve_response_code( $res );
            if ( $code >= 200 && $code < 300 ) {
                $body = wp_remote_retrieve_body( $res );
                if ( $body !== '' ) {
                    $data = @json_decode( $body, true );
                    if ( isset( $data[0] ) ) {
                        $title = html_entity_decode( wp_strip_all_tags( $data[0]['title']['rendered'] ), ENT_QUOTES, 'UTF-8' );
                        $link  = $data[0]['link'];
                        if ( $title !== '' && $link !== get_permalink() ) {
                            $all_posts[] = [ 'title' => $title, 'link' => $link ];
                        }
                        continue; // Got a post via REST API.
                    }
                }
            }
        }

        // Fallback: try RSS feed (only works on live WordPress with dynamic feeds).
        $feed_url = trailingslashit( $origin ) . 'feed/';
        $res      = wp_remote_get( $feed_url, [
            'timeout'     => 5,
            'redirection' => 2,
            'user-agent'  => 'openclaw-base-crosslink/1.0',
        ] );

        if ( is_wp_error( $res ) ) {
            continue;
        }

        $code = (int) wp_remote_retrieve_response_code( $res );
        $body = wp_remote_retrieve_body( $res );
        if ( $code < 200 || $code >= 300 || $body === '' ) {
            continue;
        }

        // Only parse as XML if content type indicates it.
        $ct = wp_remote_retrieve_header( $res, 'content-type' );
        if ( $ct && ! stripos( $ct, 'xml' ) && ! stripos( $ct, 'atom' ) && ! stripos( $ct, 'rss' ) ) {
            continue; // Static HTML export — skip.
        }

        $body = preg_replace( '/[\x00-\x08\x0B\x0C\x0E-\x1F]/', '', $body );
        $prev_errors = libxml_use_internal_errors( true );
        $xml         = @simplexml_load_string( $body );
        libxml_clear_errors();
        libxml_use_internal_errors( $prev_errors );

        if ( ! $xml || ! isset( $xml->channel->item ) ) {
            continue;
        }

        foreach ( $xml->channel->item as $item ) {
            $title = (string) $item->title;
            $link  = (string) $item->link;
            if ( $title !== '' && $link !== '' ) {
                if ( $link !== get_permalink() ) {
                    $all_posts[] = [
                        'title' => html_entity_decode( wp_strip_all_tags( $title ), ENT_QUOTES, 'UTF-8' ),
                        'link'  => $link,
                    ];
                }
                break;
            }
        }
    }

    if ( empty( $all_posts ) ) {
        return '';
    }

    ob_start();
    ?>
    <section class="openclaw-crosslink">
        <h2 class="openclaw-crosslink-heading"><?php esc_html_e( 'From other Info Verse sites', 'openclaw-base' ); ?></h2>
        <ul class="openclaw-crosslink-list">
            <?php foreach ( $all_posts as $post ) : ?>
                <li><a href="<?php echo esc_url( $post['link'] ); ?>" rel="noopener"><?php echo esc_html( $post['title'] ); ?></a></li>
            <?php endforeach; ?>
        </ul>
    </section>
    <?php
    return (string) ob_get_clean();
}
add_shortcode( 'openclaw_network_crosslink', 'openclaw_network_crosslink_shortcode' );
