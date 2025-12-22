import { renderProducts, resetPagination, renderProductDetail, renderCategorySlider } from "./products.js";
import { initSearch, initSearchInfiniteScroll } from "./search.js";
// { initWishListContainer, openWishlist, closeWishlist } from "./wishlist.js";
//import { initCartContainer, displayCartContainer } from "./cart.js"

document.addEventListener('DOMContentLoaded', async function(){
    //await renderProductsPrices();
    renderProducts();
    initSearch();
    await renderCategorySlider()
    //await initWishListContainer()
    //await initCartContainer()
    //displayCartContainer()

    //handleURLLoad();

    // Handle browser back/forward buttons
    //window.addEventListener('popstate', handleURLLoad);


    const searchList = document.querySelector(".search-list")
    const searchGrid = document.getElementById('search-grid')

    if(searchList && searchGrid){
        await initSearchInfiniteScroll(searchList, searchGrid)
    }
});

/* function handleURLLoad() {
    const productMatch = window.location.pathname.match(/^\/products\/([0-9a-fA-F-]+)\/$/);
    const wishlistContainer = document.getElementById('wishlist-product');

    if (productMatch) {
        // Product detail open
        const productId = productMatch[1];
        renderProductDetail(productId);
        
    } else {
        // Close both if neither matches
        closeProductDetail();
        if (wishlistContainer) closeWishlist(wishlistContainer, true);
    }
} */
