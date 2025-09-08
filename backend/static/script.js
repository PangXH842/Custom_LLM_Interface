document.getElementById("chat-form").addEventListener("submit", async (e) => {
  e.preventDefault();

  const input = document.getElementById("input");
  const chatbox = document.getElementById("chatbox");
  const text = input.value.trim();

  if (!text) return;

  chatbox.innerHTML += `<p class="msg user">You: ${text}</p>`;
  input.value = "";

  const response = await fetch("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: text }),
  });

  const data = await response.json();
  chatbox.innerHTML += `<p class="msg bot">Bot: ${data.reply}</p>`;
  chatbox.scrollTop = chatbox.scrollHeight;
});
