const chatbotToggler = document.querySelector(".chatbot-toggler");
const closeBtn = document.querySelector(".close-btn");
const chatbox = document.querySelector(".chatbox");
const chatInput = document.querySelector(".chat-input textarea");
const sendChatBtn = document.querySelector(".chat-input span");

let userMessage = null; // Stores user's message
const inputInitHeight = chatInput.scrollHeight; // Initial height of the chat input area

// Function to create chat <li> elements
const createChatLi = (message, className) => {
  const chatLi = document.createElement("li");
  chatLi.classList.add("chat", `${className}`);
  let chatContent =
    className === "outgoing"
      ? `<p></p>` // No icon for outgoing messages
      : `<span class="material-symbols-outlined">smart_toy</span><p></p>`; // Icon for incoming messages
  chatLi.innerHTML = chatContent;
  chatLi.querySelector("p").textContent = message;
  return chatLi;
};

// Function to handle API response and update UI
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

    messageElement.textContent = data; // Set API response text in chat
  } catch (error) {
    messageElement.classList.add("error");
    messageElement.textContent = error.message; // Display error message
  } finally {
    chatbox.scrollTo(0, chatbox.scrollHeight); // Ensure chatbox scrolls to latest message
  }
};

const createThinkingDots = () => {
  const chatLi = document.createElement("li");
  chatLi.classList.add("chat", "incoming");
  const dotsContainer = document.createElement("div");
  dotsContainer.classList.add("thinking-dots");
  for (let i = 0; i < 5; i++) {
    const dot = document.createElement("span");
    dotsContainer.appendChild(dot);
  }
  chatLi.appendChild(dotsContainer);
  return chatLi;
};

const handleChat = () => {
  userMessage = chatInput.value.trim();
  if (!userMessage) return; // Do nothing if message is empty

  chatInput.value = "";
  chatInput.style.height = `${inputInitHeight}px`;

  chatbox.appendChild(createChatLi(userMessage, "outgoing"));
  chatbox.scrollTo(0, chatbox.scrollHeight);

  setTimeout(() => {
    const incomingChatLi = createChatLi("mencari dokumen...", "incoming");
    chatbox.appendChild(incomingChatLi);
    generateResponse(incomingChatLi);
  }, 600);
};

// Event listeners for dynamic UI interactions
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
  textElement.classList.remove("animate-in"); // Reset animasi
  setTimeout(() => {
    textElement.classList.add("animate-in"); // Tambahkan kembali untuk memicu animasi
  }, 10); // Timeout kecil untuk memastikan kelas di-reset
});
