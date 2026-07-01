<?php
/**
 * Plugin Name:       Openclaw — SEO Meta for REST
 * Plugin URI:        https://github.com/openclaw
 * Description:       Registers Yoast SEO and RankMath per-post meta fields
 *                    (focus keyphrase, meta description, SEO title) as readable
 *                    and writable via the WordPress REST API. Required for the
 *                    openclaw agent to set SEO fields programmatically without
 *                    going through WP Admin.
 * Version:           1.0.0
 * Requires at least: 5.9
 * Requires PHP:      7.4
 * Author:            Openclaw
 * License:           GPL-2.0-or-later
 * License URI:       https://www.gnu.org/licenses/gpl-2.0.html
 * Text Domain:       openclaw-seo-meta
 *
 * --------------------------------------------------------------------------
 * WHY THIS PLUGIN EXISTS
 * --------------------------------------------------------------------------
 * WordPress's REST API only exposes post meta fields that have been explicitly
 * registered via register_post_meta() with show_in_rest = true. Yoast SEO and
 * RankMath do NOT register their per-post meta keys this way by default, so
 * any meta values sent by the openclaw agent in the REST payload are silently
 * discarded by WordPress.
 *
 * This plugin registers those keys so the agent can write:
 *   - Focus keyphrase  (_yoast_wpseo_focuskw / rank_math_focus_keyword)
 *   - Meta description (_yoast_wpseo_metadesc / rank_math_description)
 *   - SEO title        (_yoast_wpseo_title    / rank_math_title)
 *
 * It does nothing else. It has no admin UI, no database tables, no options.
 * It is safe to deactivate at any time without data loss.
 *
 * --------------------------------------------------------------------------
 * INSTALLATION
 * --------------------------------------------------------------------------
 * Option A — WP Admin (recommended for most sites):
 *   1. Download or clone this folder.
 *   2. ZIP the folder: right-click → "Send to → Compressed (zipped) folder"
 *      (or: zip -r openclaw-seo-meta.zip openclaw-seo-meta/)
 *   3. WP Admin → Plugins → Add New → Upload Plugin → choose the ZIP.
 *   4. Activate.
 *
 * Option B — mu-plugin (auto-active, no activation step):
 *   Copy this file to wp-content/mu-plugins/openclaw-seo-meta.php.
 *   WordPress loads mu-plugins automatically with no activation required.
 *   Use this for local dev; the copy in wp-content/mu-plugins/ serves the
 *   local Docker site.
 *
 * --------------------------------------------------------------------------
 * VERIFICATION (after installation)
 * --------------------------------------------------------------------------
 * Run a draft post and check the REST read-back:
 *
 *   python scripts/verify-seo.py <post_id>
 *
 * The "Routing" section should show all three keys as PASS.
 * --------------------------------------------------------------------------
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

add_action( 'init', 'openclaw_register_seo_meta' );

/**
 * Register Yoast SEO and RankMath meta keys for REST API read/write.
 *
 * The auth_callback requires edit_posts capability — this covers Authors,
 * Editors, and Administrators. Subscribers and unauthenticated requests
 * cannot write these fields.
 */
function openclaw_register_seo_meta() {
    $seo_meta_keys = [
        // --- Yoast SEO ---
        '_yoast_wpseo_focuskw',   // Focus keyphrase
        '_yoast_wpseo_metadesc',  // Meta description
        '_yoast_wpseo_title',     // SEO title (overrides Yoast's auto-generated title)

        // --- RankMath ---
        'rank_math_focus_keyword', // Focus keyphrase
        'rank_math_description',   // Meta description
        'rank_math_title',         // SEO title
    ];

    foreach ( $seo_meta_keys as $key ) {
        register_post_meta(
            'post',
            $key,
            [
                'show_in_rest'  => true,
                'single'        => true,
                'type'          => 'string',
                'default'       => '',
                'auth_callback' => 'openclaw_seo_meta_auth_callback',
                // Sanitize as plain text — no HTML in SEO fields.
                'sanitize_callback' => 'sanitize_text_field',
            ]
        );
    }
}

/**
 * Allow any user who can edit posts to read/write the SEO meta fields.
 *
 * @param  bool   $allowed   Whether the user is allowed.
 * @param  string $meta_key  The meta key being checked.
 * @param  int    $post_id   The post ID.
 * @return bool
 */
function openclaw_seo_meta_auth_callback( $allowed, $meta_key, $post_id ) {
    return current_user_can( 'edit_post', $post_id );
}
