<?php
/**
 * Title: Card grid (3 columns)
 * Slug: openclaw-base/card-grid
 * Description: Reusable 3-column card grid of latest posts. Drop into any page to surface recent articles with a magazine-editorial look.
 * Categories: openclaw
 * Keywords: cards, grid, posts, latest
 * Block Types: core/query
 */
?>
<!-- wp:query {"queryId":50,"query":{"perPage":9,"pages":0,"offset":0,"postType":"post","order":"desc","orderBy":"date","inherit":false},"align":"wide","layout":{"type":"default"}} -->
<div class="wp-block-query alignwide">
    <!-- wp:post-template {"layout":{"type":"grid","columnCount":3}} -->
        <!-- wp:template-part {"slug":"card"} /-->
    <!-- /wp:post-template -->

    <!-- wp:query-pagination {"paginationArrow":"chevron","layout":{"type":"flex","justifyContent":"center"},"style":{"spacing":{"margin":{"top":"var:preset|spacing|8"}}}} -->
        <!-- wp:query-pagination-previous /-->
        <!-- wp:query-pagination-numbers /-->
        <!-- wp:query-pagination-next /-->
    <!-- /wp:query-pagination -->
</div>
<!-- /wp:query -->
