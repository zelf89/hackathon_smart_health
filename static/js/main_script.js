let chatMessagesDiv = document.getElementById("chatMessages");

// Function to handle sending the chat message
function sendChat() {
  let userMessage = document.getElementById("chatInput").value;

  if (userMessage.trim() !== "") {
    addMessageToChat("user", userMessage);
    document.getElementById("chatInput").value = "";

    // Send the message to the backend
    fetch("/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        user_input: userMessage,
      }),
    })
      .then((response) => response.json())
      .then((data) => {
        // Add chatbot's response to chat
        addMessageToChat("chatbot", data.chatbot_response);
      })
      .catch((error) => console.error("Error:", error));
  }
}

// Function to handle Enter key to send message
function checkEnter(event) {
  if (event.key === "Enter") {
    sendChat();
  }
}

// Function to add messages to the chat
function addMessageToChat(sender, message) {
  let messageDiv = document.createElement("div");
  messageDiv.classList.add("chat-message");
  messageDiv.classList.add(
    sender === "user" ? "user-message" : "chatbot-message"
  );
  messageDiv.innerHTML = `<strong>${
    sender === "user" ? "You" : "Chatbot"
  }:</strong> ${message}`;
  chatMessagesDiv.appendChild(messageDiv);

  // Scroll to the bottom of the chat
  chatMessagesDiv.scrollTop = chatMessagesDiv.scrollHeight;
}
