/**
 * Chinfield Chat Widget - Mobile First Responsive
 * Professional implementation with viewport detection
 */

// =========================================================
// CONFIGURATION
// ============================================================

const CONFIG = {
    API_URL: process.env.NODE_ENV === 'production' 
        ? 'https://web-production-d0c48.up.railway.app'  // Railway URL en producción
        : 'http://localhost:8000',      // Local development
    
    MOBILE_BREAKPOINT: 768,
    ANIMATION_DURATION: 400,
    DEBOUNCE_DELAY: 150
};

// ============================================================
// STATE MANAGEMENT
// ============================================================

const STATE = {
    chatOpen: false,
    isWaitingResponse: false,
    isMobileView: window.innerWidth < CONFIG.MOBILE_BREAKPOINT,
    sessionId: generateSessionId(),
    messageCount: 0
};

// ============================================================
// INITIALIZATION
// ============================================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Chinfield Chat Widget v2.0 initialized');
    
    // Verificar elementos del DOM
    if (!verifyDOMElements()) {
        console.error('❌ Error: Widget elements not found');
        return;
    }
    
    // Setup listeners
    setupEventListeners();
    
    // Detectar cambios de viewport
    setupResponsiveListeners();
    
    // Desplazar scroll al abrir
    addWelcomeMessage();
    
    console.log(`✅ Widget ready (Mobile: ${STATE.isMobileView})`);
});

// ============================================================
// DOM VERIFICATION
// ============================================================

function verifyDOMElements() {
    const requiredElements = [
        'chatWidget',
        'chatButton',
        'chatMessages',
        'chatInput',
        'chatClose'
    ];
    
    return requiredElements.every(id => {
        const element = document.getElementById(id);
        if (!element) {
            console.warn(`⚠️ Element not found: #${id}`);
            return false;
        }
        return true;
    });
}

// ============================================================
// EVENT LISTENERS - SETUP
// ============================================================

function setupEventListeners() {
    const chatButton = document.getElementById('chatButton');
    const chatClose = document.getElementById('chatClose');
    const chatInput = document.getElementById('chatInput');
    const chatSend = document.getElementById('chatSend');
    
    // Toggle chat on button click
    chatButton?.addEventListener('click', toggleChat);
    chatButton?.addEventListener('touchend', (e) => {
        e.preventDefault();
        toggleChat();
    });
    
    // Close chat
    chatClose?.addEventListener('click', closeChat);
    chatClose?.addEventListener('touchend', (e) => {
        e.preventDefault();
        closeChat();
    });
    
    // Send message on Enter (desktop) or button click
    chatInput?.addEventListener('keypress', handleKeyPress);
    chatSend?.addEventListener('click', sendMessage);
    chatSend?.addEventListener('touchend', (e) => {
        e.preventDefault();
        sendMessage();
    });
    
    // Prevent zoom on input focus (mobile)
    chatInput?.addEventListener('focus', () => {
        if (STATE.isMobileView) {
            document.body.style.zoom = '100%';
        }
    });
}

// ============================================================
// RESPONSIVE LISTENERS
// ============================================================

function setupResponsiveListeners() {
    let resizeTimeout;
    
    window.addEventListener('resize', debounce(() => {
        const wasMobile = STATE.isMobileView;
        STATE.isMobileView = window.innerWidth < CONFIG.MOBILE_BREAKPOINT;
        
        // Si cambió el breakpoint, actualizar clases
        if (wasMobile !== STATE.isMobileView) {
            console.log(`📱 Viewport changed: Mobile=${STATE.isMobileView}`);
            updateWidgetForViewport();
        }
    }, CONFIG.DEBOUNCE_DELAY));
    
    // Detectar orientación en mobile
    window.addEventListener('orientationchange', () => {
        setTimeout(updateWidgetForViewport, 500);
    });
}

function updateWidgetForViewport() {
    const widget = document.getElementById('chatWidget');
    const chatMessages = document.getElementById('chatMessages');
    
    if (!widget) return;
    
    if (STATE.isMobileView) {
        // Mobile: fullscreen
        widget.style.borderRadius = '0';
    } else {
        // Desktop: flotante
        widget.style.borderRadius = '16px';
    }
    
    // Scroll to bottom después de layout shift
    setTimeout(() => {
        scrollToBottom();
    }, 100);
}

// ============================================================
// CHAT TOGGLE & OPEN/CLOSE
// ============================================================

function toggleChat() {
    STATE.chatOpen ? closeChat() : openChat();
}

function openChat() {
    if (STATE.chatOpen) return;
    
    const widget = document.getElementById('chatWidget');
    const button = document.getElementById('chatButton');
    const input = document.getElementById('chatInput');
    
    if (!widget) return;
    
    STATE.chatOpen = true;
    widget.classList.add('open');
    
    // Ocultar botón después de animación
    setTimeout(() => {
        if (button) button.style.display = 'none';
    }, CONFIG.ANIMATION_DURATION);
    
    // Focus en input después de que se abra
    setTimeout(() => {
        input?.focus();
        scrollToBottom();
    }, CONFIG.ANIMATION_DURATION / 2);
    
    // Remove badge notification
    const badge = document.querySelector('.chat-button-badge');
    if (badge) badge.style.display = 'none';
    
    console.log('📂 Chat opened');
}

function closeChat() {
    if (!STATE.chatOpen) return;
    
    const widget = document.getElementById('chatWidget');
    const button = document.getElementById('chatButton');
    
    if (!widget) return;
    
    STATE.chatOpen = false;
    widget.classList.remove('open');
    
    // Mostrar botón después de animación
    setTimeout(() => {
        if (button) button.style.display = 'flex';
    }, CONFIG.ANIMATION_DURATION);
    
    console.log('📁 Chat closed');
}

// ============================================================
// MESSAGE HANDLING
// ============================================================

function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

async function sendMessage() {
    const input = document.getElementById('chatInput');
    const message = input?.value?.trim();
    
    if (!message || STATE.isWaitingResponse) return;
    
    // Clear input
    if (input) input.value = '';
    
    // Add user message
    addMessage(message, 'user');
    
    // Show loading
    const loadingId = addMessage('Pensando...', 'bot', true);
    STATE.isWaitingResponse = true;
    
    try {
        // Call API
        const response = await fetch(`${CONFIG.API_URL}/api/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                session_id: STATE.sessionId
            }),
            timeout: 30000
        });
        
        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Remove loading message
        removeMessage(loadingId);
        
        // Add bot response
        addMessage(data.answer, 'bot');
        
        // Add handoff info if needed
        if (data.needs_human) {
            // El mensaje ya incluye el handoff, no agregar otro
        }
        
        // Log success
        console.log(`✅ Response received (docs: ${data.num_docs})`);
        
    } catch (error) {
        console.error('❌ Error:', error);
        
        // Remove loading
        removeMessage(loadingId);
        
        // Add error message
        addMessage(
            'Lo siento, hubo un problema al procesar tu consulta. ' +
            'Por favor, intenta nuevamente o contacta a info@chinfield.com',
            'bot'
        );
    } finally {
        STATE.isWaitingResponse = false;
        
        // Re-focus en input
        setTimeout(() => {
            document.getElementById('chatInput')?.focus();
        }, 100);
    }
}

// ============================================================
// MESSAGE DOM OPERATIONS
// ============================================================

function addMessage(text, sender, isLoading = false) {
    const messagesContainer = document.getElementById('chatMessages');
    if (!messagesContainer) return null;
    
    const messageDiv = document.createElement('div');
    const messageId = `msg-${Date.now()}-${Math.random()}`;
    
    messageDiv.id = messageId;
    messageDiv.className = `message ${sender}`;
    
    if (isLoading) {
        messageDiv.classList.add('loading');
        messageDiv.textContent = text;
    } else {
        // Permitir HTML seguro (para links en mensajes de handoff)
        messageDiv.innerHTML = sanitizeHTML(text);
    }
    
    messagesContainer.appendChild(messageDiv);
    
    // Scroll smooth to bottom
    setTimeout(() => {
        scrollToBottom();
    }, 50);
    
    STATE.messageCount++;
    
    return messageId;
}

function removeMessage(messageId) {
    const message = document.getElementById(messageId);
    if (message) {
        message.remove();
    }
}

function scrollToBottom() {
    const messagesContainer = document.getElementById('chatMessages');
    if (messagesContainer) {
        // Usar requestAnimationFrame para smooth scroll
        requestAnimationFrame(() => {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        });
    }
}

// ============================================================
// WELCOME MESSAGE
// ============================================================

function addWelcomeMessage() {
    const messagesContainer = document.getElementById('chatMessages');
    if (!messagesContainer || messagesContainer.children.length > 0) return;
    
    const welcomeDiv = document.createElement('div');
    welcomeDiv.className = 'message bot welcome';
    welcomeDiv.innerHTML = `
        <strong>👋 ¡Bienvenido al Asistente Chinfield!</strong><br/><br/>
        Puedo ayudarte con información sobre nuestros productos:
        <ul>
            <li>💊 Dosificaciones y posología</li>
            <li>🎯 Indicaciones terapéuticas</li>
            <li>⚠️ Contraindicaciones</li>
            <li>💉 Vías de administración</li>
        </ul><br/>
        <em>¿En qué puedo asistirte?</em>
    `;
    
    messagesContainer.appendChild(welcomeDiv);
}

// ============================================================
// UTILITY FUNCTIONS
// ============================================================

function generateSessionId() {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function sanitizeHTML(html) {
    /**
     * Sanitizar HTML básico para prevenir XSS
     * Solo permite: <br>, <strong>, <em>, <a href>, <ul>, <li>
     */
    const temp = document.createElement('div');
    temp.textContent = html;
    
    // Reemplazar saltos de línea
    let sanitized = temp.innerHTML
        .replace(/\n/g, '<br>')
        .replace(/&lt;br&gt;/g, '<br>')
        .replace(/&lt;strong&gt;/g, '<strong>')
        .replace(/&lt;\/strong&gt;/g, '</strong>')
        .replace(/&lt;em&gt;/g, '<em>')
        .replace(/&lt;\/em&gt;/g, '</em>')
        .replace(/&lt;a href="([^"]+)"&gt;/g, '<a href="$1" target="_blank" rel="noopener noreferrer">')
        .replace(/&lt;\/a&gt;/g, '</a>')
        .replace(/&lt;ul&gt;/g, '<ul>')
        .replace(/&lt;\/ul&gt;/g, '</ul>')
        .replace(/&lt;li&gt;/g, '<li>')
        .replace(/&lt;\/li&gt;/g, '</li>');
    
    return sanitized;
}

// ============================================================
// PUBLIC API - Para llamadas externas
// ============================================================

// Exponer en global scope para llamadas externas
window.ChinfiledChat = {
    open: openChat,
    close: closeChat,
    toggle: toggleChat,
    sendMessage: (msg) => {
        const input = document.getElementById('chatInput');
        if (input) {
            input.value = msg;
            sendMessage();
        }
    },
    askAbout: (productName) => {
        openChat();
        setTimeout(() => {
            window.ChinfiledChat.sendMessage(`¿Qué es ${productName}?`);
        }, 300);
    },
    getState: () => STATE,
    getSessionId: () => STATE.sessionId
};

console.log('📦 ChinfiledChat API available: window.ChinfiledChat.*');
