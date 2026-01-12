import { getCSRFToken } from '../utils.js';
import { showSkeletons } from './products.js';

// wishlistManager.js
let wishlistIds = new Set();
let subscribers = [];

/** Initialize wishlist state (call once after fetching wishlist products) */
export function initWishlist(products) {
    wishlistIds = new Set(products.map(p => p.id));
    notifySubscribers();
}

/** Subscribe components (like product cards, wishlist page) */
export function subscribeWishlist(callback) {
    subscribers.push(callback);
    callback([...wishlistIds]); // run immediately for sync
}

/** Check if a product is in wishlist */
export function isWishlisted(productId) {
    return wishlistIds.has(productId);
}

export async function toggleWishList(productId, iconEl){
    try{
        const response = await fetch(`/products/api/wishlist/${productId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken(),
                'Content-Type': 'application/json'
            },
            credentials: 'include',
        })

        if (response.status === 403 || response.status === 401){
            // Not authenticated → redirect to login/signup
            const currentUrl = window.location.pathname + window.location.search;
            window.location.href = `/account/login/?next=${encodeURIComponent(currentUrl)}`;
            return;
        }

        if (!response.ok) throw new Error('Error favoriting a product')

        const data = await response.json()
        
        if (data.is_favorited) {
            wishlistIds.add(productId);
            if (iconEl) iconEl.classList.add("favorited");
        } else {
            wishlistIds.delete(productId);
            if (iconEl) iconEl.classList.remove("favorited");
        }

        notifySubscribers(); // 🔥 update all pages/components

        return data

    } catch(error){
        console.error('Something went wrong while adding to wishList: ' + error)
    }
}

function notifySubscribers() {
    const ids = [...wishlistIds];
    subscribers.forEach((cb) => cb(ids));
}

export function bindFavoriteIcon(favIcon, productId, onRemovedFromWishlist = null) {
    // Initial state
    if (isWishlisted(productId)) {
        favIcon.classList.add("favorited");
    } else {
        favIcon.classList.remove("favorited");
    }

    // Subscribe for global updates
    subscribeWishlist((wishlistIds) => {
        if (wishlistIds.includes(productId)) {
            favIcon.classList.add("favorited");
        } else {
            favIcon.classList.remove("favorited");

            // Optional callback for wishlist page → remove card
            if (onRemovedFromWishlist) {
                onRemovedFromWishlist();
            }
        }
    });

    // Toggle on click
    favIcon.addEventListener("click", (e) => {
        e.stopPropagation();
        toggleWishList(productId, favIcon);
    });
}

export async function renderWishList(data) {
    const container = document.querySelector('.wishlist-grid');

    // Clear current list & show skeletons
    container.innerHTML = '';
    showSkeletons(container, 8, false);

    const startTime = Date.now();
    const elapsed = Date.now() - startTime;
    const delay = elapsed < 300 ? 400 : (elapsed < 1000 ? 200 : 0);

    setTimeout(() => {
        container.querySelectorAll('.skeleton-card').forEach(el => el.remove());

        if (data.length === 0) {
            container.innerHTML = '<p>No products in your wishlist.</p>';
            return;
        }

        data.forEach(item => {
            const product = item.products;

            const productElement = document.createElement('div');
            productElement.classList.add('new');
            productElement.setAttribute('data-product-id', product.id);

            productElement.innerHTML = `
                <div class="new-product">
                    <div class="img-p">
                        <img src="${product.images[0]?.image || "/static/images/default.jpg"}" alt="${product.name}">
                    </div>
                    <div class="p-info">
                        <h4 class="product-name">${product.name}</h4>
                        <p>$${product.min_price}</p>
                    </div>
                    <span class="material-icons-outlined favorite-icon" data-product-id="${product.id}">
                        favorite_border
                    </span>
                </div>
            `;

            // Favorite toggle
            const favIcon = productElement.querySelector('.favorite-icon');
            bindFavoriteIcon(favIcon, product.id, ()=> {
                productElement.remove()
                if (!container.querySelector('.new')) {
                    container.innerHTML = '<p>No products in your wishlist.</p>';
                }
            })

            favIcon.addEventListener('click', (e) => {
                e.stopPropagation();
                toggleWishList(product.id, favIcon);
            });

            // Open detail
            productElement.addEventListener('click', (e) => {
                if (!e.target.classList.contains('favorite-icon')) {
                    const currentUrl = window.location.href;
                    renderProductDetail(product.id, currentUrl);
                }
            });

            container.appendChild(productElement);
        });
    }, delay);
}

export async function openWishlist(wishlistContainer, backURL = '/') {
    wishlistContainer.classList.add('opening');
    wishlistContainer.style.display = 'flex';
    document.body.style.overflow = "hidden";

    const openBtn = document.getElementById('nav-icon-2')
    const removeH = document.getElementById('nav-icon-1')

    openBtn.classList.add('active')
    removeH.classList.remove('active')

    try{
        const response = await fetch('/products/api/wishlist/');
        
        if (response.status === 403 || response.status === 401) {
            // User is not authenticated → redirect
            const currentUrl = window.location.pathname; // keep current location
            window.location.href = `/account/login/?next=${encodeURIComponent('/wishlist/')}`;
            return;
        }

        const data = await response.json();
        await renderWishList(data); // pass the already-fetched data

    } catch (error) {
        console.error(error);
    }

    // Push a new state for wishlist
    history.pushState({ backURL }, '', '/wishlist/');
}

export function closeWishlist(wishlistContainer, skipHistory = false) {
    wishlistContainer.classList.remove('opening');
    wishlistContainer.classList.add('closing');
    document.body.style.overflow = "auto";

    const openBtn = document.getElementById('nav-icon-2')
    const removeH = document.getElementById('nav-icon-1')

    openBtn.classList.remove('active')
    removeH.classList.add('active')

    setTimeout(() => {
        wishlistContainer.style.display = 'none';
        wishlistContainer.classList.remove('closing');
    }, 300);

    const state = history.state;

    if (!skipHistory) {
        if (state && state.backURL) {
            history.pushState({}, '', state.backURL);
        } else {
            history.pushState({}, '', '/');
        }
    }
}

function initWishlistNavigation(wishlistContainer) {
    // Listen to back/forward button presses
    window.addEventListener('popstate', (event) => {
        if (wishlistContainer.classList.contains('opening')) {
            // Wishlist is open, so close it
            closeWishlist(wishlistContainer, true);
        }
    });

    // Handle close button
    const closeBtn = wishlistContainer.querySelector('#close_wishlist');
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            closeWishlist(wishlistContainer);
        });
    }
}

async function getAllWishProducts(){
    try{
        const response = await fetch('/products/api/wishlist/');
        
        if(!response.ok){
            throw new Error('something went wrong while fetching favorite products')
        }

        const data = await response.json();
        return data

    } catch (error) {
        console.error(error);
        return [];
    }
}

export async function initWishListContainer(){
    const wishlistContainer = document.getElementById('wishlist-product')
    const closeBtn = document.getElementById('close_wishlist')
    const openBtn = document.getElementById('nav-icon-2')
    const removeH = document.getElementById('nav-icon-1')

    // 🔹 Initialize wishlist state when container loads
    const wishlistData = await getAllWishProducts();
    initWishlist(wishlistData.map(item => item.products));

    openBtn.addEventListener('click', (e)=> {
        openWishlist(wishlistContainer);
    })

    closeBtn.addEventListener('click', (e)=> {
        closeWishlist(wishlistContainer)
    })

    initWishlistNavigation(wishlistContainer)
}
