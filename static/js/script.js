// DOM Elements
const chatbotToggler = document.querySelector('.chatbot-toggler');
const closeBtn = document.querySelector('.close-btn');
const chatbox = document.querySelector('.chatbox');
const chatInput = document.querySelector('.chat-input textarea');
const sendChatBtn = document.querySelector('.chat-input span');

// Variables
let userMessage = null;
let inputInitHeight;
let initialMessageShown = false;

// Initialize after DOM content is loaded
window.addEventListener('DOMContentLoaded', () => {
    // Simpan tinggi awal dari input chat
    inputInitHeight = chatInput.scrollHeight;
    // Tampilkan gelembung notifikasi chatbot
    showChatbotTogglerBubble();
});

// Helper Functions

/**
 * Membuat elemen list chat dengan pesan dan kelas tertentu.
 * @param {string} message - Pesan yang akan ditampilkan.
 * @param {string} className - Kelas CSS untuk styling ('outgoing' atau 'incoming').
 * @returns {HTMLLIElement} Elemen list chat yang dibuat.
 */
function createChatLi(message, className) {
    const chatLi = document.createElement('li');
    chatLi.classList.add('chat', className);
    const chatContent = className === 'outgoing'
        ? '<p></p>'
        : '<span class="material-symbols-outlined">smart_toy</span><p></p>';
    chatLi.innerHTML = chatContent;
    chatLi.querySelector('p').innerHTML = formatMessage(message);
    return chatLi;
}

/**
 * Membuat elemen animasi loading.
 * @returns {HTMLDivElement} Elemen div animasi loading.
 */
function createLoadingAnimation() {
    const loadingDiv = document.createElement('div');
    loadingDiv.classList.add('loading-spinner');
    return loadingDiv;
}

/**
 * Menganimasikan munculnya gelembung chat.
 * @param {HTMLElement} chatElement - Elemen chat yang akan dianimasikan.
 */
function animateChatBubble(chatElement) {
    chatElement.style.opacity = 0;
    chatElement.style.transform = 'scale(0.5)';
    chatElement.style.transition = 'all 0.4s ease';
    requestAnimationFrame(() => {
        chatElement.style.opacity = 1;
        chatElement.style.transform = 'scale(1)';
    });
}

/**
 * Memformat pesan untuk mendukung teks tebal dan tautan.
 * @param {string} message - Pesan yang akan diformat.
 * @returns {string} Pesan yang telah diformat dalam bentuk HTML.
 */
function formatMessage(message) {
    // Mengganti **teks** atau *teks* dengan tag HTML bold
    message = message.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    message = message.replace(/\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Mengganti URL menjadi tautan yang dapat diklik
    message = message.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" style="color: blue;">$1</a>');
    
    return message;
}

/**
 * Menghandle pengiriman pesan chat.
 */
function handleChat() {
    // Cek apakah input kosong
    if (!chatInput.value.trim()) return;
    
    userMessage = chatInput.value.trim();
    // Nonaktifkan input untuk mencegah spam
    chatInput.disabled = true;
    sendChatBtn.style.pointerEvents = 'none';
    chatInput.value = '';
    chatInput.style.height = `${inputInitHeight}px`;

    // Tampilkan pesan keluar
    const outgoingChatLi = createChatLi(userMessage, 'outgoing');
    chatbox.appendChild(outgoingChatLi);
    animateChatBubble(outgoingChatLi);
    chatbox.scrollTo(0, chatbox.scrollHeight);

    // Tampilkan animasi loading untuk pesan masuk
    const incomingChatLi = document.createElement('li');
    incomingChatLi.classList.add('chat', 'incoming');
    incomingChatLi.innerHTML = '<span class="material-symbols-outlined">smart_toy</span>';
    const loadingAnimation = createLoadingAnimation();
    incomingChatLi.appendChild(loadingAnimation);
    chatbox.appendChild(incomingChatLi);
    animateChatBubble(incomingChatLi);
    chatbox.scrollTo(0, chatbox.scrollHeight);

    // Kirim pesan ke backend
    fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage })
    })
    .then(response => response.json())
    .then(data => {
        // Aktifkan kembali input setelah menerima respon
        chatInput.disabled = false;
        sendChatBtn.style.pointerEvents = 'auto';
        chatInput.focus();

        // Hapus animasi loading dan tampilkan respon
        loadingAnimation.remove();
        const replySteps = data.reply.split('\n');
        const fragment = document.createDocumentFragment();
        replySteps.forEach(step => {
            const replyP = document.createElement('p');
            replyP.innerHTML = formatMessage(step);
            fragment.appendChild(replyP);
        });
        incomingChatLi.appendChild(fragment);
        chatbox.scrollTo(0, chatbox.scrollHeight);
    })
    .catch(error => {
        // Aktifkan kembali input jika terjadi error
        chatInput.disabled = false;
        sendChatBtn.style.pointerEvents = 'auto';
        loadingAnimation.remove();

        // Tampilkan pesan error
        const errorP = document.createElement('p');
        errorP.textContent = 'Error: ' + error.message;
        incomingChatLi.appendChild(errorP);
    });
}

/**
 * Menampilkan gelembung pesan sementara pada tombol toggler chatbot.
 */
function showChatbotTogglerBubble() {
    const bubble = document.createElement('div');
    bubble.classList.add('chatbot-bubble');
    bubble.innerHTML = '<div class="bubble-message"><div class="message-content">online!</div></div>';
    chatbotToggler.appendChild(bubble);
    bubble.style.opacity = 0;
    bubble.style.transition = 'opacity 0.5s ease';

    // Animasi fade in
    requestAnimationFrame(() => {
        bubble.style.opacity = 1;
    });

    // Animasi fade out dan hapus elemen setelah 3 detik
    setTimeout(() => {
        bubble.style.opacity = 0;
        bubble.addEventListener('transitionend', () => {
            if (bubble.parentElement) {
                bubble.parentElement.removeChild(bubble);
            }
        });
    }, 1500);
}

// Event Listeners

// Sesuaikan tinggi textarea input berdasarkan konten
chatInput.addEventListener('input', () => {
    chatInput.style.height = `${inputInitHeight}px`;
    chatInput.style.height = `${chatInput.scrollHeight}px`;
});

// Kirim pesan saat tombol Enter ditekan tanpa Shift
chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleChat();
    }
});

// Kirim pesan saat tombol kirim diklik
sendChatBtn.addEventListener('click', handleChat);

// Tutup antarmuka chatbot
closeBtn.addEventListener('click', () => {
    document.body.classList.remove('show-chatbot');
});

// Toggle visibilitas antarmuka chatbot dan tampilkan pesan awal
chatbotToggler.addEventListener('click', () => {
    document.body.classList.toggle('show-chatbot');
    if (document.body.classList.contains('show-chatbot') && !initialMessageShown) {
        const initialMessage = 'Halo Sobat UII 👋<br />Apakah ada yang bisa saya bantu?';
        const initialChatLi = createChatLi(initialMessage, 'incoming');
        chatbox.appendChild(initialChatLi);
        animateChatBubble(initialChatLi);
        initialMessageShown = true;
    }
});
