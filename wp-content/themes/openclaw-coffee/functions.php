<?php
/**
 * Crema (openclaw-coffee) — child of openclaw-base.
 *
 * Swaps in the brand's Google Fonts pair (Cormorant Garamond display + Inter body)
 * via the parent's `openclaw_base_google_fonts_url` filter.
 */

add_filter( 'openclaw_base_google_fonts_url', function () {
    return 'https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600;700&family=Inter:wght@400;500;600;700&display=swap';
} );
