const chatbotToggler = document.querySelector(".chatbot-toggler");
const closeBtn = document.querySelector(".close-btn");
const chatbox = document.querySelector(".chatbox");
const chatInput = document.querySelector(".chat-input textarea");
const sendChatBtn = document.querySelector(".chat-input span");

let userMessage = null; // Cache for the user's current message.
const inputInitHeight = chatInput.scrollHeight; // Cache initial input area height.

// Function to generate chat list items.
const createChatLi = (message, className) => {
  const chatLi = document.createElement("li");
  chatLi.classList.add("chat", `${className}`);
  let chatContent =
    className === "outgoing"
      ? `<p></p>` // Outgoing messages do not have an icon.
      : `<span class="material-symbols-outlined">smart_toy</span><p></p>`; // Incoming messages have an icon.
  chatLi.innerHTML = chatContent;
  chatLi.querySelector("p").textContent = message;
  return chatLi;
};

// Function to handle API responses and update UI accordingly.
const generateResponse = async (chatElement) => {
  const messageElement = chatElement.querySelector("p");
  const requestOptions = {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: `msg=${encodeURIComponent(userMessage)}`,
  };

  try {
    const response = await fetch("/get", requestOptions);
    const data = await response.text();
    if (!response.ok) throw new Error(data);

    messageElement.textContent = data; // Display API response text.
  } catch (error) {
    messageElement.classList.add("error");
    messageElement.textContent = error.message; // Show error message if any.
  } finally {
    chatbox.scrollTo(0, chatbox.scrollHeight); // Auto-scroll to latest message.
  }
};

const handleChat = () => {
  userMessage = chatInput.value.trim();
  if (!userMessage) return; // Ignore empty messages.

  chatInput.value = "";
  chatInput.style.height = `${inputInitHeight}px`; // Reset input height.

  chatbox.appendChild(createChatLi(userMessage, "outgoing"));
  chatbox.scrollTo(0, chatbox.scrollHeight);

  setTimeout(() => {
    const incomingChatLi = createChatLi(". . .", "incoming");
    chatbox.appendChild(incomingChatLi);
    generateResponse(incomingChatLi);
  }, 600);
};

// Attach event listeners for UI interactions.
chatInput.addEventListener("input", () => {
  chatInput.style.height = `${inputInitHeight}px`;
  chatInput.style.height = `${chatInput.scrollHeight}px`;
});

chatInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey && window.innerWidth > 800) {
    e.preventDefault();
    handleChat();
  }
});

sendChatBtn.addEventListener("click", handleChat);
closeBtn.addEventListener("click", () =>
  document.body.classList.remove("show-chatbot")
);
chatbotToggler.addEventListener("click", function () {
  document.body.classList.toggle("show-chatbot");
  const textElement = document.querySelector(".animated-text");
  textElement.classList.remove("animate-in"); // Reset animation.
  setTimeout(() => {
    textElement.classList.add("animate-in"); // Restart animation for effect.
  }, 10); // Short delay ensures class is reset.
});
