function urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding)
        .replace(/-/g, '+')
        .replace(/_/g, '/');

    const rawData = atob(base64);
    return Uint8Array.from([...rawData].map(c => c.charCodeAt(0)));
}


function canSubscribeToPush() {
    if (!("serviceWorker" in navigator)) return false;
    if (!("PushManager" in window)) return false;

    if (Notification.permission === "denied") {
        console.warn("Push permission denied");
        return false;
    }

    return true;
}

async function getServiceWorkerRegistration() {
    return await navigator.serviceWorker.ready;
}

async function getOrCreateSubscription(registration) {
    let subscription = await registration.pushManager.getSubscription();

    if (subscription) {
        console.log("Existing subscription found");
        return subscription;
    }

    console.log("Creating new push subscription");

    return await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(
            "BCcVqQQPgD3gSBqL0Ln1sh5YlyJUdniJr64-HIQvWtTJEAdI9mTRkBJbP3D_Bc8OV8V8WlaqyXvMgN2P9vfKsPg"
        ),
    });
}

function detectDeviceName() {
    const ua = navigator.userAgent;

    if (/iphone/i.test(ua)) return "iPhone (Safari)";
    if (/ipad/i.test(ua)) return "iPad (Safari)";
    if (/android/i.test(ua)) return "Android Device";
    if (/windows/i.test(ua)) return "Windows Desktop";
    if (/macintosh/i.test(ua)) return "Mac Desktop";

    return "Unknown Device";
}

async function sendSubscriptionToServer(subscription) {
    const payload = {
        endpoint: subscription.endpoint,
        keys: subscription.toJSON().keys,
        device_name: detectDeviceName(),
    };

    const response = await fetch("/order/notifications/subscribe/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCSRFToken(),
        },
        body: JSON.stringify(payload),
    });

    if (!response.ok) {
        console.error("Failed to save push subscription");
    }
}

async function subscribeToPushNotifications() {
    if (!canSubscribeToPush()) return;

    const registration = await getServiceWorkerRegistration();
    const subscription = await getOrCreateSubscription(registration);

    console.log("Push subscription:", subscription);

    await sendSubscriptionToServer(subscription);
}

document.addEventListener("DOMContentLoaded", () => {
    subscribeToPushNotifications().catch(console.error);
});
