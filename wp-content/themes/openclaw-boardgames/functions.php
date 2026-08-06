<?php
/**
 * Meeple (openclaw-boardgames) — child of openclaw-base.
 *
 * Swaps in the brand's Google Fonts pair (Roboto Slab display + Work Sans body)
 * via the parent's `openclaw_base_google_fonts_url` filter.
 */

add_filter( 'openclaw_base_google_fonts_url', function () {
    return 'https://fonts.googleapis.com/css2?family=Roboto+Slab:wght@400;500;600;700&family=Work+Sans:wght@400;500;600;700&display=swap';
} );

// GA4 measurement ID for this subsite (Phase 7 Step 7.3). Undefined = no
// tracking snippet output (see openclaw-base's wp_head hook). Fill in once
// the GA4 property for Meeple exists.
define( 'OPENCLAW_GA4_ID', 'G-EMJRNCZR10' );

// Social media profiles for Step 9.3 (Phase 9).
// Placeholder URLs — update when actual accounts are created.
define( 'OPENCLAW_SOCIAL_PROFILES', [
    'https://x.com/BoardgamesInfoVerse'  => 'https://x.com/BoardgamesInfoVerse',
    'https://reddit.com/r/BoardgamesInfoVerse' => 'https://reddit.com/r/BoardgamesInfoVerse',
] );
