const uploadStatus = document.getElementById("uploadStatus");
const chatBox = document.getElementById("chatBox");
const sessionInput = document.getElementById("sessionInput");
const CHAT_STORAGE_KEY = "chatbot_agent_chat_history_v1";
const SESSION_STORAGE_KEY = "chatbot_agent_session_id_v1";

function setUploadStatus(message, isError = false) {
  uploadStatus.textContent = message;
  uploadStatus.style.color = isError ? "#b91c1c" : "#065f46";
}

function appendMessage(role, text) {
  const item = document.createElement("div");
  item.className = `msg ${role === "user" ? "user" : "bot"}`;
  item.textContent = text;
  chatBox.appendChild(item);
  chatBox.scrollTop = chatBox.scrollHeight;
  persistChatHistory();
}

function getMessageItems() {
  const nodes = Array.from(chatBox.querySelectorAll(".msg"));
  return nodes.map((node) => ({
    role: node.classList.contains("user") ? "user" : "assistant",
    text: node.textContent || "",
  }));
}

function persistChatHistory() {
  const messages = getMessageItems();
  localStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(messages));
}

function restoreChatHistory() {
  const raw = localStorage.getItem(CHAT_STORAGE_KEY);
  if (!raw) {
    return;
  }
  try {
    const messages = JSON.parse(raw);
    if (!Array.isArray(messages)) {
      return;
    }
    messages.forEach((msg) => {
      if (!msg || typeof msg.text !== "string") {
        return;
      }
      const role = msg.role === "user" ? "user" : "assistant";
      const item = document.createElement("div");
      item.className = `msg ${role === "user" ? "user" : "bot"}`;
      item.textContent = msg.text;
      chatBox.appendChild(item);
    });
    chatBox.scrollTop = chatBox.scrollHeight;
  } catch (_error) {
    localStorage.removeItem(CHAT_STORAGE_KEY);
  }
}

async function parseResponse(response) {
  const data = await response.json();
  if (!response.ok) {
    const detail = data.detail || "Request failed";
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return data;
}

document.getElementById("uploadFileBtn").addEventListener("click", async () => {
  const fileInput = document.getElementById("fileInput");
  if (!fileInput.files || fileInput.files.length === 0) {
    setUploadStatus("Ban chua chon file.", true);
    return;
  }

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);
  setUploadStatus("Dang upload file...");

  try {
    const response = await fetch("/ingest-file", {
      method: "POST",
      body: formData,
    });
    const data = await parseResponse(response);
    setUploadStatus(`${data.message}\nChunk: ${data.chunk_count}`);
  } catch (error) {
    setUploadStatus(`Upload loi: ${error.message}`, true);
  }
});

document.getElementById("ingestUrlBtn").addEventListener("click", async () => {
  const url = document.getElementById("urlInput").value.trim();
  if (!url) {
    setUploadStatus("Ban chua nhap URL.", true);
    return;
  }

  setUploadStatus("Dang ingest URL...");
  try {
    const response = await fetch("/ingest-url", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });
    const data = await parseResponse(response);
    setUploadStatus(`${data.message}\nChunk: ${data.chunk_count}`);
  } catch (error) {
    setUploadStatus(`Ingest URL loi: ${error.message}`, true);
  }
});

document.getElementById("ingestTextBtn").addEventListener("click", async () => {
  const source = document.getElementById("sourceInput").value.trim() || "manual_input";
  const text = document.getElementById("textInput").value.trim();
  if (!text) {
    setUploadStatus("Ban chua nhap text.", true);
    return;
  }

  setUploadStatus("Dang ingest text...");
  try {
    const response = await fetch("/ingest-text", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ source, text }),
    });
    const data = await parseResponse(response);
    setUploadStatus(`${data.message}\nChunk: ${data.chunk_count}`);
  } catch (error) {
    setUploadStatus(`Ingest text loi: ${error.message}`, true);
  }
});

document.getElementById("sendBtn").addEventListener("click", async () => {
  const sessionId = sessionInput.value.trim() || "default-session";
  localStorage.setItem(SESSION_STORAGE_KEY, sessionId);
  const chatInput = document.getElementById("chatInput");
  const message = chatInput.value.trim();
  if (!message) {
    return;
  }

  appendMessage("user", message);
  chatInput.value = "";

  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: sessionId,
        message,
      }),
    });
    const data = await parseResponse(response);
    appendMessage("assistant", `${data.answer}\n\n[source: ${data.source}]`);
  } catch (error) {
    appendMessage("assistant", `Loi: ${error.message}`);
  }
});

const restoredSessionId = localStorage.getItem(SESSION_STORAGE_KEY);
if (restoredSessionId) {
  sessionInput.value = restoredSessionId;
}
restoreChatHistory();
