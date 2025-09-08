async function sendMessage() {
  const input = document.getElementById("input");
  const text = input.value.trim();
  if (!text) return;

  const chat = document.getElementById("chat");
  chat.innerHTML += `<div class="msg user">You: ${text}</div>`;
  input.value = "";

  const res = await fetch("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: text })
  });
  const data = await res.json();

  chat.innerHTML += `<div class="msg bot">Bot: ${data.reply}</div>`;
  chat.scrollTop = chat.scrollHeight;
}
