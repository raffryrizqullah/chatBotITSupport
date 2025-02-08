// Elemen HTML
const chatbotToggleButton = document.querySelector(".chatbot-toggle-button");
const chatbotCloseButton = document.querySelector(".chatbot-close-button");
const chatMessagesContainer = document.querySelector(".chat-messages");
const chatInputField = document.querySelector(".chat-input-area textarea");
const sendMessageButton = document.querySelector(".chat-input-area span");

// Variabel untuk menyimpan pesan pengguna dan tinggi awal input
let currentUserMessage = null;
const initialChatInputHeight = chatInputField.scrollHeight;

// Fungsi untuk membuat elemen list (li) untuk pesan chat
const createChatListItem = (messageText, messageType) => {
  const chatListItem = document.createElement("li");
  chatListItem.classList.add("chat", messageType);
  const chatContent =
    messageType === "outgoing"
      ? `<p></p>`
      : `<span class="material-symbols-outlined">smart_toy</span><p></p>`;
  chatListItem.innerHTML = chatContent;
  chatListItem.querySelector("p").textContent = messageText;
  return chatListItem;
};

// Fungsi untuk mendapatkan respons dari server dan memperbarui pesan chat
const generateResponse = async (chatListItem) => {
  const messageParagraph = chatListItem.querySelector("p");
  const requestOptions = {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: `msg=${encodeURIComponent(currentUserMessage)}`,
  };

  try {
    const response = await fetch("/get", requestOptions);
    const responseText = await response.text();
    if (!response.ok) throw new Error(responseText);
    messageParagraph.textContent = responseText;
  } catch (error) {
    messageParagraph.classList.add("error");
    messageParagraph.textContent = error.message;
  } finally {
    chatMessagesContainer.scrollTo(0, chatMessagesContainer.scrollHeight);
  }
};

// Fungsi utama untuk memproses pesan chat pengguna
const handleChat = () => {
  currentUserMessage = chatInputField.value.trim();
  if (!currentUserMessage) return;

  // Bersihkan input dan kembalikan ke tinggi awal
  chatInputField.value = "";
  chatInputField.style.height = `${initialChatInputHeight}px`;

  // Tambahkan pesan keluar (outgoing) ke container chat
  chatMessagesContainer.appendChild(
    createChatListItem(currentUserMessage, "outgoing")
  );
  chatMessagesContainer.scrollTo(0, chatMessagesContainer.scrollHeight);

  // Setelah jeda, tambahkan pesan masuk (incoming) dengan placeholder dan dapatkan respons
  setTimeout(() => {
    const incomingChatListItem = createChatListItem(". . .", "incoming");
    chatMessagesContainer.appendChild(incomingChatListItem);
    generateResponse(incomingChatListItem);
  }, 600);
};

// Atur perubahan tinggi input sesuai isian teks
chatInputField.addEventListener("input", () => {
  chatInputField.style.height = `${initialChatInputHeight}px`;
  chatInputField.style.height = `${chatInputField.scrollHeight}px`;
});

// Tangani pengiriman pesan dengan menekan tombol Enter (kecuali jika shift ditekan)
chatInputField.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey && window.innerWidth > 800) {
    event.preventDefault();
    handleChat();
  }
});

// Atur event listener untuk tombol kirim dan tombol tutup chatbot
sendMessageButton.addEventListener("click", handleChat);
chatbotCloseButton.addEventListener("click", () =>
  document.body.classList.remove("show-chatbot")
);
chatbotToggleButton.addEventListener("click", () => {
  document.body.classList.toggle("show-chatbot");
});
