const messagesElement = document.querySelector("#messages");
const form = document.querySelector("#chat-form");
const input = document.querySelector("#message-input");
const sendButton = document.querySelector("#send-button");
const resetButton = document.querySelector("#reset-button");

const initialMessage = `안녕하세요. 저는 비밀번호를 복구하는데 도움을 드리는 AI 챗봇입니다.

다음과 같은 절차에 따라 현재 웹사이트의 비밀번호 복구 및 재설정을 도와드리겠습니다.

1. 가입되어 있는 유저인지 확인하기 위한 이메일 확인
2. 가입되어 있는 이메일이라면 임시 비밀번호 발급
3. 이후 새 비밀번호로 재설정할지 확인
4. 재설정을 한다면 새로 사용할 비밀번호 입력

문제 설명에 제공된 테스트용 가입 이메일을 입력하면 복구 절차를 시작할 수 있습니다.`;
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
  addMessage("assistant", initialMessage);
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
