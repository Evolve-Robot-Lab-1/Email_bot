/**
 * AI Chatbot - Email Writing Assistant
 * Powered by Groq API
 */

class AIChatbot {
    constructor() {
        this.isOpen = false;
        this.isTyping = false;
        this.conversationHistory = [];

        // DOM elements
        this.toggle = document.getElementById('chatbot-toggle');
        this.window = document.getElementById('chatbot-window');
        this.close = document.getElementById('chatbot-close');
        this.messages = document.getElementById('chatbot-messages');
        this.input = document.getElementById('chatbot-input');
        this.send = document.getElementById('chatbot-send');
        this.clear = document.getElementById('chatbot-clear');
        this.status = document.getElementById('chatbot-status');

        this.init();
    }

    init() {
        // Event listeners
        this.toggle.addEventListener('click', () => this.toggleChat());
        this.close.addEventListener('click', () => this.toggleChat());
        this.send.addEventListener('click', () => this.sendMessage());
        this.clear.addEventListener('click', () => this.clearConversation());

        // Enter to send
        this.input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Auto-resize input
        this.input.addEventListener('input', () => {
            this.input.style.height = 'auto';
            this.input.style.height = this.input.scrollHeight + 'px';
        });
    }

    toggleChat() {
        this.isOpen = !this.isOpen;

        if (this.isOpen) {
            this.toggle.classList.add('hidden');
            this.window.classList.remove('hidden');
            this.input.focus();
        } else {
            this.toggle.classList.remove('hidden');
            this.window.classList.add('hidden');
        }
    }

    async sendMessage() {
        const message = this.input.value.trim();

        if (!message || this.isTyping) return;

        // Add user message to UI
        this.addMessage(message, 'user');
        this.input.value = '';

        // Check for special commands
        if (message.startsWith('/')) {
            this.handleCommand(message);
            return;
        }

        // Get context from current page
        const context = this.getPageContext();

        // Call AI API
        this.isTyping = true;
        this.setStatus('AI is typing...');

        try {
            const response = await fetch('/api/ai/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ message, context })
            });

            const data = await response.json();

            if (data.error) {
                if (data.setup_required) {
                    this.addMessage(
                        'Please set up your Groq API key in the .env file. Get your free key at https://console.groq.com/',
                        'assistant',
                        'error'
                    );
                } else {
                    this.addMessage(`Error: ${data.error}`, 'assistant', 'error');
                }
            } else {
                this.addMessage(data.response, 'assistant');
            }

        } catch (error) {
            this.addMessage(`Connection error: ${error.message}`, 'assistant', 'error');
        } finally {
            this.isTyping = false;
            this.setStatus('Ready');
        }
    }

    async handleCommand(command) {
        const cmd = command.toLowerCase().split(' ')[0];

        switch(cmd) {
            case '/improve':
                await this.improveCurrentEmail();
                break;

            case '/subject':
                await this.generateSubject();
                break;

            case '/personalize':
                await this.personalizeEmail();
                break;

            case '/analyze':
                await this.analyzeCompany();
                break;

            case '/help':
                this.showHelp();
                break;

            default:
                this.addMessage(
                    `Unknown command: ${cmd}. Type /help for available commands.`,
                    'assistant',
                    'warning'
                );
        }
    }

    async improveCurrentEmail() {
        // Try to get email content from page
        const emailBody = this.getEmailFromPage();

        if (!emailBody) {
            this.addMessage(
                'No email found on this page. Please go to the Campaign page and select an email to improve.',
                'assistant',
                'warning'
            );
            return;
        }

        const company = this.getCurrentCompany();
        const audience = this.getCurrentAudience();

        this.setStatus('Improving email...');

        try {
            const response = await fetch('/api/ai/enhance-email', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    body: emailBody,
                    company,
                    audience
                })
            });

            const data = await response.json();

            if (data.success) {
                this.addMessage(
                    `**Improved Email:**\n\n**Subject:** ${data.subject}\n\n${data.body}`,
                    'assistant',
                    'success'
                );

                // If on campaign page, offer to apply
                if (window.location.pathname.includes('campaign')) {
                    this.addMessage(
                        'Would you like me to apply these improvements to your email?',
                        'assistant'
                    );
                }
            } else {
                this.addMessage(`Error: ${data.error}`, 'assistant', 'error');
            }

        } catch (error) {
            this.addMessage(`Error: ${error.message}`, 'assistant', 'error');
        } finally {
            this.setStatus('Ready');
        }
    }

    async generateSubject() {
        const company = this.getCurrentCompany();

        if (!company) {
            this.addMessage('Please select a company first.', 'assistant', 'warning');
            return;
        }

        const audience = this.getCurrentAudience();
        const emailBody = this.getEmailFromPage() || '';

        this.setStatus('Generating subject line...');

        try {
            const response = await fetch('/api/ai/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    message: `Generate 3 compelling email subject lines for ${company} (${audience} audience)`,
                    context: { page: 'campaign', company_name: company, audience_type: audience }
                })
            });

            const data = await response.json();

            if (data.success) {
                this.addMessage(data.response, 'assistant');
            } else {
                this.addMessage(`Error: ${data.error}`, 'assistant', 'error');
            }

        } catch (error) {
            this.addMessage(`Error: ${error.message}`, 'assistant', 'error');
        } finally {
            this.setStatus('Ready');
        }
    }

    async personalizeEmail() {
        const company = this.getCurrentCompany();

        if (!company) {
            this.addMessage('Please select a company first.', 'assistant', 'warning');
            return;
        }

        this.setStatus('Analyzing company...');

        try {
            const companyData = this.getCompanyData();

            const response = await fetch('/api/ai/analyze-company', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ company: companyData })
            });

            const data = await response.json();

            if (data.success) {
                const message = `**Personalization Insights for ${company}:**\n\n` +
                    `**Tone:** ${data.tone}\n\n` +
                    `**Focus Areas:**\n${data.focus_areas.map(a => `• ${a}`).join('\n')}\n\n` +
                    `**Talking Points:**\n${data.talking_points.map(p => `• ${p}`).join('\n')}`;

                this.addMessage(message, 'assistant', 'success');
            } else {
                this.addMessage(`Error: ${data.error}`, 'assistant', 'error');
            }

        } catch (error) {
            this.addMessage(`Error: ${error.message}`, 'assistant', 'error');
        } finally {
            this.setStatus('Ready');
        }
    }

    async analyzeCompany() {
        await this.personalizeEmail();
    }

    showHelp() {
        const helpText = `**Available Commands:**\n\n` +
            `**/improve** - Enhance current email\n` +
            `**/subject** - Generate subject lines\n` +
            `**/personalize** - Analyze company for personalization\n` +
            `**/analyze** - Same as /personalize\n` +
            `**/help** - Show this help\n\n` +
            `You can also just chat naturally with me!`;

        this.addMessage(helpText, 'assistant');
    }

    addMessage(text, sender, type = '') {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'flex items-start ' + (sender === 'user' ? 'justify-end' : '');

        const bubble = document.createElement('div');
        bubble.className = 'rounded-lg p-3 max-w-[80%] ';

        if (sender === 'user') {
            bubble.classList.add('bg-blue-600', 'text-white');
        } else {
            if (type === 'error') {
                bubble.classList.add('bg-red-100', 'text-red-800');
            } else if (type === 'warning') {
                bubble.classList.add('bg-yellow-100', 'text-yellow-800');
            } else if (type === 'success') {
                bubble.classList.add('bg-green-100', 'text-green-800');
            } else {
                bubble.classList.add('bg-gray-200', 'text-gray-800');
            }
        }

        // Format text (simple markdown)
        let formattedText = text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\n/g, '<br>');

        bubble.innerHTML = `<p class="text-sm whitespace-pre-wrap">${formattedText}</p>`;

        messageDiv.appendChild(bubble);
        this.messages.appendChild(messageDiv);

        // Scroll to bottom
        this.messages.scrollTop = this.messages.scrollHeight;
    }

    clearConversation() {
        // Keep only welcome message
        const messages = this.messages.children;
        while (messages.length > 1) {
            messages[messages.length - 1].remove();
        }

        this.conversationHistory = [];
        this.setStatus('Conversation cleared');
        setTimeout(() => this.setStatus('Ready'), 2000);
    }

    setStatus(text) {
        this.status.textContent = text;
    }

    // Helper functions to get page context
    getPageContext() {
        const page = window.location.pathname.split('/').pop() || 'campaign';

        return {
            page: page,
            company_name: this.getCurrentCompany(),
            audience_type: this.getCurrentAudience()
        };
    }

    getCurrentCompany() {
        // Try to get from page (will be implemented in campaign.html)
        const companyInput = document.querySelector('[data-company-name]');
        return companyInput ? companyInput.getAttribute('data-company-name') : null;
    }

    getCurrentAudience() {
        const audienceSelect = document.getElementById('audience-select');
        return audienceSelect ? audienceSelect.value : 'VCs';
    }

    getEmailFromPage() {
        // Try to get email body from textarea
        const emailInput = document.querySelector('[data-email-body]');
        return emailInput ? emailInput.value : null;
    }

    getCompanyData() {
        // Get full company data from page
        return {
            Company: this.getCurrentCompany(),
            Details: document.querySelector('[data-company-details]')?.textContent || '',
            Website: document.querySelector('[data-company-website]')?.textContent || '',
            Email: document.querySelector('[data-company-email]')?.textContent || ''
        };
    }
}

// Initialize chatbot when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.chatbot = new AIChatbot();
});

// Add pulse animation to chatbot button
const style = document.createElement('style');
style.textContent = `
    .chatbot-pulse {
        animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
    }

    @keyframes pulse {
        0%, 100% {
            box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.7);
        }
        50% {
            box-shadow: 0 0 0 10px rgba(59, 130, 246, 0);
        }
    }
`;
document.head.appendChild(style);
