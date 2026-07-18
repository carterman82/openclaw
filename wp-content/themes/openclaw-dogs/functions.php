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
