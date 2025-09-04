import { fetchCategories } from "./category.js";

const cache = new Map()

export async function fetchProducts(filters = {}, page=1){
    let url = '/products/api/products/'

    const params = new URLSearchParams({...filters, page}).toString();
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
        return {
            results: [],
            next: null,
            previous: null,
            count: 0
        };
    }
}

export async function renderProductsPrices(){
    const products = await fetchProducts()
    const selectPrice = document.getElementById('select-price')

    products.results.forEach(product => {
        const option = document.createElement('option')
        const price = parseFloat(product.min_price)
        option.textContent = `$${price.toFixed(2)}`
        option.value = price

        selectPrice.appendChild(option)
    })
}


function showSkeletons(container, count = 6, append=false) {
    if(!append) container.innerHTML = '';
    for (let i = 0; i < count; i++) {
        const skeleton = document.createElement('div');
        skeleton.classList.add('skeleton-card');
        skeleton.innerHTML = `
            <div class="skeleton skeleton-img"></div>
            <div class="skeleton skeleton-text"></div>
            <div class="skeleton skeleton-price"></div>
        `;
        container.appendChild(skeleton);
    }
}

let currentPage = 1
let loading = false
let hasMore = true

const bottomLoader = document.querySelector('.bottom-loader');

let filtersState = {}; // keep last used filters

export function resetPagination(newFilters = {}) {
    currentPage = 1;
    hasMore = true;
    filtersState = newFilters;
}

export async function renderProducts(filters = {}, append = false) {
    if (loading || !hasMore) return;
    loading = true;

    // If new filters are passed, update filtersState
    if (Object.keys(filters).length > 0) {
        filtersState = filters;
    } else {
        filters = filtersState;
    }

    const container = document.getElementById('new');
    if (!append) container.innerHTML = '';

    // Show skeleton or loader
    if (append) {
        bottomLoader.style.display = 'block';
    } else {
        showSkeletons(container, 8, false);
    }

    const startTime = Date.now();
    const data = await fetchProducts(filters, currentPage);
    const elapsed = Date.now() - startTime;

    let delay;
    if (elapsed < 300) delay = 400;
    else if (elapsed < 1000) delay = 200;
    else delay = 0;

    setTimeout(() => {
        container.querySelectorAll('.skeleton-card').forEach(el => el.remove());
        bottomLoader.style.display = 'none';

        if (data.results.length === 0 && currentPage === 1) {
            container.innerHTML = `<p>No products available</p>`;
            loading = false;
            hasMore = false;
            return;
        }

        if (data.results.length === 0) {
            loading = false;
            hasMore = false;
            return;
        }

        data.results.forEach(product => {
            const productElement = document.createElement('div');
            productElement.classList.add('new-product');
            productElement.innerHTML = `
                <div class="img-p">
                    <img src="${product.images[0]?.image || '/static/images/default.jpg'}" alt="${product.name}">
                </div>
                <div class="p-info">
                    <h4 class="product-name">${product.name}</h4>
                    <p>$${product.min_price}</p>
                </div>
                <span class="material-icons-outlined">favorite_border</span>
            `;
            productElement.addEventListener('click', () => renderProductDetail(product.id));
            container.appendChild(productElement);
        });

        hasMore = data.next !== null;
        loading = false;
        if (hasMore) currentPage++;
    }, delay);
}

window.addEventListener('scroll', () => {
    if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 200) {
        renderProducts({}, true);
    }
});


export async function fetchProductDetail(productId){
    const url = `/products/api/products/${productId}/`

    if (cache.has(url)){
        return cache.get(url)
    }

    try{

        const response = await fetch(url)

        if(!response.ok){
            throw new Error('Error fetching a single product')
        }

        const product = await response.json()
        cache.set(url, product)

        return product;

    } catch(error){
        console.error('Something went retrieving a single product ' + error)
        return null;
    }
}

function isMobileDevice(){
    return /Mobi|Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
}

export async function renderProductDetail(productId) {
    const container = document.getElementById('product-detail');
    container.style.display = 'block';
    void container.offsetWidth;
    container.classList.add('opening');
    container.classList.remove('closing');

    container.innerHTML = `<div class="loader"></div>`;

    const startTime = Date.now();
    const product = await fetchProductDetail(productId);
    const elapsed = Date.now() - startTime;
    let delay = elapsed < 300 ? 400 : elapsed < 1000 ? 200 : 0;

    if (!product) {
        setTimeout(() => {
            container.innerHTML = `<p>No product found</p>`;
        }, delay);
        return;
    }

    setTimeout(() => {
        container.innerHTML = `
            <div class="p-container">
                <div class="products-images">
                    <div class="img-pr">
                        <img src="${product.images[0]?.image}" alt="${product.name}" class="img-1">
                    </div>
                    <div class="img-pr-slide">
                        ${product.images.map(img => `<img src="${img.image}" alt="${product.name}">`).join('')}
                    </div>
                </div>

                <div class="product-info-d">
                    <div class="h-p">
                        <h2>${product.name}</h2>
                        <p>$${product.min_price}</p>
                    </div>
                    <div class="cart-buy">
                        <button class="cart-btn">Add To Cart <span class="material-icons-outlined">shopping_cart</span></button>
                        <button class="order-btn">ORDER NOW <span class="material-icons-outlined">local_shipping</span></button>
                    </div>
                    <div class="descriptions">
                        <h4>Description</h4>
                        <p>${product.description || "No description available."}</p>
                    </div>
                </div>
                <span class="close">+</span>
            </div>
        `;

        const pContainer = container.querySelector('.p-container');
        requestAnimationFrame(() => pContainer.classList.add('show'));

        const closeBtn = container.querySelector('.close');
        closeBtn.addEventListener('click', () => closeProductDetail());

        container.addEventListener('click', (e) => {
            if (!isMobileDevice() && e.target.id === 'product-detail') closeProductDetail();
        });

        const mainImage = container.querySelector('.img-1');
        const thumbnails = container.querySelectorAll('.img-pr-slide img');
        thumbnails.forEach(thumbnail => thumbnail.addEventListener('click', () => {
            mainImage.src = thumbnail.src;
        }));

        // Push new state when product is opened
        history.pushState({}, '', `/products/${productId}/`);
    }, delay);
}

export function closeProductDetail(skipHistory = false) {
    const container = document.getElementById('product-detail');
    container.classList.add('closing');
    setTimeout(() => {
        container.style.display = 'none';
        container.innerHTML = '';
    }, 300);
    if (!skipHistory) history.pushState({}, '', '/');
}

const searchList = document.getElementById('search-list')
const closeSearch = document.getElementById('close_search')
const searchGrid = document.getElementById('search-grid')

function showSearchResults(results){
    searchGrid.innerHTML = '';

}
