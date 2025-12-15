import { getCSRFToken, IsEmail, isMobileDevice, formatPhoneNumber } from "./utils.js";
import { fetchUserProfile, setUserRole } from "./profile_setup.js";


// Toggle between login and register forms
document.querySelectorAll('.toggle-link').forEach(link=> {
    link.addEventListener('click', e=> {
        e.preventDefault();
        document.querySelectorAll('.form-content').forEach(box=> {
            box.classList.toggle('active');
        });
    })
})

const client_id = document.querySelector('meta[name="google-client-id"]').getAttribute('content')

// Google Sign In
window.onload = function () {
    google.accounts.id.initialize({
    client_id: client_id,
    callback: "",
    auto_select: false, // ✅ force show account chooser
    cancel_on_tap_outside: false,
    context: 'signin'
    });

    document.querySelectorAll('#g_id_signin').forEach(function(signin) {
        google.accounts.id.renderButton(
            signin, {
                theme: "outline",
                size: "large",
                type: "standard",
                text: "continue_with",
                shape: "rectangular"
            }
        );
    });

    google.accounts.id.prompt();
};

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

document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault()

    let email_or_phonenumber = document.getElementById('emailOrPhone').value
    const password = document.getElementById('password').value

    if (IsEmail(email_or_phonenumber)){
        email_or_phonenumber = email_or_phonenumber.toLowerCase().trim()
    } else{
        email_or_phonenumber = formatPhoneNumber(email_or_phonenumber)
    }

    const params = new URLSearchParams(window.location.search)
    const next = params.get('next') || '/';

    try{
        const response = await fetch(`/account/api/login/?next=${encodeURIComponent(next)}`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken(),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email_or_phonenumber: email_or_phonenumber,
                password: password
            })
        })

        const data = await response.json()

        if(response.ok && data.access_token){
            if(isMobileDevice()){
                showLoginMessage()

            } else{
                document.querySelector('.login-message').style.display = 'flex'
            } 

            setTimeout(() => {
                window.location.href = data.next && data.next !== '/' ? data.next : '/';
            }, 1500);

        } else if (data.email_or_phonenumber || data.password){
            const loginMessage = document.querySelector('.login-message');

            if (isMobileDevice()){
                document.querySelectorAll('.input-field').forEach(field => {
                    field.style.borderColor = 'var(--error-color)';
                })

                document.querySelectorAll('.error').forEach(e => {
                    e.innerHTML = '<p>Incorrect email/phone or password</p>'
                    e.style.color = 'var(--error-color)'
                })

                setTimeout(() => {
                    document.querySelectorAll('.input-field').forEach(field => {
                        field.style.borderColor = 'var(--primary-color)';
                    })

                    document.querySelectorAll('.error').forEach(e => {
                        e.innerHTML = ''
                    })

                }, 1500);

            } else{
                loginMessage.textContent = 'Email/Phone or password is incorrect';
                loginMessage.style.display = 'flex';
                loginMessage.style.backgroundColor = 'var(--error-color)';

                document.querySelectorAll('.input-field').forEach(field => {
                    field.style.borderColor = 'var(--error-color)';
                })

                setTimeout(() => {
                    document.querySelectorAll('.input-field').forEach(field => {
                        field.style.borderColor = 'var(--primary-color)';
                    })

                }, 1500);
            }

            setTimeout(() => {
                loginMessage.style.display = 'none';
            }, 1500); 
        }

    } catch(error){
        console.log('Something went wrong: ' + error)
    }
})

document.getElementById('registerForm').addEventListener('submit', async (e) => {
    e.preventDefault()

    const email = document.getElementById('email').value
    let phonenumber = document.getElementById('phonenumber').value
    const password = document.getElementById('password-').value

    phonenumber = formatPhoneNumber(phonenumber)

    const params = new URLSearchParams(window.location.search)
    const next = params.get('next') || '/'

    try{
        const response = await fetch(`/account/api/register/?next=${encodeURIComponent(next)}`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken(),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email: email.toLowerCase().trim(),
                phonenumber: phonenumber,
                password: password
            })
        })

        const data = await response.json()

        if (response.ok){
            if(isMobileDevice()){

                const loginMessage = document.querySelector('.login-message-mobile');
                const text = loginMessage.querySelector('.text h4')

                text.textContent = 'Registration Successful.'

                loginMessage.classList.add('show')

                setTimeout(() => {
                    loginMessage.classList.add('hide');
                    setTimeout(() => {
                        loginMessage.classList.remove('show', 'hide');
                        loginMessage.style.display = 'none';
                    }, 300);
                }, 1500)

            } else{
                const loginMessage = document.querySelector('.login-message')
                const text = loginMessage.querySelector('.text h4')

                text.textContent = 'Registration Successful.'

                loginMessage.style.display = 'flex'
            } 

            setTimeout(() => {
                handleRoleCheck();
            }, 1500);

        } else if(data.errors){

            document.querySelectorAll('.input-field').forEach(field => {
                field.style.borderColor = 'var(--error-color)';
            })

            document.querySelectorAll('.error').forEach(err => {
                if (data.errors.phonenumber){
                    err.textContent = data.errors.phonenumber[0];
                } else if (data.errors.email){
                    err.textContent = data.errors.email[0];
                } else if (data.errors.password){
                    err.textContent = data.errors.password[0];
                } else if(data.errors.full_name) {
                    err.textContent = data.errors.full_name[0];
                } else {
                    err.textContent = 'Registration failed, please try again'
                }
                err.style.color = 'var(--error-color)';
            })

            setTimeout(() => {
                document.querySelectorAll('.input-field').forEach(field => {
                    field.style.borderColor = 'var(--primary-color)';
                })
            }, 1500);
        }

    } catch(error){
        console.error('Something went wrong: ' + error)
    }
})

async function handleRoleCheck(){
    const profile =  await fetchUserProfile();

    if (!profile){
        return;
    }

    if (!profile.role_confirmed){
        openModal();
        closeRegisterForm();
    }
}

function openModal(){
    document.getElementById('roleSelectionModal').classList.remove('hidden');
}

function closeRegisterForm(){
    document.getElementById('form-card').style.display = 'none';
    document.querySelector('.login-message').style.display = 'none';
    document.querySelector('.login-message-mobile').style.display = 'none';
}

function hideRoleModal() {
    document.getElementById('roleSelectionModal').classList.add('hidden');
}

document.getElementById('buyerRole').addEventListener('click', async () => {
    try {
        await setUserRole('buyer');
        hideRoleModal();
        // NEXT STEP: buyer profile popup
        showBuyerProfileModal()
    } catch (error) {
        console.error('Error setting role to buyer:', error);
    }
});

document.getElementById('sellerRole').addEventListener('click', async () => {
    try {
        await setUserRole('seller');
        window.location.href = '/account/seller/onboarding/';
    } catch (error) {
        console.error('Error setting role to seller:', error);
    }
});

function showBuyerProfileModal() {
    document.getElementById('buyerProfileModal').classList.remove('hidden');

    document.getElementById('buyerFullName').focus();
}

function hideBuyerProfileModal() {
    document.getElementById('buyerProfileModal')
        .classList.add('hidden');
}

document.getElementById("buyerProfileForm").addEventListener("submit", async (e) => {
    e.preventDefault()

    const errorBox = document.getElementById("buyerProfileError")
    errorBox.textContent = "";

    const fullName = document.getElementById("buyerFullName").value.trim()
    const profilePicture = document.getElementById("buyerProfilePicture").files[0]

    if(!fullName){
        errorBox.textContent = "Full name is required."
        return;
    }

    const formData = new FormData()
    formData.append("full_name", fullName)

    if (profilePicture){
        formData.append('profile_picture', profilePicture)
    }

    try{
        const response = await fetch("/account/api/profile/", {
            method: 'PUT',
            headers: {
                "X-CSRFToken": getCSRFToken()
            },
            body: formData
        })

        const data = await response.json()

        if (!response.ok){
            throw new Error(
                data?.full_name?.[0] ||
                data?.profile_picture?.[0] ||
                'Failed to update profile'
            )
        }

        showToast("Buyer profile setup complete!", "success");

        setTimeout(() => {
            window.location.href = '/';
        }, 1500);   

    } catch(error){
        errorBox.textContent = error.message;
        showToast(error.message, "error");
    }
})

function showToast(message, type = "success") {
    const container = document.getElementById("toast-container");
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);

    // Auto remove after animation
    setTimeout(() => toast.remove(), 4000);
}