// Configuration
const API_URL = 'http://localhost:8000'; // Cambiar a Railway URL en producción

// State
let chatOpen = false;
let isWaitingResponse = false;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    console.log('Chinfield Chat Widget initialized');
});

// Toggle chat
function toggleChat() {
    const widget = document.getElementById('chatWidget');
    const button = document.getElementById('chatButton');
    
    chatOpen = !chatOpen;
    
    if (chatOpen) {
        widget.classList.add('open');
        button.style.display = 'none';
        document.getElementById('chatInput').focus();
        
        // Remove badge
        const badge = document.querySelector('.chat-button-badge');
        if (badge) badge.style.display = 'none';
    } else {
        widget.classList.remove('open');
        button.style.display = 'flex';
    }
}

function openChat() {
    if (!chatOpen) {
        toggleChat();
    }
}

function closeChat() {
    if (chatOpen) {
        toggleChat();
    }
}

// Ask about product
function askAbout(productName) {
    openChat();
    setTimeout(() => {
        document.getElementById('chatInput').value = `¿Qué es ${productName}?`;
        sendMessage();
    }, 300);
}

// Handle enter key
function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

// Send message
async function sendMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    
    if (!message || isWaitingResponse) return;
    
    // Clear input
    input.value = '';
    
    // Add user message
    addMessage(message, 'user');
    
    // Show loading
    const loadingId = addMessage('Pensando...', 'bot', true);
    isWaitingResponse = true;
    
    try {
        // Call API
        const response = await fetch(`${API_URL}/api/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message
            })
        });
        
        if (!response.ok) {
            throw new Error('Error en la respuesta del servidor');
        }
        
        const data = await response.json();
        
        // Remove loading message
        removeMessage(loadingId);
        
        // Add bot response
        addMessage(data.response, 'bot');
        
        // Add handoff info if needed
        if (data.handoff_to_human) {
            addHandoffMessage();
        }
        
    } catch (error) {
        console.error('Error:', error);
        
        // Remove loading
        removeMessage(loadingId);
        
        // Add error message
        addMessage(
            'Lo siento, hubo un problema al procesar tu consulta. Por favor, intenta nuevamente o contacta directamente a info@chinfield.com',
            'bot'
        );
    } finally {
        isWaitingResponse = false;
    }
}

// Add message to chat
function addMessage(text, sender, isLoading = false) {
    const messagesContainer = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    const messageId = 'msg-' + Date.now();
    
    messageDiv.id = messageId;
    messageDiv.className = `message ${sender}`;
    if (isLoading) messageDiv.classList.add('loading');
    
    messageDiv.textContent = text;
    
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    return messageId;
}

// Remove message
function removeMessage(messageId) {
    const message = document.getElementById(messageId);
    if (message) {
        message.remove();
    }
}

// Add handoff message
function addHandoffMessage() {
    const messagesContainer = document.getElementById('chatMessages');
    const handoffDiv = document.createElement('div');
    
    handoffDiv.className = 'message bot';
    handoffDiv.innerHTML = `
        <strong>💬 ¿Necesitás más ayuda?</strong><br/><br/>
        Para consultas específicas contactá:<br/>
        📧 info@chinfield.com<br/>
        📞 +54 11 4762-5163<br/>
        🌐 <a href="https://chinfield.com/contacto" target="_blank" style="color: #e89a3c;">chinfield.com/contacto</a>
    `;
    
    messagesContainer.appendChild(handoffDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Smooth scroll
function scrollToSection(sectionId) {
    const element = document.getElementById(sectionId);
    if (element) {
        element.scrollIntoView({ behavior: 'smooth' });
    }
}