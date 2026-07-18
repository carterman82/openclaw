<?php
/**
 * Rootstock (openclaw-gardening) — child of openclaw-base.
 *
 * Overrides only what needs to differ from the parent: swaps in the brand's
 * Google Fonts pair (Fraunces display + Lora body) via the parent's
 * `openclaw_base_google_fonts_url` filter.
 */

add_filter( 'openclaw_base_google_fonts_url', function () {
    return 'https://fonts.googleapis.com/css2?family=Fraunces:wght@400;500;600;700&family=Lora:wght@400;500;600;700&display=swap';
} );
