// Toggle between login and register forms
document.querySelectorAll('.toggle-link').forEach(link=> {
    link.addEventListener('click', e=> {
        e.preventDefault();
        document.querySelectorAll('.form-content').forEach(box=> {
            box.classList.toggle('active');
        });
    })
})

// get the csrf token from the cookies
function getCSRFToken(){
    let csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    return csrfToken;
}

// Google Sign In
window.onload = function () {
    google.accounts.id.initialize({
    client_id: "385739643247-oho5nt0tf63fvibo70mdrre9l18ah23l.apps.googleusercontent.com",
    auto_select: true, // ✅ force show account chooser
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
};

// Cleaning email or Phone
function IsEmail(value){
    return /\S+@\S+\.\S+/.test(value);
}

function formatPhoneNumber(phone){
    let cleaned = phone.replace(/\D/g, '');
    if(cleaned.startsWith('0')){
        cleaned = cleaned.substring(1);
    }

    return '+233' + cleaned;
}

function isMobileDevice(){
    return /Mobi|Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
}

if(isMobileDevice()){
    console.log("You are using a mobile device")
} else {
    console.log("You are using a desktop device")
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


// Handling login form submission
document.getElementById('loginForm').addEventListener('submit', async function(e){
    e.preventDefault();

    let email_or_phonenumber = document.getElementById("emailOrPhone").value;
    const password = document.getElementById("password").value;

    if (IsEmail(email_or_phonenumber)) {
        // If it's an email, no formatting needed
        email_or_phonenumber = email_or_phonenumber.toLowerCase().trim();
    } else {
        // If it's a phone number, format it
        email_or_phonenumber = formatPhoneNumber(email_or_phonenumber);
    }

    const params = new URLSearchParams(window.location.search);
    const next = params.get('next') || '/';

    try{

        const response = await fetch(`/account/api/login/?next=${encodeURIComponent(next)}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({
                email_or_phonenumber: email_or_phonenumber,
                password: password
            })
        })

        const data = await response.json();
        
        if(response.ok && data.access_token){
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('refresh_token', data.refresh_token);

            if(isMobileDevice()){
                showLoginMessage();
            } else{
                const loginMessage = document.querySelector('.login-message');
                loginMessage.textContent = 'Login Successful via Desktop. Redirecting...';
                loginMessage.style.display = 'flex';
                loginMessage.style.backgroundColor = 'var(--success-color)';
            }

            setTimeout(() => {
                window.location.href = data.next && data.next !== '/' ? data.next : '/';
            }, 1500); 

        } else {
            const loginMessage = document.querySelector('.login-message');
            
            if(isMobileDevice()){
                document.querySelectorAll('.input-field').forEach(field => {
                    field.style.borderColor = 'var(--error-color)';
                })

                setTimeout(() => {
                    document.querySelectorAll('.input-field').forEach(field => {
                        field.style.borderColor = 'var(--primary-color)';
                    })
                }, 1500);

            } else{
                loginMessage.textContent = data.error || 'Login Failed via Desktop, either email/phone or password is incorrect';
                loginMessage.style.display = 'flex';
                loginMessage.style.backgroundColor = 'var(--error-color)';
            }

            setTimeout(() => {
                loginMessage.style.display = 'none';
            }, 1500); 
        }

    } catch(error){
        console.error('Error:', error);
    }
})

document.getElementById('registerForm').addEventListener('submit', async function(e){
    e.preventDefault();

    const email = document.getElementById("email").value;
    let phonenumber = document.getElementById("phonenumber").value;
    const password = document.getElementById("password-").value;

    console.log('My password is: ' + password)

    phonenumber = formatPhoneNumber(phonenumber);

    const params = new URLSearchParams(window.location.search);
    const next = params.get('next') || '/';

    try{

        const response = await fetch(`/account/api/register/?next=${encodeURIComponent(next)}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({
                email: email.toLowerCase().trim(),
                phonenumber: phonenumber,
                password: password
            })
        })

        const data = await response.json()

        if (response.ok){
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('refresh_token', data.refresh_token);

            if(isMobileDevice()){
                showLoginMessage();
            } else{
                const loginMessage = document.querySelector('.login-message');
                loginMessage.textContent = 'Registration Successful via Desktop. Redirecting...';
                loginMessage.style.display = 'flex';
                loginMessage.style.backgroundColor = 'var(--success-color)';
            }

            setTimeout(() => {
                window.location.href = data.next && data.next !== '/' ? data.next : '/account/profile/';
            }, 1500)

        } else{
            const loginMessage = document.querySelector('.login-message');

            if(isMobileDevice()){
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
                    } else {
                        err.textContent = 'Registration Failed, please try again';
                    }
                    err.style.color = 'var(--error-color)';
                })

                setTimeout(() => {
                    document.querySelectorAll('.input-field').forEach(field => {
                        field.style.borderColor = 'var(--primary-color)';
                    })
                }, 1500);

            } else{
                loginMessage.textContent = data.error || 'Registration Failed via Desktop, please try again';
                loginMessage.style.display = 'flex';
                loginMessage.style.backgroundColor = 'var(--error-color)';
            }

            setTimeout(() => {
                loginMessage.style.display = 'none';
            }, 1500);
        }

    } catch(error){
        console.error('Error:', error);
    }
})