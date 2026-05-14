const api = typeof browser !== "undefined" ? browser : chrome;

const MODEL_ENDPOINT = "http://localhost:5000/normalize";

api.runtime.onMessage.addListener((message) => {
  if (message && message.type === "set-started") {
    return api.storage.local.set({ started: Boolean(message.started) }).then(() => ({ ok: true }));
  }

  if (message && message.type === "normalize") {
    const payload = {
      text: message.text || "",
      language: message.language || "auto",
    };
    return fetch(MODEL_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
      .then((response) => response.json())
      .then((data) => ({ meaning: data.meaning || payload.text, found: true }))
      .catch(() => ({ meaning: payload.text, found: false }));
  }

  return false;
});
