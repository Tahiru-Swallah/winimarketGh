import { getCSRFToken } from "./utils.js";

// ===============================
// FILE HANDLER
// ===============================
function handleFileInput(fileInput, previewContainerId, maxSizeMB = 5) {
    const previewContainer = document.getElementById(previewContainerId);
    previewContainer.innerHTML = ''; // Clear previous preview

    const file = fileInput.files[0];
    if (!file) return;

    // Validate size
    if (file.size > maxSizeMB * 1024 * 1024) {
        showError(`File size must be less than ${maxSizeMB}MB`, fileInput);
        fileInput.value = '';
        return;
    }

    // Validate type
    if (!file.type.startsWith('image/')) {
        showError('Invalid file type. Only images are allowed.', fileInput);
        fileInput.value = '';
        return;
    }

    // Create thumbnail preview
    const reader = new FileReader();
    reader.onload = function (e) {
        const img = document.createElement('img');
        img.src = e.target.result;
        img.alt = 'Preview';
        img.style.width = '100px';
        img.style.height = '100px';
        img.style.objectFit = 'cover';
        img.style.borderRadius = '8px';
        img.style.marginTop = '8px';
        previewContainer.appendChild(img);
    };
    reader.readAsDataURL(file);
}

// ===============================
// FILE INPUT LISTENERS
// ===============================
const storeLogoInput = document.getElementById('storeLogo');
storeLogoInput.addEventListener('change', () => {
    handleFileInput(storeLogoInput, 'storeLogoPreview');
});

const idCardInput = document.getElementById('idCardImage');
idCardInput.addEventListener('change', () => {
    handleFileInput(idCardInput, 'idCardPreview');
});

const selfieInput = document.getElementById('selfieWithId');
selfieInput.addEventListener('change', () => {
    handleFileInput(selfieInput, 'selfiePreview');
});

/* ===============================
   GLOBAL STATE
================================ */
let currentStep = 1;
const totalSteps = 4;

const steps = document.querySelectorAll('.step');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');

const nextBtn = document.getElementById('nextBtn');
const backBtn = document.getElementById('prevBtn');

const errorCard = document.getElementById('errorCard');
const errorText = document.getElementById('errorText');

/* ===============================
   UI HELPERS
================================ */
function showError(message, inputField = null) {
    errorText.textContent = message;
    errorCard.hidden = false;

    if (inputField) {
        inputField.classList.add('input-error');
    }
}

function clearError() {
    errorText.textContent = '';
    errorCard.hidden = true;
}

function updateProgress() {
    const percent = (currentStep / totalSteps) * 100;
    progressFill.style.width = `${percent}%`;
    progressText.textContent = `Step ${currentStep} of ${totalSteps}`;
}

function showStep(step) {
    steps.forEach((s, index) => {
        s.classList.toggle('active', index === step - 1);
    });

    backBtn.disabled = step === 1;
    nextBtn.textContent = step === totalSteps ? 'Submit' : 'Continue';

    updateProgress();
    clearError();
}

/* ===============================
   API CALLS
================================ */
async function submitStoreInfo() {
    const storeName = document.getElementById('storeName').value.trim();
    const storeDescription = document.getElementById('storeDescription').value.trim();
    const storeLogo = document.getElementById('storeLogo').files[0];

    if (!storeName) {
        throw { detail: "Store name is required." };
    }

    const data = new FormData();
    data.append('store_name', storeName);
    data.append('store_description', storeDescription);
    if (storeLogo) data.append('store_logo', storeLogo);

    const res = await fetch('/account/api/seller-profile/', {
        method: 'POST',
        headers: { 'X-CSRFToken': getCSRFToken() },
        body: data
    });

    if (!res.ok) throw await res.json();
}

async function submitAddressInfo() {
    const region = document.getElementById('region').value.trim();
    const city = document.getElementById('city').value.trim();

    if (!region || !city) {
        throw { detail: "Region and city are required." };
    }

    const data = new FormData();
    data.append('country', 'Ghana');
    data.append('region', region);
    data.append('city', city);
    data.append('address', document.getElementById('address').value.trim());

    const res = await fetch('/account/api/seller-address/', {
        method: 'PUT',
        headers: { 'X-CSRFToken': getCSRFToken() },
        body: data
    });

    if (!res.ok) throw await res.json();
}

async function submitPaymentInfo() {
    const momoNumber = document.getElementById('momoNumber').value.trim();

    if (!momoNumber) {
        throw { detail: "MoMo number is required." };
    }

    const data = new FormData();
    data.append('momo_name', document.getElementById('momoName').value.trim());
    data.append('momo_number', momoNumber);
    data.append('bank_name', document.getElementById('bankName').value.trim());
    data.append('bank_account', document.getElementById('bankAccount').value.trim());

    const res = await fetch('/account/api/seller-payment-info/', {
        method: 'PUT',
        headers: { 'X-CSRFToken': getCSRFToken() },
        body: data
    });

    if (!res.ok) throw await res.json();
}

async function submitVerification() {
    const idType = document.getElementById('idType').value;
    const idNumber = document.getElementById('idNumber').value.trim();
    const idCard = document.getElementById('idCardImage').files[0];
    const selfie = document.getElementById('selfieWithId').files[0];

    console.log(idType, idNumber, idCard, selfie);

    if (!idType || !idNumber || !idCard || !selfie) {
        throw { detail: "All verification fields are required." };
    }

    const data = new FormData();
    data.append('id_type', idType);
    data.append('id_number', idNumber);
    data.append('id_card_image', idCard);
    data.append('selfie_with_id', selfie);

    const res = await fetch('/account/api/seller-verification/', {
        method: 'POST',
        headers: { 'X-CSRFToken': getCSRFToken() },
        body: data
    });

    const errData = await res.json();

    if (!res.ok) throw new Error(errData.detail || 'Verification submission failed');
}

function showSuccessState() {
    //document.querySelector('.onboarding-container').style.display = 'none';
    const success = document.getElementById('successState');
    success.style.display = 'flex';

    console.log(success);

    setTimeout(() => {
        window.location.href = '/account/seller/dashboard/';
    }, 3500);
}


/* ===============================
   STEP CONTROLLER
================================ */
async function handleNext() {
    try {
        nextBtn.disabled = true;

        if (currentStep === 1) {
            await submitStoreInfo();
        } 
        else if (currentStep === 2) {
            await submitAddressInfo();
        } 
        else if (currentStep === 3) {
            await submitPaymentInfo();
        } 
        else if (currentStep === 4) {
            await submitVerification();
            showSuccessState();
            return;
        }

        currentStep++;
        showStep(currentStep);

    } catch (error) {
        showError(error.detail || 'Please check your input.');
    } finally {
        nextBtn.disabled = false;
    }
}


function handleBack() {
    if (currentStep > 1) {
        currentStep--;
        showStep(currentStep);
    }
}

/* ===============================
   INIT
================================ */
nextBtn.addEventListener('click', handleNext);
backBtn.addEventListener('click', handleBack);

showStep(currentStep);

const idTypeSelect = document.getElementById('idType');
const idNumberInput = document.getElementById('idNumber');
const idNumberTooltip = document.getElementById('idNumberTooltip');

idTypeSelect.addEventListener('change', () => {
    const type = idTypeSelect.value;

    if (type === 'ghana_card') {
        idNumberInput.placeholder = 'GHA-123456-6';
        idNumberInput.pattern = '^GHA-\\d{6}-\\d$';
        idNumberTooltip.textContent = 'Format: GHA-XXXXXX-X';
    } else if (type === 'student_id') {
        idNumberInput.placeholder = '1234';
        idNumberInput.pattern = '^\\d{4,10}$';
        idNumberTooltip.textContent = 'Format: Only numbers, e.g., 1234';
    } else {
        idNumberInput.placeholder = 'Enter ID Number';
        idNumberInput.pattern = '.*';
        idNumberTooltip.textContent = '';
    }

    idNumberInput.value = '';
});

// Image preview function
function setupImagePreview(inputId, previewId) {
    const input = document.getElementById(inputId);
    const preview = document.getElementById(previewId);

    input.addEventListener('change', () => {
        preview.innerHTML = ''; // clear previous
        const file = input.files[0];
        if (file) {
            if (file.size > 2 * 1024 * 1024) { // 2MB limit
                alert('File size exceeds 2MB.');
                input.value = '';
                return;
            }
            const img = document.createElement('img');
            img.src = URL.createObjectURL(file);
            preview.appendChild(img);
        }
    });
}

// Setup previews
setupImagePreview('idCardImage', 'idCardPreview');
setupImagePreview('selfieWithId', 'selfiePreview');
