let deferredInstallPrompt = null;
let serviceWorkerRegistration = null;
let orderStatusPoller = null;

function setInstallButtonVisible(visible) {
  const button = document.getElementById('installAppButton');
  if (!button) return;
  button.hidden = !visible;
}

if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/service-worker.js')
      .then(registration => {
        serviceWorkerRegistration = registration;
      })
      .catch(() => {});
  });
}

window.addEventListener('beforeinstallprompt', event => {
  event.preventDefault();
  deferredInstallPrompt = event;
  setInstallButtonVisible(true);
});

window.addEventListener('appinstalled', () => {
  deferredInstallPrompt = null;
  setInstallButtonVisible(false);
});

document.addEventListener('DOMContentLoaded', () => {
  const button = document.getElementById('installAppButton');
  if (button) {
    button.addEventListener('click', async () => {
      if (!deferredInstallPrompt) return;
      deferredInstallPrompt.prompt();
      await deferredInstallPrompt.userChoice;
      deferredInstallPrompt = null;
      setInstallButtonVisible(false);
    });
  }

  const notificationButton = document.getElementById('enableNotificationsButton');
  if (notificationButton && 'Notification' in window) {
    notificationButton.hidden = Notification.permission === 'granted';
    notificationButton.addEventListener('click', async () => {
      const permission = await Notification.requestPermission();
      notificationButton.hidden = permission === 'granted';
      if (permission === 'granted') {
        startOrderStatusPolling(true);
      }
    });
  }

  startOrderStatusPolling(false);
});

function canNotify() {
  return 'Notification' in window && Notification.permission === 'granted';
}

async function notifyOrderStatus(order) {
  if (!canNotify()) return;
  const title = `Order #${order.id} updated`;
  const options = {
    body: `Status: ${order.status}`,
    icon: '/static/images/marks-food-corner-logo.png',
    badge: '/static/images/marks-food-corner-logo.png',
    tag: `order-${order.id}`,
    data: { url: `/track/${order.id}/` }
  };

  if (serviceWorkerRegistration && serviceWorkerRegistration.showNotification) {
    await serviceWorkerRegistration.showNotification(title, options);
    return;
  }

  const notification = new Notification(title, options);
  notification.onclick = () => {
    window.focus();
    window.location.href = options.data.url;
  };
}

async function loadOrderStatusFeed(showInitialNotice) {
  let response;
  try {
    response = await fetch('/orders/status-feed/', {
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
      credentials: 'same-origin'
    });
  } catch (error) {
    return;
  }

  if (!response.ok || !response.headers.get('content-type')?.includes('application/json')) return;

  const data = await response.json();
  const previous = JSON.parse(localStorage.getItem('orderStatusSnapshot') || '{}');
  const next = {};

  for (const order of data.orders || []) {
    next[order.id] = order.status;
    if (previous[order.id] && previous[order.id] !== order.status) {
      notifyOrderStatus(order);
    }
  }

  localStorage.setItem('orderStatusSnapshot', JSON.stringify(next));

  if (showInitialNotice && (data.orders || []).length) {
    const latest = data.orders[0];
    notifyOrderStatus({ id: latest.id, status: `Notifications enabled. Current status: ${latest.status}` });
  }
}

function startOrderStatusPolling(showInitialNotice) {
  if (orderStatusPoller) return;
  loadOrderStatusFeed(showInitialNotice);
  orderStatusPoller = window.setInterval(() => loadOrderStatusFeed(false), 15000);
}
