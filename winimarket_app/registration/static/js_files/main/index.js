import { renderCategories } from "./category.js";
import { renderProductsPrices } from "./products.js";
import { renderProducts } from "./products.js";

document.addEventListener('DOMContentLoaded', async function(){
    await renderCategories()
    await renderProductsPrices()
    renderProducts()

    const filterForm = document.getElementById('filterForm')
    filterForm.addEventListener('submit', async function(e){
        e.preventDefault()

        const cat = document.getElementById('select-category').value
        const price = document.getElementById('select-price').value
        const condition = document.getElementById('select-condition').value
        console.log(cat)
        console.log(price)
        console.log(condition)

        const filters = {};

        if (cat && cat !== 'cat') {
            filters.category_id = cat;
        }

        if (price && price !== "") {
            filters.min_price = price;
        }

        if (condition && condition !== "") {
            filters.condition = condition;
        }

        console.log(filters);

        await renderProducts(filters)
    })

})