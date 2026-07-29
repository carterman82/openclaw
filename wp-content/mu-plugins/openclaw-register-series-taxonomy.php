<?php
/**
 * Plugin Name: Openclaw — Register openclaw_series Taxonomy
 * Description: Custom flat taxonomy `openclaw_series` on the `post` post type,
 *              exposed to the REST API so the openclaw agent can assign an
 *              editorial-series term at publish time. Sibling to
 *              openclaw-register-{seo,editorial}-meta.php.
 * Version:     1.0.0
 */

add_action( 'init', function () {
    register_taxonomy( 'openclaw_series', 'post', [
        'label'             => 'Editorial Series',
        'labels'            => [
            'name'          => 'Editorial Series',
            'singular_name' => 'Series',
            'menu_name'     => 'Series',
        ],
        'public'            => true,
        'show_ui'           => true,
        'show_in_menu'      => true,
        'show_admin_column' => true,
        'show_in_rest'      => true,
        'rest_base'         => 'openclaw_series',
        'hierarchical'      => false,
        'rewrite'           => [ 'slug' => 'series' ],
    ] );
} );
