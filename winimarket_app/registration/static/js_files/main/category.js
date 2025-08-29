export async function fetchCategories (){
    try{
        const response = await fetch('/products/api/categories/')

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const categories = await response.json();
        return categories;

    } catch(error){
        console.error("Error fetching categories:", error);
    }
}

export async function renderCategories(){
    const categories = await fetchCategories()
    console.log(categories)

    const selectCategory = document.getElementById('select-category')

    categories.forEach(cat=> {
        const option = document.createElement('option')
        option.textContent = cat.name
        option.value = cat.id

        selectCategory.appendChild(option)
    })
}