// static/script.js

// --- DOM Elements (no changes) ---
const chatContainer = document.getElementById("chat-container");
const historyDiv = document.getElementById("history");
const userInput = document.getElementById("user-input");
const fileInput = document.getElementById("file-input");
const sendBtn = document.getElementById("send-btn");

// --- State Management (no changes) ---
let conversations = [];
let currentChatIndex = -1;

// --- Core Functions (no changes) ---
function appendMessage(content, sender, isHtml = true) {
    const messageWrapper = document.createElement("div");
    messageWrapper.classList.add("message", sender);
    if (isHtml) {
        messageWrapper.innerHTML = content;
    } else {
        messageWrapper.textContent = content;
    }
    chatContainer.appendChild(messageWrapper);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    return messageWrapper;
}

function showTypingIndicator() {
    const indicator = document.createElement("div");
    indicator.classList.add("message", "bot", "typing-indicator");
    indicator.innerHTML = "<span></span><span></span><span></span>";
    chatContainer.appendChild(indicator);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    return indicator;
}

// --- BUG FIX & LOGIC UPDATE in handleFileUpload ---
async function handleFileUpload() {
    const file = fileInput.files[0];
    if (!file) return;

    if (currentChatIndex === -1) {
        startNewChat();
    }

    const feedbackMsg = appendMessage(`<i>Uploading ${file.name}...</i>`, 'user');
    let finalFeedbackText = ""; // Variable to hold the final message text

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/upload', { method: 'POST', body: formData });
        const result = await response.json();
        if (!response.ok) {
            throw new Error(result.error || 'File upload failed');
        }
        
        finalFeedbackText = `✅ ${file.name} has been processed. You can now ask questions about it.`;
        feedbackMsg.innerHTML = `✅ <i><b>${file.name}</b> has been processed. You can now ask questions about it.</i>`;
        
    } catch (error) {
        finalFeedbackText = `❌ Error uploading ${file.name}: ${error.message}`;
        feedbackMsg.innerHTML = `❌ Error uploading ${file.name}: ${error.message}`;
    } finally {
        // --- THIS IS THE BUG FIX ---
        // Save the final, visible feedback message to the conversation history.
        // We give it a role of "system" to differentiate it from user/bot messages.
        conversations[currentChatIndex].messages.push({ 
            role: "system", // Using a "system" role for file status messages
            content: finalFeedbackText 
        });
        // -------------------------

        fileInput.value = "";
        updateHistory();
    }
}

// --- Send Message function (no changes) ---
async function sendMessage() {
    // ... (This function remains the same as the previous version)
    const text = userInput.value.trim();
    if (!text) return;
    sendBtn.disabled = true;
    if (currentChatIndex === -1) { startNewChat(); }
    appendMessage(text, 'user', false);
    conversations[currentChatIndex].messages.push({ role: 'user', content: text });
    userInput.value = "";
    const typingIndicator = showTypingIndicator();
    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: text }),
        });
        if (!response.ok) { throw new Error(`HTTP error! status: ${response.status}`); }
        const data = await response.json();
        chatContainer.removeChild(typingIndicator);
        appendMessage(data.reply, 'bot', false);
        conversations[currentChatIndex].messages.push({ role: "assistant", content: data.reply });
    } catch (error) {
        console.error("Error fetching bot reply:", error);
        chatContainer.removeChild(typingIndicator);
        appendMessage("Sorry, I encountered an error. Please try again.", "bot");
    } finally {
        sendBtn.disabled = false;
        updateHistory();
    }
}


// --- HISTORY & CHAT MANAGEMENT (HEAVILY UPGRADED) ---

function newChat() {
    chatContainer.innerHTML = "";
    currentChatIndex = -1;
    updateHistory(); // Deselect active item in history
}

function startNewChat() {
    const newConversation = { title: "New Chat", messages: [] };
    conversations.unshift(newConversation);
    currentChatIndex = 0;
}

function loadChat(index) {
    if (index < 0 || index >= conversations.length) return;
    currentChatIndex = index;
    const chat = conversations[index];
    chatContainer.innerHTML = "";
    chat.messages.forEach(msg => {
        // Display "system" (file upload) messages differently if desired
        if (msg.role === 'system') {
            appendMessage(`<i>${msg.content}</i>`, 'system');
        } else {
            appendMessage(msg.content, msg.role, false);
        }
    });
    updateHistory();
}

function updateHistory() {
    historyDiv.innerHTML = "";
    conversations.forEach((convo, index) => {
        if (convo.title === "New Chat" && convo.messages.length > 0) {
            const firstUserMsg = convo.messages.find(m => m.role === 'user');
            if (firstUserMsg) {
                convo.title = firstUserMsg.content.substring(0, 20) + "...";
            }
        }

        const item = document.createElement("div");
        item.classList.add("history-item");
        if (index === currentChatIndex) {
            item.classList.add("active");
        }
        
        const titleSpan = document.createElement("span");
        titleSpan.textContent = convo.title;
        titleSpan.style.flexGrow = "1"; // Allow title to take up space
        item.appendChild(titleSpan);

        // --- NEW: Add Delete Button ---
        const deleteBtn = document.createElement("button");
        deleteBtn.textContent = "×";
        deleteBtn.classList.add("delete-chat-btn");
        deleteBtn.onclick = (event) => {
            event.stopPropagation(); // Prevent loading the chat when deleting
            deleteChat(index);
        };
        item.appendChild(deleteBtn);

        // --- NEW: Add Rename Functionality ---
        item.ondblclick = () => renameChat(index);
        item.onclick = () => loadChat(index);
        
        historyDiv.appendChild(item);
    });
    saveConversations();
}

// --- NEW: Rename Chat Function ---
function renameChat(index) {
    const convo = conversations[index];
    const newTitle = prompt("Enter a new title for this chat:", convo.title);
    if (newTitle && newTitle.trim() !== "") {
        conversations[index].title = newTitle.trim();
        updateHistory();
    }
}

// --- NEW: Delete Chat Function ---
function deleteChat(index) {
    if (confirm("Are you sure you want to delete this chat?")) {
        conversations.splice(index, 1);
        // If the deleted chat was the active one, clear the view
        if (index === currentChatIndex) {
            newChat();
        } else {
            // Adjust currentChatIndex if a preceding chat was deleted
            if (index < currentChatIndex) {
                currentChatIndex--;
            }
            updateHistory();
        }
    }
}


// --- Local Storage (no changes) ---
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

// --- Event Listeners (no changes) ---
userInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
        event.preventDefault();
        sendMessage();
    }
});
document.addEventListener("DOMContentLoaded", loadConversations);