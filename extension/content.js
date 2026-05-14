const api = typeof browser !== "undefined" ? browser : chrome;

let started = false;
let tooltip = null;

function removeTooltip() {
  if (tooltip) {
    tooltip.remove();
    tooltip = null;
  }
}

function showTooltip(rect, text, isFound) {
  removeTooltip();

  tooltip = document.createElement("div");
  tooltip.textContent = text;
  tooltip.style.position = "fixed";
  tooltip.style.top = `${rect.bottom + 8}px`;
  tooltip.style.left = `${rect.left}px`;
  tooltip.style.maxWidth = "280px";
  tooltip.style.padding = "8px 10px";
  tooltip.style.background = isFound ? "#2d2419" : "#4b4b4b";
  tooltip.style.color = "#f6f1e7";
  tooltip.style.borderRadius = "10px";
  tooltip.style.fontFamily = "'Space Grotesk', 'Segoe UI', sans-serif";
  tooltip.style.fontSize = "12px";
  tooltip.style.boxShadow = "0 8px 20px rgba(0, 0, 0, 0.2)";
  tooltip.style.zIndex = "2147483647";

  document.body.appendChild(tooltip);
  setTimeout(removeTooltip, 4000);
}

async function handleSelection() {
  if (!started) {
    return;
  }

  const active = document.activeElement;
  if (active && (active.tagName === "INPUT" || active.tagName === "TEXTAREA")) {
    return;
  }

  const selection = window.getSelection();
  if (!selection || selection.isCollapsed) {
    return;
  }

  const text = selection.toString().trim();
  if (!text) {
    return;
  }

  const range = selection.getRangeAt(0);
  const rect = range.getBoundingClientRect();
  if (!rect || rect.width === 0 || rect.height === 0) {
    return;
  }

  const response = await api.runtime.sendMessage({ type: "normalize", text });
  showTooltip(rect, response.meaning, Boolean(response.found));
}

api.runtime.onMessage.addListener((message) => {
  if (message && message.type === "set-started") {
    started = Boolean(message.started);
    if (!started) {
      removeTooltip();
    }
  }
});

document.addEventListener("mouseup", () => {
  handleSelection().catch(() => {});
});

document.addEventListener("keyup", (event) => {
  if (event.key === "Escape") {
    removeTooltip();
  }
});
