import { renderCategories } from "./category.js";
import { renderProductsPrices, closeProductDetail } from "./products.js";
import { renderProducts, resetPagination, renderProductDetail } from "./products.js";

document.addEventListener('DOMContentLoaded', async function(){
    await renderCategories();
    await renderProductsPrices();
    renderProducts();

    const filterForm = document.getElementById('filterForm');
    filterForm.addEventListener('submit', async function(e){
        e.preventDefault();

        const cat = document.getElementById('select-category').value;
        const price = document.getElementById('select-price').value;
        const condition = document.getElementById('select-condition').value;

        const filters = {};

        if (cat && cat !== 'cat') filters.category_id = cat;
        if (price && price !== "") filters.min_price = price;
        if (condition && condition !== "") filters.condition = condition;

        resetPagination(filters);   // Reset page & filters in products.js
        await renderProducts(filters);
    });

    handleURLLoad();

    // Handle browser back/forward buttons
    window.addEventListener('popstate', handleURLLoad);
});

function handleURLLoad() {
    const match = window.location.pathname.match(/^\/products\/([0-9a-fA-F-]+)\/$/);
    if (match) {
        const productId = match[1];
        renderProductDetail(productId);
    } else {
        closeProductDetail(); // Hide detail if returning to list
    }
}
