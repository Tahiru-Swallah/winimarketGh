import { renderProductDetail } from './products.js'

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

async function fetchSearchResults(query){
    try{
        const response = await fetch(`/product/api/search/?q=${encodeURIComponent(query)}`)

        if (!response.ok) throw new Error('Something went wrong while fetching search results')

        const data = await response.json()
        console.log('data from search ', data)
        return data;

    } catch(error){
        console.error(error)
    }
}

function renderSearchResults(data, searchGrid){
    searchGrid.innerHTML = "";

    data.results.forEach(product => {
        let item = document.createElement('div')
        item.classList.add('search-list-item')
        item.innerHTML = `
            <div class="search-item-thumbnail">
                <img src="${product.images[0]?.image}" alt='${product.name}'>
            </div>
            <div class="search-item-info">
                <h3>${product.name}</h3>
                <p>$${product.min_price}</p>
            </div>
            <span class="material-icons-outlined favorite-icon">favorite_border</span>
        `

        item.addEventListener('click', async (e) => {
            if(e.target.classList.contains('favorite-icon')) return;
            
            const currentURL = window.location.href

            await renderProductDetail(product.id, currentURL)
        })

        searchGrid.appendChild(item)
    })
}

async function runSearch(query, searchSuggestions, searchList, searchGrid){
    if (!query) return;

    searchSuggestions.style.display = 'none'

    searchList.classList.add('opening')
    searchList.style.display = 'flex'

    // 🔥 hide scrollbar
    document.body.style.overflow = "hidden";

    const data = await fetchSearchResults(query)
    renderSearchResults(data, searchGrid)

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