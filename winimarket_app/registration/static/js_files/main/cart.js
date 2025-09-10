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
