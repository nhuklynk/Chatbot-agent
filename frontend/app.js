const uploadStatus = document.getElementById("uploadStatus");
const chatBox = document.getElementById("chatBox");
const sessionInput = document.getElementById("sessionInput");
const sendBtn = document.getElementById("sendBtn");
const defaultSendButtonContent = sendBtn ? sendBtn.innerHTML : "";
const fileInput = document.getElementById("fileInput");
const uploadFileBtn = document.getElementById("uploadFileBtn");
const selectedFileName = document.getElementById("selectedFileName");
const uploadLoading = document.getElementById("uploadLoading");
const uploadLoadingText = document.getElementById("uploadLoadingText");
const defaultUploadButtonText = uploadFileBtn ? uploadFileBtn.textContent : "";
const knowledgeSourcesList = document.getElementById("knowledgeSourcesList");
const knowledgeSourcesEmpty = document.getElementById("knowledgeSourcesEmpty");
const refreshSourcesBtn = document.getElementById("refreshSourcesBtn");
const CHAT_STORAGE_KEY = "chatbot_agent_chat_history_v1";
const SESSION_STORAGE_KEY = "chatbot_agent_session_id_v1";
let toastContainer = null;
let activeDialogOverlay = null;

function setUploadStatus(message, isError = false) {
  if (!uploadStatus) return;
  uploadStatus.textContent = message;
  uploadStatus.style.color = isError ? "#b91c1c" : "#065f46";
}

function getToastContainer() {
  if (toastContainer) return toastContainer;
  toastContainer = document.createElement("div");
  toastContainer.id = "toastContainer";
  toastContainer.className = "toast-container";
  document.body.appendChild(toastContainer);
  return toastContainer;
}

function showToast(message, type = "info", durationMs = 3200) {
  if (!message) return;
  const container = getToastContainer();
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  container.appendChild(toast);

  requestAnimationFrame(() => {
    toast.classList.add("show");
  });

  const dismiss = () => {
    toast.classList.remove("show");
    setTimeout(() => {
      if (toast.parentNode) toast.parentNode.removeChild(toast);
    }, 220);
  };

  const timeoutId = setTimeout(dismiss, durationMs);
  toast.addEventListener("click", () => {
    clearTimeout(timeoutId);
    dismiss();
  });
}

function askConfirm({
  title = "Xác nhận",
  message = "Bạn có chắc chắn muốn thực hiện thao tác này?",
  confirmText = "Đồng ý",
  cancelText = "Hủy",
} = {}) {
  return new Promise((resolve) => {
    if (activeDialogOverlay && activeDialogOverlay.parentNode) {
      activeDialogOverlay.parentNode.removeChild(activeDialogOverlay);
      activeDialogOverlay = null;
    }

    const overlay = document.createElement("div");
    overlay.className = "confirm-dialog-overlay";

    const dialog = document.createElement("div");
    dialog.className = "confirm-dialog";
    dialog.innerHTML = `
      <h4 class="confirm-dialog-title">${title}</h4>
      <p class="confirm-dialog-message">${message}</p>
      <div class="confirm-dialog-actions">
        <button type="button" class="confirm-dialog-btn confirm-dialog-cancel">${cancelText}</button>
        <button type="button" class="confirm-dialog-btn confirm-dialog-confirm">${confirmText}</button>
      </div>
    `;

    overlay.appendChild(dialog);
    document.body.appendChild(overlay);
    activeDialogOverlay = overlay;

    const confirmBtn = dialog.querySelector(".confirm-dialog-confirm");
    const cancelBtn = dialog.querySelector(".confirm-dialog-cancel");
    let settled = false;

    const handleKeydown = (event) => {
      if (event.key === "Escape") close(false);
    };

    const close = (result) => {
      if (!overlay.parentNode || settled) return;
      settled = true;
      document.removeEventListener("keydown", handleKeydown);
      overlay.classList.add("closing");
      setTimeout(() => {
        if (overlay.parentNode) overlay.parentNode.removeChild(overlay);
        if (activeDialogOverlay === overlay) activeDialogOverlay = null;
        resolve(result);
      }, 120);
    };

    confirmBtn.addEventListener("click", () => close(true));
    cancelBtn.addEventListener("click", () => close(false));
    overlay.addEventListener("click", (event) => {
      if (event.target === overlay) close(false);
    });
    document.addEventListener("keydown", handleKeydown);
  });
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

function setUploadLoading(isLoading, message = "Đang tải tệp...") {
  if (!uploadLoading || !uploadLoadingText || !uploadFileBtn || !fileInput) return;
  uploadLoadingText.textContent = message;
  uploadLoading.classList.toggle("hidden", !isLoading);
  uploadFileBtn.textContent = isLoading ? "Đang tải..." : defaultUploadButtonText;
  uploadFileBtn.disabled = isLoading;
  fileInput.disabled = isLoading;
}

function formatSelectedFileNames(files) {
  if (files.length === 1) {
    return `Đã chọn: ${files[0].name}`;
  }
  const preview = files.slice(0, 3).map((file) => file.name).join(", ");
  const remaining = files.length - 3;
  if (remaining > 0) {
    return `Đã chọn ${files.length} tệp: ${preview}, +${remaining} tệp khác`;
  }
  return `Đã chọn ${files.length} tệp: ${preview}`;
}

async function uploadSingleFile(file) {
  const formData = new FormData();
  formData.append("file", file, file.name);
  const response = await fetch("/ingest-file", {
    method: "POST",
    body: formData,
  });
  return parseResponse(response);
}

async function uploadSelectedFiles() {
  if (!fileInput || !uploadFileBtn) return;
  if (!fileInput.files || fileInput.files.length === 0) {
    setUploadStatus("Bạn chưa chọn tệp.", true);
    showToast("Bạn chưa chọn tệp.", "warning");
    return;
  }

  const files = Array.from(fileInput.files);
  const total = files.length;
  const results = [];
  let successCount = 0;
  setUploadLoading(true, `Đang tải ${total} tệp...`);

  try {
    for (let index = 0; index < total; index += 1) {
      const file = files[index];
      setUploadLoading(true, `Đang tải tệp ${index + 1}/${total}: ${file.name}`);
      setUploadStatus(`Đang tải tệp ${index + 1}/${total}: ${file.name}...`);
      try {
        const data = await uploadSingleFile(file);
        successCount += 1;
        results.push(`[OK] ${file.name}: ${data.chunk_count} chunk`);
      } catch (error) {
        results.push(`[LOI] ${file.name}: ${error.message}`);
      }
    }
    const failCount = total - successCount;
    const summary = [
      `Hoàn tất tải tệp: ${successCount}/${total} thành công${failCount ? `, ${failCount} lỗi` : "."}`,
      ...results,
    ].join("\n");
    setUploadStatus(summary, failCount > 0);
    if (failCount === 0) {
      showToast(`Tải thành công ${successCount} tệp.`, "success");
    } else if (successCount > 0) {
      showToast(`Đã tải ${successCount} tệp, ${failCount} tệp lỗi.`, "warning");
    } else {
      showToast("Tải tệp thất bại.", "error");
    }
    await refreshKnowledgeSources();
  } finally {
    setUploadLoading(false);
    fileInput.value = "";
    if (selectedFileName) selectedFileName.textContent = "Chưa chọn tệp nào";
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
    const files = Array.from(fileInput.files);
    if (selectedFileName) selectedFileName.textContent = formatSelectedFileNames(files);
    await uploadSelectedFiles();
  });
}

const ingestUrlBtn = document.getElementById("ingestUrlBtn");
if (ingestUrlBtn) ingestUrlBtn.addEventListener("click", async () => {
  const ingestUrlBtn = document.getElementById("ingestUrlBtn");
  const url = document.getElementById("urlInput").value.trim();
  if (!url) {
    setUploadStatus("Bạn chưa nhập URL.", true);
    showToast("Bạn chưa nhập URL.", "warning");
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
    showToast(data.message, "success");
    await refreshKnowledgeSources();
  } catch (error) {
    setUploadStatus(`Nạp URL lỗi: ${error.message}`, true);
    showToast(`Nạp URL lỗi: ${error.message}`, "error");
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
    showToast("Bạn chưa nhập văn bản.", "warning");
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
    showToast(data.message, "success");
    await refreshKnowledgeSources();
  } catch (error) {
    setUploadStatus(`Nạp văn bản lỗi: ${error.message}`, true);
    showToast(`Nạp văn bản lỗi: ${error.message}`, "error");
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

async function refreshKnowledgeSources(showSuccessToast = false) {
  if (!knowledgeSourcesList || !knowledgeSourcesEmpty) return;
  try {
    const response = await fetch("/knowledge-sources");
    const data = await parseResponse(response);
    const items = Array.isArray(data.items) ? data.items : [];

    knowledgeSourcesList.innerHTML = "";
    if (items.length === 0) {
      knowledgeSourcesEmpty.style.display = "block";
      if (showSuccessToast) {
        showToast("Đã làm mới danh sách: chưa có dữ liệu.", "info");
      }
      return;
    }

    knowledgeSourcesEmpty.style.display = "none";
    if (showSuccessToast) {
      showToast(`Đã làm mới danh sách: ${items.length} nguồn dữ liệu.`, "success");
    }
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
          const confirmed = await askConfirm({
            title: "Xác nhận xóa nguồn dữ liệu",
            message: `Bạn có chắc muốn xóa "${item.display_name}" khỏi kho tri thức?`,
            confirmText: "Xóa",
            cancelText: "Giữ lại",
          });
          if (!confirmed) {
            showToast("Đã hủy thao tác xóa.", "info");
            return;
          }

          deleteBtn.disabled = true;
          const result = await deleteKnowledgeSource(item.source);
          setUploadStatus(`${result.message}\nĐã xóa ${result.removed_chunks} chunk`);
          showToast(result.message, "success");
          await refreshKnowledgeSources();
        } catch (error) {
          setUploadStatus(`Xóa nguồn dữ liệu lỗi: ${error.message}`, true);
          showToast(`Xóa nguồn dữ liệu lỗi: ${error.message}`, "error");
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
    showToast("Không tải được danh sách dữ liệu.", "error");
  }
}

if (refreshSourcesBtn) {
  refreshSourcesBtn.addEventListener("click", () => refreshKnowledgeSources(true));
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
    showToast(`Lỗi chat: ${error.message}`, "error");
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
    showToast("Đã xóa lịch sử chat.", "info");
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
