import { getCSRFToken } from "./utils.js";

export async function fetchUserProfile() {
    try{
        const response = await fetch('/account/api/profile/', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken(),
            },
        })

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        return data;

    } catch(error){
        console.error("Error fetching user profile:", error);
        return null;
    }
}

export async function setUserRole(role) {
    const response = await fetch('/account/api/profile/set-role/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({ role })
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.error || 'Failed to set role');
    }

    return data;
}
