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