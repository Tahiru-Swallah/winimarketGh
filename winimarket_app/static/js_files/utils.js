export function getCSRFToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}

// Cleaning email or Phone
export function IsEmail(value){
    return /\S+@\S+\.\S+/.test(value);
}

export function formatPhoneNumber(phone) {
    let cleaned = phone.replace(/\s+/g, ''); // remove spaces

    // If already in international format
    if (cleaned.startsWith('+233')) {
        return cleaned;
    }

    // If starts with 0 (local number)
    if (cleaned.startsWith('0')) {
        cleaned = cleaned.substring(1);
    }

    // Default: prepend Ghana country code
    return '+233' + cleaned;
}


export function isMobileDevice(){
    return /Mobi|Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
}