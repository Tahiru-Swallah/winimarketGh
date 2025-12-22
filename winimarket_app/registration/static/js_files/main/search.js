import { showSkeletons } from './products.js'
import { toggleWishList, bindFavoriteIcon } from './wishlist.js'

async function fetchSuggestion(query){
    try{
        const response = await fetch(`/product/api/search/suggestions/?q=${encodeURIComponent(query)}`)

        if(!response.ok) throw new Error('Error fetching suggestions')
        const data = await response.json()

        return data;

    } catch(error){
        console.error( 'Somthing went wrong trying to fetch search suggestion: ' + error)
        return [];
    }
}

function renderSuggestions(suggestions, searchSuggestions, runSearch){
    searchSuggestions.innerHTML = ''

    suggestions.forEach(suggestion => {
        let item = document.createElement('div')
        item.classList.add('search-suggestion-item')
        item.innerHTML = `
            <span class="material-icons-outlined">search</span>
            <span>${suggestion.name}</span>
        `
        item.addEventListener('click', () => {
            runSearch(suggestion.name)
        })
        searchSuggestions.appendChild(item)
    })
}

async function fetchSearchResults(query, page = 1){
    try{
        const response = await fetch(`/product/api/search/?q=${encodeURIComponent(query)}&page=${page}`)

        if (!response.ok) throw new Error('Something went wrong while fetching search results')

        const data = await response.json()
        return data;

    } catch(error){
        console.error(error)
        return {results: [], next: null}
    }
}

let currentPage = 1
let loading = false
let hasMore = true
let lastQuery = ''

async function renderSearchResults(query, searchGrid, append=false){
    if (loading || !hasMore) return;
    loading = true;

    if (!append) {
        currentPage = 1;
        hasMore = true;
        searchGrid.innerHTML = "";
        showSkeletons(searchGrid, 8, false);
    }

    lastQuery = query;

    const startTime = Date.now();
    const data = await fetchSearchResults(query, currentPage);
    const elapsed = Date.now() - startTime;

    // Delay removal if API is too fast (to let skeletons "flash" at least 300ms)
    const delay = elapsed < 300 ? 400 : (elapsed < 1000 ? 200 : 0);

    setTimeout(() => {
        // Remove skeletons
        searchGrid.querySelectorAll('.skeleton-card').forEach(el => el.remove());

        if (data.results.length === 0 && currentPage === 1) {
            searchGrid.innerHTML = `<p>No results found for "${query}"</p>`;
            hasMore = false;
            loading = false;
            return;
        }

        data.results.forEach(product => {
            let item = document.createElement('div');
            item.classList.add('search-list-item');
            item.innerHTML = `
                <div class="search-item-thumbnail">
                    <img src="${product.images[0]?.image}" alt="${product.name}">
                </div>
                <div class="search-item-info">
                    <h3>${product.name}</h3>
                    <p>$${product.min_price}</p>
                </div>
                <span class="material-icons-outlined favorite-icon" data-product-id="${product.id}">favorite_border</span>
            `;

            item.addEventListener('click', async (e) => {
                if (e.target.classList.contains('favorite-icon')) return;
                const currentURL = window.location.href;
                await renderProductDetail(product.id, currentURL);
            });

            const favIcon = item.querySelector('.favorite-icon')
            bindFavoriteIcon(favIcon, product.id)

            searchGrid.appendChild(item);
        });

        hasMore = data.next !== null;
        if (hasMore) currentPage++;

        loading = false;
    }, delay);
}


// ====== SEARCH INFINITE SCROLL ======
export function initSearchInfiniteScroll(searchList, searchGrid) {
    searchList.addEventListener("scroll", () => {
        const { scrollTop, scrollHeight, clientHeight } = searchList;
        if (scrollTop + clientHeight >= scrollHeight - 100) {
            if (lastQuery) {
                renderSearchResults(lastQuery, searchGrid, true);
            }
        }
    });
}

async function runSearch(query, searchSuggestions, searchList, searchGrid){
    if (!query) return;

    searchSuggestions.style.display = 'none'

    searchList.classList.add('opening')
    searchList.style.display = 'flex'

    // 🔥 hide scrollbar
    document.body.style.overflow = "hidden";

    currentPage = 1
    hasMore = true
    lastQuery = query

    await renderSearchResults(query, searchGrid)

    const searchInput = document.querySelector('.search-input');
    const closeBtn = document.querySelector('.icon');
    if (searchInput) searchInput.value = query

    if (searchInput.value.length > 0) closeBtn.style.display = 'flex';

    updateSearchURL(query)
}

function updateSearchURL(query) {
    const url = new URL(window.location)
    url.searchParams.set("search", query)
    window.history.pushState({ search: query }, "", url)
}


function closeSearchOverlay(searchList, skipHistory=false){
    searchList.classList.remove('opening')
    searchList.classList.add('closing')
    document.body.style.overflow = "auto";

    setTimeout(() => {
        searchList.style.display = 'none';
        searchList.classList.remove('closing')

        const searchInput = document.querySelector('.search-input');
        if (searchInput) searchInput.value = '';
    }, 3000)

    if(!skipHistory){
        const url = new URL(window.location)
        url.searchParams.delete('search')
        window.history.pushState({}, "", url)
    }
}

export function initSearch(){
    const searchInput = document.querySelector('.search-input')
    const searchSuggestions = document.getElementById('search-suggestion')
    const searchList = document.querySelector(".search-list")
    const closeSearch = document.getElementById('close_search')
    const searchGrid = document.getElementById('search-grid')
    const closeBtn = document.querySelector('.icon')

    searchInput.addEventListener('input', async (e) => {
        const query = e.target.value.trim()

        if(!query){
            searchSuggestions.style.display = 'none'
            if(searchInput.value.length > 0) closeBtn.style.display = 'none';
            return;
        } else{
            searchSuggestions.style.display = 'block'
            closeBtn.style.display = 'flex'
        }

        const suggestions = await fetchSuggestion(query)
        renderSuggestions(suggestions, searchSuggestions, (q) => {
            runSearch(q, searchSuggestions, searchList, searchGrid)
        });
    })

    searchInput.addEventListener('keydown', (e) => {
        if(e.key === 'Enter'){
            runSearch(searchInput.value.trim(), searchSuggestions, searchList, searchGrid)
        }
    });

    closeSearch.addEventListener('click', () => closeSearchOverlay(searchList))
    closeBtn.addEventListener('click', () => {
        closeSearchOverlay(searchList)
        searchInput.value = '';
        searchSuggestions.style.display = 'none';
    })

    window.addEventListener('popstate', (event) => {
        const params = new URLSearchParams(window.location.search)
        const query = params.get('search')

        if(query){
            runSearch(query, searchSuggestions, searchList, searchGrid)
        } else{
            searchList.style.display = 'none'
        }
    })

    const params = new URLSearchParams(window.location.search)
    const query = params.get('search')
    if (query) {
        runSearch(query, searchSuggestions, searchList, searchGrid)
    }
}