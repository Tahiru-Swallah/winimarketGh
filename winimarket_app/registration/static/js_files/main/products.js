import { fetchCategories } from "./category.js";

const cache = new Map()

export async function fetchProducts(filters = {}){
    let url = '/products/api/products/'

    const params = new URLSearchParams(filters).toString();
    const fullUrl = params ? `${url}?${params}` : url

    if(cache.has(fullUrl)){
        return cache.get(fullUrl)
    }
    
    try{

        const response = await fetch(fullUrl);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const products = await response.json();
        cache.set(fullUrl, products)

        return products;

    } catch(error){
        console.error("Error fetching products:", error);
        return [];
    }
}

export async function renderProductsPrices(){
    const products = await fetchProducts()
    console.log(products)
    const selectPrice = document.getElementById('select-price')

    products.forEach(product => {
        const option = document.createElement('option')
        const price = parseFloat(product.min_price)
        option.textContent = `$${price.toFixed(2)}`
        option.value = price

        selectPrice.appendChild(option)
    })
}

export async function renderProducts(filters = {}){
    const products = await fetchProducts(filters)
    const container = document.getElementById('new')
    container.innerHTML = ''

    if (products.length === 0){
        container.innerHTML = `<p>No products available</p>`
        return;
    }

    products.forEach(product=> {
        const productHTML = `
            <div class="new-product">
                <div class="img-p">
                    <img src="${product.images[0].image}" alt="${product.name}">
                </div>
                <div class="p-info">
                    <h4 class="product-name">${product.name}</h4>
                    <p>$${product.min_price}</p>
                </div>
                <span class="material-icons-outlined">favorite_border</span>
            </div>
        `

        container.insertAdjacentHTML('beforeend', productHTML)
    })
}