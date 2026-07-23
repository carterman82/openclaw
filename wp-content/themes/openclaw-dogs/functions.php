<?php
/**
 * Kennelside (openclaw-dogs) — child of openclaw-base.
 *
 * Swaps in the brand's Google Fonts pair (Domine display + Nunito Sans body)
 * via the parent's `openclaw_base_google_fonts_url` filter.
 */

add_filter( 'openclaw_base_google_fonts_url', function () {
    return 'https://fonts.googleapis.com/css2?family=Domine:wght@400;500;600;700&family=Nunito+Sans:wght@400;500;600;700&display=swap';
} );

// GA4 measurement ID for this subsite (Phase 7 Step 7.3). Undefined = no
// tracking snippet output (see openclaw-base's wp_head hook). Fill in once
// the GA4 property for Kennelside exists.
define( 'OPENCLAW_GA4_ID', 'G-EMJRNCZR10' );
