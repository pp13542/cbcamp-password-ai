const messagesElement = document.querySelector("#messages");
const form = document.querySelector("#chat-form");
const input = document.querySelector("#message-input");
const sendButton = document.querySelector("#send-button");
const resetButton = document.querySelector("#reset-button");

const greeting = "안녕하세요. 저는 비밀번호 찾기 도움 AI입니다.\n비밀번호를 직접 알려드리지는 않지만, 이전 대화나 학습 데이터 속 단서를 바탕으로 도움을 드릴 수 있습니다.";
let history = [];

function addMessage(role, content) {
  const item = document.createElement("div");
  item.className = `message ${role}`;
  item.textContent = content;
  messagesElement.appendChild(item);
  messagesElement.scrollTop = messagesElement.scrollHeight;
}

function resetChat() {
  history = [];
  messagesElement.replaceChildren();
  addMessage("assistant", greeting);
  input.focus();
}

async function sendMessage(message) {
  addMessage("user", message);
  const previousHistory = [...history];
  history.push({ role: "user", content: message });
  sendButton.disabled = true;
  input.disabled = true;
  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, history: previousHistory }),
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    addMessage("assistant", data.answer);
    history.push({ role: "assistant", content: data.answer });
  } catch (error) {
    addMessage("assistant", "응답을 가져오지 못했습니다. 잠시 후 다시 시도해 주세요.");
  } finally {
    sendButton.disabled = false;
    input.disabled = false;
    input.focus();
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const message = input.value.trim();
  if (!message) return;
  input.value = "";
  sendMessage(message);
});
input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});
resetButton.addEventListener("click", resetChat);
resetChat();

