import { getCSRFToken } from '../utils.js';  // make sure path is correct

let cartState = new Set();
let subscribers = [];

export function initCart(cartItems = []) {
    if (!Array.isArray(cartItems)) {
        console.warn("initCart received non-array:", cartItems);
        cartItems = [];
    }

    cartState = new Set(cartItems.map(item => item.product.id));
    notifySubscribers();
}

export function isInCart(productId) {
    return cartState.has(productId);
}

export async function addToCart(productId, quantity = 1, choice_price = null) {
  try {
    const body = { product_id: productId, quantity };
    if (choice_price !== null && choice_price !== undefined) {
      body.choice_price = String(choice_price);
    }

    const response = await fetch('/cart/api/add/', {
      method: 'POST',
      headers: {
        'X-CSRFToken': getCSRFToken(),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    if (response.status === 401 || response.status === 403) {
      const currentUrl = window.location.href;
      window.location.href = `/account/login/?next=${encodeURIComponent(currentUrl)}`;
      return null;
    }

    if (!response.ok) {
      const errData = await response.json().catch(() => null);
      throw new Error(errData?.error || response.statusText || 'Something went wrong while adding to cart');
    }

    const data = await response.json();

    if(data.is_in_cart){
        cartState.add(productId)
    } else{
        cartState.delete(productId)
    }

    notifySubscribers()

    return data;

  } catch (error) {
    console.error('addToCart error:', error);
    throw error; // let caller show UI feedback
  }
}

function notifySubscribers() {
    subscribers.forEach(cb => cb([...cartState]));
}

export function subscribeCart(cb) {
    subscribers.push(cb);
}

async function getCartProducts(){
    try{
        const response = await fetch('/cart/api/view/')

        if(!response.ok){
            throw new Error('Something went wrong while fetching')
        }

        const data = await response.json()
        return data

    } catch(error){
        console.error(error)
        return []
    }
}

export async function initCartContainer(){
    try {
        const { items, total } = await getCartProducts();
        initCart(items || []);   // always pass an array
    } catch (err) {
        console.error("Error initializing cart:", err);
        initCart([]); // fallback to empty
    }
}

async function fetchCartData(){
  try{
    const response = await fetch('/cart/api/view/')

    if (response.status === 401 || response.status === 403){
      const currentUrl = window.location.pathname
      window.location.href = `/account/login/?next=${encodeURIComponent('/products/cart/')}`;
      return null;
    }

    if(!response.ok){
      throw new Error('Failed to fetch, please try again.')
    }

  } catch(error){
    console.error('Something went wrong while fetching data, ' + error)
    return [];
  }
}


export async function renderCart(data){
  const cartContainer = document.getElementById('cart-container-grid')
  const cartWrapper = cartContainer.querySelector('.cart-products')
  const cartSummary = cartContainer.querySelector('#cart-summary')

  if(!data){
    showCartSkeletons(cartWrapper, 3)
    return;
  };

  console.log(data)

  const items = data.items || null;
  const total = data.total || 0;

  cartWrapper.innerHTML = ''

  if (items.length === 0){
    cartWrapper.innerHTML = '<p>Yor cart is empty.</p>'
    cartSummary.querySelector('.cart-total-price').textContent = '$0.00'
    return;
  }

  items.forEach((item) => {
    const product = item.product
    const cartElem = document.createElement('div')
    cartElem.classList.add('cart-show')
    cartElem.setAttribute('data-cart-id', item.id)

    cartElem.innerHTML = `
      <div class="c-im">
        <div class="cart-img">
            <img src="${product.images[0]?.image}" alt="${product.name}">
        </div>
        <div class="cart-info">
            <h2>${product.name}</h2>
            <p class="price">$${product.min_price}</p>
            <p class="seller">Seller: <span>${product.seller?.store_name || 'Uknown'}</span></p>
        </div>
      </div>
      <div class="cart-quantity">
          <button class="decrease" data-cart-id="${item.id}">-</button>
          <span class="quantity">${item.quantity}</span>
          <button class="increase" data-cart-id="${item.id}">+</button>
      </div>
      <span class="delete-cart" data-cart-id="${item.id}">+</span>
    `

    cartWrapper.appendChild(cartElem)
  })

  cartSummary.querySelector('.cart-total-price').textContent = `$${total.toFixed(2)}`

  attachCartListeners()
}

function attachCartListeners(){
  document.querySelectorAll('.increase').forEach(btn =>{
    btn.addEventListener('click', () => {
      const cartId = btn.dataset.cartId
      updateQuantity(cartId, 1)
    })
  })

  document.querySelectorAll('.decrease').forEach(btn => {
    btn.addEventListener('click', ()=> {
      const cartId = btn.dataset.cartId
      updateQuantity(cartId, -1)
    })
  })

  document.querySelectorAll('.delete-cart').forEach(btn => {
    btn.addEventListener('click', () => {
      const cartId = btn.dataset.cartId
      deleteCartItem(cartId)
    })
  })
}

async function updateQuantity(cartId, change){
  try{ 

    const quantityEl = document.querySelector(`.cart-show[data-cart-id=${cartId}].quantity`)
    let newQuantity = parseInt(quantityEl.textContent, 10) + change;

    if(newQuantity < 1){
      return;
    }

    const response = await fetch(`/cart/api/update/${cartId}/`, {
      method: 'PATCH',
      headers: {
        'X-CSRFToken': getCSRFToken(),
        'Content-Type': 'application/json'
      },
      credentials: 'include',
      body: JSON.stringify({quantity: newQuantity})
    })

    if (!response.ok){
      const errorData = await response.json()
      throw new Error(errorData?.error || 'Failed to update')
    }

    await renderCart()

  } catch(error){
    console.error(error)
  }
}

async function deleteCartItem(cartId){
  try{
    const response = await fetch(`/cart/api/remove/${cartId}/`, {
      method: 'DELETE',
      headers: {
        'X-CSRFToken': getCSRFToken()
      }
    })

    if(!response.ok){
      const errorData = await response.json()
      throw new Error(errorData?.error || 'failed to delete')
    }

    await renderCart()

  } catch(error){
    console.error(error)
  }
}

async function openCartContainer(cartContainer, backURL = '/'){
  cartContainer.classList.add('opening');
  cartContainer.style.display = 'flex';
  document.body.style.overflow = "hidden";

  const removeH = document.getElementById('nav-icon-1')
  const removeW = document.getElementById('nav-icon-2')
  const removeC = document.getElementById('nav-icon-3')
  const removeP = document.getElementById('nav-icon-4')
  const removeO = document.getElementById('nav-icon-5')

  removeC.classList.add('active')
  removeH.classList.remove('active')
  removeO.classList.remove('active')
  removeW.classList.remove('active')
  removeP.classList.remove('active')

  try{
        const response = await fetch('/cart/api/view/');
        
        if (response.status === 403 || response.status === 401) {
            // User is not authenticated → redirect
            const currentUrl = window.location.pathname; // keep current location
            window.location.href = `/account/login/?next=${encodeURIComponent('/products/cart/')}`;
            return;
        }

        const data = await response.json()
        await renderCart(data)

    } catch (error) {
        console.error(error);
    }

    history.pushState({ backURL }, '', '/products/cart/')
}

function closeCartContainer(cartContainer, skipHistory = false){
  cartContainer.classList.add('closing');
  cartContainer.style.display = 'flex';
  document.body.style.overflow = "auto";

  const removeH = document.getElementById('nav-icon-1')
  const removeW = document.getElementById('nav-icon-2')
  const removeC = document.getElementById('nav-icon-3')
  const removeP = document.getElementById('nav-icon-4')
  const removeO = document.getElementById('nav-icon-5')

  removeC.classList.remove('active')
  removeH.classList.add('active')
  removeO.classList.remove('active')
  removeW.classList.remove('active')
  removeP.classList.remove('active')

  setTimeout(() => {
    cartContainer.style.display = 'none'
    cartContainer.classList.remove('closing')
  }, 300)

  const state = history.state;

  if (!skipHistory) {
      if (state && state.backURL) {
          history.pushState({}, '', state.backURL);
      } else {
          history.pushState({}, '', '/');
      }
  }
}

export async function displayCartContainer(){
  const cartContainer = document.querySelector('.cart-container')
  const closeBtn = document.getElementById('close_cart')
  const openBtn = document.getElementById('nav-icon-3')

  closeBtn.addEventListener('click', ()=> {closeCartContainer(cartContainer)})
  openBtn.addEventListener('click', () => {openCartContainer(cartContainer)})
}

function showCartSkeletons(container, count = 3) {
  for (let i = 0; i < count; i++) {
    const skeleton = document.createElement('div')
    skeleton.classList.add('cart-skeleton')

    skeleton.innerHTML = `
      <div class="skeleton-img"></div>
      <div class="skeleton-info">
        <div class="skeleton-line short"></div>
        <div class="skeleton-line long"></div>
      </div>
    `
    container.appendChild(skeleton)
  }
}
