const uploadStatus = document.getElementById("uploadStatus");
const chatBox = document.getElementById("chatBox");
const sessionInput = document.getElementById("sessionInput");
const sendBtn = document.getElementById("sendBtn");
const defaultSendButtonContent = sendBtn ? sendBtn.innerHTML : "";
const fileInput = document.getElementById("fileInput");
const uploadFileBtn = document.getElementById("uploadFileBtn");
const selectedFileName = document.getElementById("selectedFileName");
const knowledgeSourcesList = document.getElementById("knowledgeSourcesList");
const knowledgeSourcesEmpty = document.getElementById("knowledgeSourcesEmpty");
const refreshSourcesBtn = document.getElementById("refreshSourcesBtn");
const CHAT_STORAGE_KEY = "chatbot_agent_chat_history_v1";
const SESSION_STORAGE_KEY = "chatbot_agent_session_id_v1";

function setUploadStatus(message, isError = false) {
  if (!uploadStatus) return;
  uploadStatus.textContent = message;
  uploadStatus.style.color = isError ? "#b91c1c" : "#065f46";
}

function appendMessage(role, text) {
  if (!chatBox) return;
  const item = document.createElement("div");
  item.className = `msg ${role === "user" ? "user" : "bot"}`;
  item.textContent = text;
  chatBox.appendChild(item);
  chatBox.scrollTop = chatBox.scrollHeight;
  persistChatHistory();
}

function showTypingIndicator() {
  if (!chatBox) return null;
  const indicator = document.createElement("div");
  indicator.className = "msg bot typing-indicator";
  indicator.innerHTML = "<span></span><span></span><span></span>";
  chatBox.appendChild(indicator);
  chatBox.scrollTop = chatBox.scrollHeight;
  return indicator;
}

function removeTypingIndicator(indicator) {
  if (!indicator || !indicator.parentNode) return;
  indicator.parentNode.removeChild(indicator);
}

function getMessageItems() {
  if (!chatBox) return [];
  const nodes = Array.from(chatBox.querySelectorAll(".msg"));
  return nodes.map((node) => ({
    role: node.classList.contains("user") ? "user" : "assistant",
    text: node.textContent || "",
  }));
}

function persistChatHistory() {
  if (!chatBox) return;
  const messages = getMessageItems();
  localStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(messages));
}

function restoreChatHistory() {
  if (!chatBox) return;
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
    const detail = data.detail || "Yêu cầu thất bại";
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return data;
}

async function uploadSelectedFile() {
  if (!fileInput || !uploadFileBtn) return;
  if (!fileInput.files || fileInput.files.length === 0) {
    setUploadStatus("Bạn chưa chọn tệp.", true);
    return;
  }

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);
  setUploadStatus("Đang tải tệp...");
  uploadFileBtn.disabled = true;

  try {
    const response = await fetch("/ingest-file", {
      method: "POST",
      body: formData,
    });
    const data = await parseResponse(response);
    setUploadStatus(`${data.message}\nChunk: ${data.chunk_count}`);
    await refreshKnowledgeSources();
  } catch (error) {
    setUploadStatus(`Tải tệp lỗi: ${error.message}`, true);
  } finally {
    uploadFileBtn.disabled = false;
  }
}

if (uploadFileBtn && fileInput) {
  uploadFileBtn.addEventListener("click", () => {
    fileInput.click();
  });
}

if (fileInput) {
  fileInput.addEventListener("change", async () => {
    if (!fileInput.files || fileInput.files.length === 0) {
      if (selectedFileName) selectedFileName.textContent = "Chưa chọn tệp nào";
      return;
    }
    if (selectedFileName) selectedFileName.textContent = `Đã chọn: ${fileInput.files[0].name}`;
    await uploadSelectedFile();
  });
}

const ingestUrlBtn = document.getElementById("ingestUrlBtn");
if (ingestUrlBtn) ingestUrlBtn.addEventListener("click", async () => {
  const ingestUrlBtn = document.getElementById("ingestUrlBtn");
  const url = document.getElementById("urlInput").value.trim();
  if (!url) {
    setUploadStatus("Bạn chưa nhập URL.", true);
    return;
  }

  setUploadStatus("Đang nạp URL...");
  ingestUrlBtn.disabled = true;
  try {
    const response = await fetch("/ingest-url", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });
    const data = await parseResponse(response);
    setUploadStatus(`${data.message}\nChunk: ${data.chunk_count}`);
    await refreshKnowledgeSources();
  } catch (error) {
    setUploadStatus(`Nạp URL lỗi: ${error.message}`, true);
  } finally {
    ingestUrlBtn.disabled = false;
  }
});

const ingestTextBtn = document.getElementById("ingestTextBtn");
if (ingestTextBtn) ingestTextBtn.addEventListener("click", async () => {
  const ingestTextBtn = document.getElementById("ingestTextBtn");
  const source = document.getElementById("sourceInput").value.trim() || "manual_input";
  const text = document.getElementById("textInput").value.trim();
  if (!text) {
    setUploadStatus("Bạn chưa nhập văn bản.", true);
    return;
  }

  setUploadStatus("Đang nạp văn bản...");
  ingestTextBtn.disabled = true;
  try {
    const response = await fetch("/ingest-text", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ source, text }),
    });
    const data = await parseResponse(response);
    setUploadStatus(`${data.message}\nChunk: ${data.chunk_count}`);
    await refreshKnowledgeSources();
  } catch (error) {
    setUploadStatus(`Nạp văn bản lỗi: ${error.message}`, true);
  } finally {
    ingestTextBtn.disabled = false;
  }
});

function sourceTypeLabel(sourceType) {
  if (sourceType === "file") return "Tệp";
  if (sourceType === "url") return "URL";
  return "Văn bản";
}

async function deleteKnowledgeSource(source) {
  const response = await fetch(`/knowledge-sources?source=${encodeURIComponent(source)}`, {
    method: "DELETE",
  });
  return parseResponse(response);
}

async function refreshKnowledgeSources() {
  if (!knowledgeSourcesList || !knowledgeSourcesEmpty) return;
  try {
    const response = await fetch("/knowledge-sources");
    const data = await parseResponse(response);
    const items = Array.isArray(data.items) ? data.items : [];

    knowledgeSourcesList.innerHTML = "";
    if (items.length === 0) {
      knowledgeSourcesEmpty.style.display = "block";
      return;
    }

    knowledgeSourcesEmpty.style.display = "none";
    items.forEach((item) => {
      const li = document.createElement("li");
      li.className = "source-item";

      const row = document.createElement("div");
      row.className = "source-item-row";

      const title = document.createElement("div");
      title.className = "source-item-title";
      title.textContent = item.display_name;

      const deleteBtn = document.createElement("button");
      deleteBtn.className = "source-delete-btn";
      deleteBtn.textContent = "Xóa";
      deleteBtn.addEventListener("click", async () => {
        try {
          deleteBtn.disabled = true;
          const result = await deleteKnowledgeSource(item.source);
          setUploadStatus(`${result.message}\nĐã xóa ${result.removed_chunks} chunk`);
          await refreshKnowledgeSources();
        } catch (error) {
          setUploadStatus(`Xóa nguồn dữ liệu lỗi: ${error.message}`, true);
          deleteBtn.disabled = false;
        }
      });

      const meta = document.createElement("div");
      meta.className = "source-item-meta";
      meta.textContent = `${sourceTypeLabel(item.source_type)} • ${item.chunk_count} chunk`;

      row.appendChild(title);
      row.appendChild(deleteBtn);
      li.appendChild(row);
      li.appendChild(meta);
      knowledgeSourcesList.appendChild(li);
    });
  } catch (_error) {
    knowledgeSourcesList.innerHTML = "";
    knowledgeSourcesEmpty.style.display = "block";
    knowledgeSourcesEmpty.textContent = "Không tải được danh sách dữ liệu.";
  }
}

if (refreshSourcesBtn) {
  refreshSourcesBtn.addEventListener("click", refreshKnowledgeSources);
}

async function sendMessage() {
  if (!sessionInput || !sendBtn) return;
  const sessionId = sessionInput.value.trim() || "default-session";
  localStorage.setItem(SESSION_STORAGE_KEY, sessionId);
  const chatInput = document.getElementById("chatInput");
  const message = chatInput.value.trim();
  if (!message) {
    return;
  }

  appendMessage("user", message);
  chatInput.value = "";
  sendBtn.disabled = true;
  sendBtn.innerHTML = '<span class="material-symbols-outlined" style="font-variation-settings: \'FILL\' 1;">hourglass_top</span>';
  const typingIndicator = showTypingIndicator();

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
    removeTypingIndicator(typingIndicator);
    appendMessage("assistant", data.answer);
  } catch (error) {
    removeTypingIndicator(typingIndicator);
    appendMessage("assistant", `Lỗi: ${error.message}`);
  } finally {
    sendBtn.disabled = false;
    sendBtn.innerHTML = defaultSendButtonContent;
  }
}

if (sendBtn) {
  sendBtn.addEventListener("click", sendMessage);
}

const chatInput = document.getElementById("chatInput");
if (chatInput) {
  chatInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  });
}

const clearChatBtn = document.getElementById("clearChatBtn");
if (clearChatBtn && chatBox) {
  clearChatBtn.addEventListener("click", () => {
    chatBox.innerHTML = "";
    localStorage.removeItem(CHAT_STORAGE_KEY);
  });
}

const restoredSessionId = localStorage.getItem(SESSION_STORAGE_KEY);
if (restoredSessionId && sessionInput) {
  sessionInput.value = restoredSessionId;
}
restoreChatHistory();
if (uploadStatus) {
  setUploadStatus("Sẵn sàng tải dữ liệu.");
}
refreshKnowledgeSources();
