// Main S-Chat application JavaScript
class SChatApp {
    constructor() {
        this.socket = null;
        this.currentUser = null;
        this.currentChat = null;
    }

    init() {
        this.setupEventListeners();
        this.checkAuthentication();
    }

    setupEventListeners() {
        // Navigation
        document.addEventListener('DOMContentLoaded', () => {
            this.initializePage();
        });
    }

    initializePage() {
        const bodyClass = document.body.className;
        
        if (bodyClass.includes('chat-page')) {
            this.initializeChat();
        } else if (bodyClass.includes('auth-page')) {
            this.initializeAuth();
        }
    }

    initializeAuth() {
        // Auth forms are handled by their respective templates
        console.log('Auth page initialized');
    }

    initializeChat() {
        this.connectSocket();
        this.loadUserChats();
        this.setupChatEventListeners();
    }

    connectSocket() {
        this.socket = io({
            transports: ['websocket', 'polling']
        });

        this.socket.on('connect', () => {
            console.log('Connected to server');
            this.joinCurrentChat();
        });

        this.socket.on('disconnect', () => {
            console.log('Disconnected from server');
        });

        this.socket.on('new_message', (data) => {
            this.handleNewMessage(data);
        });

        this.socket.on('user_typing', (data) => {
            this.handleTypingIndicator(data);
        });

        this.socket.on('error', (data) => {
            this.showError(data.message);
        });
    }

    async loadUserChats() {
        try {
            const response = await fetch('/chats?user_id=' + CURRENT_USER.id);
            const data = await response.json();
            
            if (response.ok) {
                this.displayChats(data.chats);
            } else {
                this.showError('Failed to load chats');
            }
        } catch (error) {
            this.showError('Network error loading chats');
        }
    }

    displayChats(chats) {
        const chatsList = document.getElementById('chatsList');
        chatsList.innerHTML = '';

        chats.forEach(chat => {
            const chatElement = this.createChatElement(chat);
            chatsList.appendChild(chatElement);
        });
    }

    createChatElement(chat) {
        const div = document.createElement('div');
        div.className = 'chat-item';
        div.innerHTML = `
            <div class="chat-name">${chat.name || 'Unnamed Chat'}</div>
            <div class="chat-preview">${chat.last_message?.content || 'No messages'}</div>
            <div class="chat-time">${this.formatTime(chat.last_message?.timestamp)}</div>
        `;

        div.addEventListener('click', () => {
            this.selectChat(chat);
        });

        return div;
    }

    selectChat(chat) {
        this.currentChat = chat;
        this.joinChat(chat.id);
        this.loadChatMessages(chat.id);
        this.updateChatHeader(chat);
    }

    joinChat(chatId) {
        if (this.socket && this.socket.connected) {
            this.socket.emit('join_chat', {
                chat_id: chatId,
                user_id: CURRENT_USER.id
            });
        }
    }

    async loadChatMessages(chatId) {
        try {
            const response = await fetch(`/chats/${chatId}/messages`);
            const data = await response.json();
            
            if (response.ok) {
                this.displayMessages(data.messages);
            }
        } catch (error) {
            this.showError('Failed to load messages');
        }
    }

    displayMessages(messages) {
        const messagesContainer = document.getElementById('chatMessages');
        messagesContainer.innerHTML = '';

        messages.reverse().forEach(message => {
            const messageElement = this.createMessageElement(message);
            messagesContainer.appendChild(messageElement);
        });

        this.scrollToBottom();
    }

    createMessageElement(message) {
        const div = document.createElement('div');
        const isOwn = message.user_id === CURRENT_USER.id;
        
        div.className = `message ${isOwn ? 'own' : 'other'}`;
        div.innerHTML = `
            <div class="message-header">
                <strong>${isOwn ? 'You' : 'User'}</strong>
                <span>${this.formatTime(message.timestamp)}</span>
            </div>
            <div class="message-content">${this.decryptMessage(message.content)}</div>
            ${message.file_path ? `<div class="message-file">📎 Attachment</div>` : ''}
        `;

        return div;
    }

    decryptMessage(encryptedContent) {
        // In a real implementation, this would use Signal Protocol
        // For now, we assume content is already decrypted by the server
        return encryptedContent;
    }

    formatTime(timestamp) {
        if (!timestamp) return '';
        const date = new Date(timestamp);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    scrollToBottom() {
        const messagesContainer = document.getElementById('chatMessages');
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    handleNewMessage(message) {
        if (message.chat_id === this.currentChat?.id) {
            const messageElement = this.createMessageElement(message);
            document.getElementById('chatMessages').appendChild(messageElement);
            this.scrollToBottom();
        }
    }

    handleTypingIndicator(data) {
        const indicator = document.getElementById('typingIndicator');
        if (data.is_typing) {
            indicator.style.display = 'block';
        } else {
            indicator.style.display = 'none';
        }
    }

    showError(message) {
        // Simple error display - you might want to use a toast or modal
        alert('Error: ' + message);
    }

    setupChatEventListeners() {
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendMessageBtn');

        if (messageInput && sendButton) {
            messageInput.addEventListener('input', () => {
                this.handleTyping();
            });

            messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.sendMessage();
                }
            });

            sendButton.addEventListener('click', () => {
                this.sendMessage();
            });
        }
    }

    handleTyping() {
        if (this.socket && this.currentChat) {
            this.socket.emit('typing', {
                chat_id: this.currentChat.id,
                user_id: CURRENT_USER.id,
                is_typing: true
            });

            // Stop typing after 2 seconds
            clearTimeout(this.typingTimeout);
            this.typingTimeout = setTimeout(() => {
                this.socket.emit('typing', {
                    chat_id: this.currentChat.id,
                    user_id: CURRENT_USER.id,
                    is_typing: false
                });
            }, 2000);
        }
    }

    sendMessage() {
        const messageInput = document.getElementById('messageInput');
        const content = messageInput.value.trim();

        if (!content || !this.currentChat) return;

        if (this.socket) {
            this.socket.emit('send_message', {
                chat_id: this.currentChat.id,
                user_id: CURRENT_USER.id,
                content: content,
                type: 'text'
            });

            messageInput.value = '';
        }
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.sChatApp = new SChatApp();
    window.sChatApp.init();
});