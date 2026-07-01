<?php
/**
 * Plugin Name: Openclaw — Register SEO Meta for REST
 * Description: Makes Yoast SEO and RankMath per-post meta fields readable and
 *              writable via the WordPress REST API so the openclaw agent can
 *              set focus keyphrases, meta descriptions, and SEO titles without
 *              going through WP Admin.
 * Version:     1.0.0
 */

add_action( 'init', function () {
    $keys = [
        // Yoast SEO
        '_yoast_wpseo_focuskw',
        '_yoast_wpseo_metadesc',
        '_yoast_wpseo_title',
        // RankMath
        'rank_math_focus_keyword',
        'rank_math_description',
        'rank_math_title',
    ];

    foreach ( $keys as $key ) {
        register_post_meta( 'post', $key, [
            'show_in_rest'  => true,
            'single'        => true,
            'type'          => 'string',
            'auth_callback' => function () {
                return current_user_can( 'edit_posts' );
            },
        ] );
    }
} );
