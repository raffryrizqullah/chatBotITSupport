// Backend Logic and Helper Functions

let userMessage = null;
let inputInitHeight;
window.addEventListener('DOMContentLoaded', () => {
    inputInitHeight = chatInput.scrollHeight;
});

const createChatLi = (message, className) => {
    const chatLi = document.createElement("li");
    chatLi.classList.add("chat", `${className}`);
    let chatContent = className === "outgoing" ? `<p></p>` : `<span class="material-symbols-outlined">smart_toy</span><p></p>`;
    chatLi.innerHTML = chatContent;
    chatLi.querySelector("p").innerHTML = formatMessage(message);
    return chatLi;
};

const createLoadingAnimation = () => {
    const loadingDiv = document.createElement("div");
    loadingDiv.classList.add("loading-spinner");
    return loadingDiv;
};

const animateChatBubble = (chatElement) => {
    chatElement.style.opacity = 0;
    chatElement.style.transform = 'scale(0.5)';
    chatElement.style.transition = 'all 0.4s ease';
    setTimeout(() => {
        chatElement.style.opacity = 1;
        chatElement.style.transform = 'scale(1)';
    }, 10);
};

const formatMessage = (message) => {
    // Replace **text** or *text* with bold HTML tags
    message = message.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    message = message.replace(/\*(.*?)\*/g, '<strong>$1</strong>');
    
    // Replace URLs with clickable links
    message = message.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" style="color: blue;">$1</a>');
    
    return message;
};

const handleChat = () => {
    // Disable input to prevent spam
    chatInput.disabled = true;
    sendChatBtn.style.pointerEvents = 'none';
    userMessage = chatInput.value.trim();
    if (!userMessage) return;
    chatInput.value = "";
    chatInput.style.height = `${inputInitHeight}px`;

    const outgoingChatLi = createChatLi(userMessage, "outgoing");
    chatbox.appendChild(outgoingChatLi);
    animateChatBubble(outgoingChatLi);
    chatbox.scrollTo(0, chatbox.scrollHeight);

    const incomingChatLi = document.createElement("li");
    incomingChatLi.classList.add("chat", "incoming");
    incomingChatLi.innerHTML = `<span class="material-symbols-outlined">smart_toy</span>`;
    const loadingAnimation = createLoadingAnimation();
incomingChatLi.appendChild(loadingAnimation);
// Keep chatbot icon visible alongside loading animation

    setTimeout(() => {
        chatbox.appendChild(incomingChatLi);
        animateChatBubble(incomingChatLi);
        chatbox.scrollTo(0, chatbox.scrollHeight);

        fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: userMessage })
        })
        .then(response => response.json())
        .then(data => {
            // Enable input after receiving response
            chatInput.disabled = false;
            sendChatBtn.style.pointerEvents = 'auto';
            chatInput.focus(); // Return focus to input textarea
            // Keep the chatbot icon after loading, only remove the spinner
if (loadingAnimation) {
    loadingAnimation.style.display = 'none';
}
            const replySteps = data.reply.split('\n');
            replySteps.forEach(step => {
                const replyP = document.createElement("p");
                replyP.innerHTML = formatMessage(step);
                incomingChatLi.appendChild(replyP);
                chatbox.scrollTo(0, chatbox.scrollHeight); // Auto-scroll when adding a new reply
            });
        })
        .catch(error => {
            // Enable input in case of error
            chatInput.disabled = false;
            sendChatBtn.style.pointerEvents = 'auto';
            incomingChatLi.removeChild(loadingAnimation);
            const errorP = document.createElement("p");
            errorP.textContent = "Error: " + error.message;
            incomingChatLi.appendChild(errorP);
        });
    }, 500);
};

// Frontend Event Listeners and Initial Setup

const chatbotToggler = document.querySelector(".chatbot-toggler");
const closeBtn = document.querySelector(".close-btn");
const chatbox = document.querySelector(".chatbox");
const chatInput = document.querySelector(".chat-input textarea");
const sendChatBtn = document.querySelector(".chat-input span");

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
closeBtn.addEventListener("click", () => document.body.classList.remove("show-chatbot"));

let initialMessageShown = false;
chatbotToggler.addEventListener("click", () => {
    document.body.classList.toggle("show-chatbot");
    setTimeout(() => {
        if (document.body.classList.contains("show-chatbot") && !initialMessageShown) {
            const initialChatLi = createChatLi("Halo Sobat UII 👋<br />Apakah ada yang bisa saya bantu?", "incoming");
            chatbox.appendChild(initialChatLi);
            animateChatBubble(initialChatLi);
            initialMessageShown = true;
        }
    }, 225);
});