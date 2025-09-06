import { getCSRFToken } from '../utils.js';

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
        
        if (data.is_favorited === true){
            iconEl.classList.add('favorited')
        } else{
            iconEl.classList.remove('favorited')
        }

        await getAllWishProducts()

    } catch(error){
        console.error('Something went wrong while adding to wishList: ' + error)
    }
}

async function getAllWishProducts(){
    try{
        const response = await fetch('/products/api/wishlist/')
        const data = await response.json()

        console.log(data)
    } catch(error){
        console.error(error)
    }
}