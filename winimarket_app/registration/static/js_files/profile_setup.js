function getCSRFToken(){
    let csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    return csrfToken;
}

function isMobileDevice(){
    return /Mobi|Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
}

function showLoginMessage() {
    const loginMessage = document.querySelector('.login-message-mobile');
    loginMessage.classList.add('show');

    setTimeout(() => {
        loginMessage.classList.add('hide');
        setTimeout(() => {
            loginMessage.classList.remove('show', 'hide');
            loginMessage.style.display = 'none';
        }, 300);
    }, 2000);
}


let profile = document.getElementById('show-profile')
let avatar = document.getElementById('avatar')

avatar.addEventListener('change', () => {
    profile.src = URL.createObjectURL(avatar.files[0])
})

document.getElementById('profileForm').addEventListener('submit', async function(e){
    e.preventDefault()

    const formData = new FormData()
    const csrfToken = getCSRFToken()
    const fullName = document.getElementById('buyer-name').value
    const avatar = document.getElementById('avatar').files[0]

    formData.append('full_name', fullName)
    if (avatar){
        formData.append('profile_pic', avatar)
    }

    try{
        const response = await fetch('/account/api/profile/', {
            method: 'PUT',
            headers: {
                'X-CSRFToken': csrfToken,
            },
            credentials: 'include',
            body: formData
        })

        const data = await response.json()

        if (response.ok){
            if(isMobileDevice()){
                showLoginMessage()
            }

            setTimeout(() => {
                window.location.href = '/account/';
            }, 2000);

        } else{
            console.error('Error:', data.error || 'An error occurred while setting up the profile.');
        }

    } catch(error){
        console.error("Submission failed:", error);
    }
})