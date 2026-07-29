<?php
/**
 * Plugin Name: Openclaw — Register Editorial Meta for REST
 * Description: Registers _openclaw_last_reviewed post meta so the byline can
 *              show a "Reviewed" date next to "Published", and defaults it to
 *              the publish date when a post first goes live. Sibling to
 *              openclaw-register-seo-meta.php; kept separate because reviewed-
 *              date meta is editorial, not SEO.
 * Version:     1.0.0
 */

add_action( 'init', function () {
    register_post_meta( 'post', '_openclaw_last_reviewed', [
        'show_in_rest'  => true,
        'single'        => true,
        'type'          => 'string',
        'auth_callback' => function () {
            return current_user_can( 'edit_posts' );
        },
    ] );

    // openclaw_brand: per-subsite editorial brand name (e.g. "Rootstock",
    // "Kennelside"). Used by the [openclaw_byline] shortcode and any other
    // template code that wants the brand identity rather than the blogname.
    // Exposed via REST /wp/v2/settings so create-legal-pages.py can set it.
    register_setting( 'general', 'openclaw_brand', [
        'type'         => 'string',
        'default'      => '',
        'show_in_rest' => true,
    ] );
} );

/**
 * On first publish, if _openclaw_last_reviewed is empty, seed it with the
 * post's own publish date (YYYY-MM-DD). Runs on transition_post_status so it
 * only fires once per post — subsequent updates leave the reviewed date alone
 * unless it's explicitly bumped via `wp post meta update`.
 */
add_action( 'transition_post_status', function ( $new_status, $old_status, $post ) {
    if ( 'publish' !== $new_status || 'post' !== get_post_type( $post ) ) {
        return;
    }
    $existing = get_post_meta( $post->ID, '_openclaw_last_reviewed', true );
    if ( ! empty( $existing ) ) {
        return;
    }
    $publish_date = get_the_date( 'Y-m-d', $post );
    if ( $publish_date ) {
        update_post_meta( $post->ID, '_openclaw_last_reviewed', $publish_date );
    }
}, 10, 3 );
