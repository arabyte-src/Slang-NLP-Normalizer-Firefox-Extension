const api = typeof browser !== "undefined" ? browser : chrome;

const toggleButton = document.getElementById("toggle");
const statusText = document.getElementById("status");

function setUI(started) {
  toggleButton.textContent = started ? "Stop" : "Start";
  toggleButton.classList.toggle("active", started);
  statusText.textContent = started ? "Listening for selections" : "Ready to start";
}

async function notifyActiveTab(started) {
  const tabs = await api.tabs.query({ active: true, currentWindow: true });
  const tabId = tabs[0] && tabs[0].id;
  if (tabId != null) {
    await api.tabs.sendMessage(tabId, { type: "set-started", started });
  }
}

async function syncState() {
  const stored = await api.storage.local.get("started");
  const started = Boolean(stored.started);
  setUI(started);
  await notifyActiveTab(started);
}

async function toggleState() {
  const stored = await api.storage.local.get("started");
  const next = !stored.started;
  await api.runtime.sendMessage({ type: "set-started", started: next });
  setUI(next);
  await notifyActiveTab(next);
}

syncState();

toggleButton.addEventListener("click", () => {
  toggleState().catch((error) => {
    statusText.textContent = "Error: " + error.message;
  });
});
