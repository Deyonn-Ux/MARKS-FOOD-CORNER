let deferredInstallPrompt = null;

function setInstallButtonVisible(visible) {
  const button = document.getElementById('installAppButton');
  if (!button) return;
  button.hidden = !visible;
}

if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/service-worker.js').catch(() => {});
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
  if (!button) return;

  button.addEventListener('click', async () => {
    if (!deferredInstallPrompt) return;
    deferredInstallPrompt.prompt();
    await deferredInstallPrompt.userChoice;
    deferredInstallPrompt = null;
    setInstallButtonVisible(false);
  });
});
