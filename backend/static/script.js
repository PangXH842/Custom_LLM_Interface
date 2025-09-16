// --- DOM Elements ---
const chatContainer = document.getElementById("chat-container");
const historyDiv = document.getElementById("history");
const userInput = document.getElementById("user-input");
const fileInput = document.getElementById("file-input");

// --- State Management ---
let conversations = [];
let currentChatIndex = -1; // Use an index to track the active chat

// --- Core Functions ---

/**
 * Appends a message to the chat container.
 * @param {string} content - The HTML content of the message.
 * @param {string} sender - The sender ('user' or 'bot').
 */
function appendMessage(content, sender) {
  const messageWrapper = document.createElement("div");
  messageWrapper.classList.add("message", sender);
  // Use innerHTML to allow for simple formatting like the file link
  messageWrapper.innerHTML = content;
  chatContainer.appendChild(messageWrapper);
  chatContainer.scrollTop = chatContainer.scrollHeight;
}

/**
 * Appends a "Bot is typing..." indicator.
 * @returns {HTMLElement} The indicator element to be removed later.
 */
function showTypingIndicator() {
  const indicator = document.createElement("div");
  indicator.classList.add("message", "bot", "typing-indicator");
  indicator.innerHTML = "<span></span><span></span><span></span>";
  chatContainer.appendChild(indicator);
  chatContainer.scrollTop = chatContainer.scrollHeight;
  return indicator;
}

/**
 * Handles sending a message, including text and files.
 */
async function sendMessage() {
  const text = userInput.value.trim();
  const file = fileInput.files[0];

  if (!text && !file) return;

  // Create a new chat if this is the first message
  if (currentChatIndex === -1) {
    startNewChat();
  }
  
  let userMessageContent = "";
  if (text) {
      userMessageContent += text;
  }
  
  // For this example, we just send the file name. 
  // A full implementation would involve uploading the file first.
  if (file) {
      const fileNameText = `📎 File attached: <i>${file.name}</i>`;
      userMessageContent += (userMessageContent ? `<br>${fileNameText}` : fileNameText);
  }
  
  appendMessage(userMessageContent, "user");
  conversations[currentChatIndex].messages.push({ role: "user", content: userMessageContent });
  
  // Clear inputs
  userInput.value = "";
  fileInput.value = "";

  // Show typing indicator and fetch response
  const typingIndicator = showTypingIndicator();

  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }), // Sending only text to the backend for now
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    const botReply = data.reply;

    // Remove typing indicator and append the real reply
    chatContainer.removeChild(typingIndicator);
    appendMessage(botReply, "bot");
    conversations[currentChatIndex].messages.push({ role: "assistant", content: botReply });

  } catch (error) {
    console.error("Error fetching bot reply:", error);
    chatContainer.removeChild(typingIndicator);
    appendMessage("Sorry, I encountered an error. Please try again.", "bot");
  } finally {
      updateHistory();
  }
}

// --- History and Chat Management ---

/**
 * Starts a new, empty chat session.
 */
function newChat() {
  chatContainer.innerHTML = "";
  currentChatIndex = -1; // Indicate that we are in a "pre-chat" state
}

/**
 * Creates a new chat array when the first message is sent.
 */
function startNewChat() {
  const newConversation = {
    title: "New Chat",
    messages: [],
  };
  conversations.unshift(newConversation); // Add to the beginning
  currentChatIndex = 0; // The new chat is now active at the first index
}

/**
 * Loads a specific chat session into the main view.
 * @param {number} index - The index of the conversation to load.
 */
function loadChat(index) {
  if (index < 0 || index >= conversations.length) return;
  
  currentChatIndex = index;
  const chat = conversations[index];
  chatContainer.innerHTML = "";
  chat.messages.forEach(msg => appendMessage(msg.content, msg.role));
  updateHistory(); // To highlight the active chat
}

/**
 * Renders the chat history in the sidebar.
 */
function updateHistory() {
  historyDiv.innerHTML = "";
  conversations.forEach((convo, index) => {
    // Set title from the first user message if it's still "New Chat"
    if (convo.title === "New Chat" && convo.messages.length > 0) {
      const firstUserMsg = convo.messages.find(m => m.role === 'user');
      if (firstUserMsg) {
          // A simple way to clean up content for a title
          const tempDiv = document.createElement('div');
          tempDiv.innerHTML = firstUserMsg.content;
          convo.title = tempDiv.textContent.substring(0, 30) + "...";
      }
    }

    const item = document.createElement("div");
    item.classList.add("history-item");
    if (index === currentChatIndex) {
        item.classList.add("active");
    }
    item.textContent = convo.title;
    item.onclick = () => loadChat(index);
    historyDiv.appendChild(item);
  });
  saveConversations();
}

// --- Local Storage ---

function saveConversations() {
  localStorage.setItem("chatConversations", JSON.stringify(conversations));
}

function loadConversations() {
  const saved = localStorage.getItem("chatConversations");
  if (saved) {
    conversations = JSON.parse(saved);
    updateHistory();
  }
}

// --- Event Listeners ---

// Handle 'Enter' key press in the input field
userInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    event.preventDefault(); // Prevent new line in input
    sendMessage();
  }
});

// Load chats from local storage when the page loads
document.addEventListener("DOMContentLoaded", loadConversations);
