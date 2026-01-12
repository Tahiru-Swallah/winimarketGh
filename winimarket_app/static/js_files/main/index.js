import { renderProducts, renderCategorySlider } from "./products.js";
import { initSearch, initSearchInfiniteScroll } from "./search.js";
//import { initCartContainer, displayCartContainer } from "./cart.js"

document.addEventListener('DOMContentLoaded', async function(){
    renderProducts();
    initSearch();
    await renderCategorySlider()

    const searchList = document.querySelector(".search-list")
    const searchGrid = document.getElementById('search-grid')

    if(searchList && searchGrid){
        await initSearchInfiniteScroll(searchList, searchGrid)
    }
});