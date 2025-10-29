// script.js — versão ajustada para conversar com app.py
const API_FLASK = "http://127.0.0.1:5000";

document.addEventListener("DOMContentLoaded", () => {
  // elementos
  const initialView = document.getElementById("initial-view");
  const chatView = document.getElementById("chat-view");
  const initialInput = document.getElementById("initial-input");
  const initialSendButton = document.getElementById("initial-send-btn");

  const sendBtn = document.getElementById("send-btn");
  const userInput = document.getElementById("user-input");
  const chatBox = document.getElementById("chat-box");

  const fileInput = document.getElementById("file-upload");
  const addFileBtn = document.getElementById("add-file-btn");
  const fileOptionsMenu = document.getElementById("file-options-menu");
  const themeToggle = document.getElementById("theme-toggle");
  const themeIcon = document.querySelector(".theme-icon");

  const personality = `
Você é Beka, uma assistente profissional simpática e eficiente.
Mantenha sempre um tom cordial e respeitoso, adequado a um ambiente de trabalho.
Evite expressões afetivas como "querido", "amor", "hahaha" ou emojis.
Quando solicitado para redigir e-mails, use linguagem formal, objetiva e clara.
Em situações informais, pode ser mais leve, mas nunca excessivamente pessoal.
`;


  // session id persistente
  let sessionId = localStorage.getItem("beka_session_id");
  if (!sessionId) {
    sessionId = Date.now().toString();
    localStorage.setItem("beka_session_id", sessionId);
  }

  function toggleTheme() {
    const currentTheme = document.body.getAttribute("data-theme");
    if (currentTheme === "dark") {
      document.body.removeAttribute("data-theme");
      themeIcon.textContent = "☀️";
    } else {
      document.body.setAttribute("data-theme", "dark");
      themeIcon.textContent = "🌙";
    }
  }
  if (themeToggle) themeToggle.addEventListener("click", toggleTheme);

  addFileBtn && addFileBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    fileOptionsMenu.classList.toggle("hidden");
  });
  document.addEventListener("click", (e) => {
    if (fileOptionsMenu && !fileOptionsMenu.contains(e.target) && e.target !== addFileBtn) {
      fileOptionsMenu.classList.add("hidden");
    }
  });
  const input = document.getElementById("user-input");

input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        document.getElementById("send-btn").click();
    }
});


  document.querySelectorAll(".file-option").forEach(option => {
    option.addEventListener("click", () => {
      const type = option.getAttribute("data-type");
      fileInput.setAttribute("accept", type === "image" ? "image/*" : ".pdf");
      fileInput.click();
      fileOptionsMenu.classList.add("hidden");
    });
  });

  function escapeHtml(str) {
    if (!str) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function appendMessageHTML(author, text) {
    const messageDiv = document.createElement("div");
    messageDiv.classList.add("message", author === "Você" ? "user" : "ai");

    const bubble = document.createElement("div");
    bubble.classList.add("message-bubble");
    bubble.innerHTML = escapeHtml(text);

    messageDiv.appendChild(bubble);
    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
  }

  async function sendMessage() {
    const text = userInput.value.trim();

    if (!text && (!fileInput || fileInput.files.length === 0)) return;

    if (text) {
      appendMessageHTML("Você", text);
      userInput.value = "";
    }

    if (fileInput && fileInput.files.length) {
      const f = fileInput.files[0];
      appendMessageHTML("Você", `📎 Enviou arquivo: ${f.name}`);
      fileInput.value = "";
      // NOTE: upload de arquivo não implementado aqui — requer endpoint /upload
    }

    sendBtn.disabled = true;
    sendBtn.innerHTML = '<span class="send-icon">⏳</span>';

    try {
      const res = await fetch(`${API_FLASK}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, session_id: sessionId }),
      });

      if (!res.ok) {
        const txt = await res.text();
        appendMessageHTML("Beka", `⚠️ Erro do servidor: ${txt}`);
        return;
      }

      const data = await res.json();
      const resposta = data.reply || "⚠️ Sem resposta do servidor.";
      appendMessageHTML("Beka", resposta);

    } catch (err) {
      console.error("Erro ao enviar:", err);
      appendMessageHTML("Beka", `🚫 Erro de conexão: ${err.message}`);
    } finally {
      sendBtn.disabled = false;
      sendBtn.innerHTML = '<span class="send-icon">→</span>';
      userInput.focus();
    }
  }

  function startChatFromInitial(message) {
    if (initialView) initialView.classList.add("hidden");
    if (chatView) {
      chatView.classList.remove("hidden");
      chatView.classList.add("visible");
    }
    if (message) {
      userInput.value = message;
      sendMessage();
      initialInput.value = "";
    }
  }

  initialSendButton && initialSendButton.addEventListener("click", () => {
    const message = initialInput.value.trim();
    if (message) startChatFromInitial(message);
  });

  initialInput && initialInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") initialSendButton.click();
  });

  sendBtn && sendBtn.addEventListener("click", (e) => {
    e.preventDefault();
    sendMessage();
  });

  userInput && userInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  initialInput && initialInput.focus();
});


