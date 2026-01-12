import { addToCart, isInCart } from "./cart.js";
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


export function showSkeletons(container, count = 6, append=false) {
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

    const container = document.getElementById('productsGrid');
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
            productElement.classList.add('product-card');
            productElement.innerHTML = `
            <a href="/product/detail/${product.id}/${product.slug}/" class="product-link">
                <div class="product-img">
                    <img src="${product.images[0]?.image}" alt="${product.name}">
                </div>
                <div class="product-info">
                    <h3 class="product-name">${product.name}</h3>
                    <p class="product-price">₡${product.price}</p>
                </div>
            </a>
            `;

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

export async function renderCategorySlider() {
  const track = document.getElementById('categoryTrack');
  const categories = await fetchCategories();
  const productHeader = document.querySelector('.product-header');

  if (!categories.length) {
    track.innerHTML = `<p style="text-align:center;">No categories found</p>`;
    return;
  }

   // Prepend a virtual "All Products" category
  const allOption = { id: 'all', name: 'All Products', image: null}; 
  // You can use any default image you like (or leave null to fetch one)
  const updatedCategories = [allOption, ...categories];

  const categoryHTML = await Promise.all(
    updatedCategories.map(async (cat) => {
      const imageUrl = cat.image_url || await getCachedCategoryImage(cat.name);

      return `
        <div class="category-item" data-id="${cat.id}" data-name="${cat.name}">
          <div class="category-circle">
            <img src="${imageUrl}" alt="${cat.name}">
          </div>
          <p class="category-name">${cat.name}</p>
        </div>
      `;
    })
  );

  track.innerHTML = categoryHTML.join('');

  // Clicking a category applies filter
  track.querySelectorAll('.category-item').forEach(item => {
    item.addEventListener('click', async () => {
      const categoryId = item.dataset.id;

      if (categoryId === 'all') {
        resetPagination();
        productHeader.textContent = 'All Products';
        await renderProducts();
        return;
      } else{
        const filters = { category_id: categoryId };
        resetPagination(filters);
        productHeader.textContent = item.dataset.name;
        await renderProducts(filters);
      }
    });
  });
}

const UNSPLASH_ACCESS_KEY = "pbRRkrnw3NFbDfGTumTxMiQgPIzULt01ZaUI_Ka9EIU";

async function getCategoryImage(categoryName) {
  try {
    const response = await fetch(
      `https://api.unsplash.com/search/photos?query=${encodeURIComponent(categoryName)}&per_page=1&client_id=${UNSPLASH_ACCESS_KEY}`
    );
    const data = await response.json();
    if (data.results && data.results.length > 0) {
      return data.results[0].urls.small;
    }
    return "https://via.placeholder.com/150?text=" + categoryName; // fallback
  } catch (err) {
    console.error("Unsplash error:", err);
    return "https://via.placeholder.com/150?text=" + categoryName;
  }
}

async function getCachedCategoryImage(categoryName) {
  const cacheKey = `cat_image_${categoryName.toLowerCase()}`;
  const cached = localStorage.getItem(cacheKey);
  if (cached) return cached;

  const url = await getCategoryImage(categoryName);
  localStorage.setItem(cacheKey, url);
  return url;
}

