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
 */
// define( 'OPENCLAW_ADSENSE_ID', 'ca-pub-XXXXXXXXXXXXXXXX' );

function openclaw_base_adsense_snippet(): void {
    if ( ! defined( 'OPENCLAW_ADSENSE_ID' ) || ! OPENCLAW_ADSENSE_ID ) {
        return;
    }
    $id = esc_attr( OPENCLAW_ADSENSE_ID );
    ?>
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=<?php echo $id; ?>" crossorigin="anonymous"></script>
    <?php
}
add_action( 'wp_head', 'openclaw_base_adsense_snippet', 1 );

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
 * [openclaw_site_copyright] — site-specific footer identity for every child
 * theme.  A hard-coded parent-theme brand made Rootstock, Kennelside, Meeple,
 * Crema, and Tech Tool Guide look like anonymous network microsites.
 */
function openclaw_site_copyright_shortcode(): string {
    return sprintf(
        '&copy; <a href="%1$s">%2$s</a>',
        esc_url( home_url( '/' ) ),
        esc_html( get_bloginfo( 'name' ) )
    );
}
add_shortcode( 'openclaw_site_copyright', 'openclaw_site_copyright_shortcode' );

/**
 * [openclaw_related_posts count="3"] — same-category posts first, then same-tag
 * fill, then most-recent to top up. Skips the current post. Rendered as a
 * 3-col grid of thumbnail cards. Excluded on non-single or when nothing to
 * relate to.
 */
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
    $found_ids    = [];

    // Priority 1: same category.
    if ( $category_ids ) {
        $q = new WP_Query( [
            'post_type'      => 'post',
            'post_status'    => 'publish',
            'posts_per_page' => $count,
            'post__not_in'   => [ $current_id ],
            'category__in'   => $category_ids,
            'orderby'        => 'date',
            'order'          => 'DESC',
            'fields'         => 'ids',
            'no_found_rows'  => true,
        ] );
        $found_ids = $q->posts;
    }

    // Priority 2: fill with same-tag posts.
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

    // Priority 3: top up with most-recent.
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
