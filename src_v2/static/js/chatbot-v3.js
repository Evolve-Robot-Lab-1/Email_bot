/**
 * AI Chatbot v3 - Clean Modern Design
 * Enhanced context-aware email generation with CSV data
 */

class AIChatbot {
    constructor() {
        this.isOpen = false;
        this.isTyping = false;
        this.conversationHistory = [];
        this.recipientData = null;
        this.campaignGoal = null;
        this.lastGeneratedContent = null; // Store last generated email

        // DOM elements
        this.toggle = document.getElementById('chatbot-toggle');
        this.window = document.getElementById('chatbot-window');
        this.close = document.getElementById('chatbot-close');
        this.minimize = document.getElementById('chatbot-minimize');
        this.messages = document.getElementById('chatbot-messages');
        this.input = document.getElementById('chatbot-input');
        this.send = document.getElementById('chatbot-send');
        this.clear = document.getElementById('chatbot-clear');
        this.status = document.getElementById('chatbot-status');
        this.uploadBtn = document.getElementById('chatbot-upload-btn');
        this.documentInput = document.getElementById('chatbot-document-input');

        // Document state
        this.uploadedDocument = null;
        this.campaignData = null;
        this.emailTemplate = null;

        if (this.toggle) {
            this.init();
        }
    }

    init() {
        // Event listeners
        this.toggle.addEventListener('click', () => this.toggleChat());
        this.close.addEventListener('click', () => this.toggleChat());
        this.minimize.addEventListener('click', () => this.toggleChat());
        this.send.addEventListener('click', () => this.sendMessage());
        this.clear.addEventListener('click', () => this.clearConversation());

        // Document upload
        this.uploadBtn.addEventListener('click', () => this.documentInput.click());
        this.documentInput.addEventListener('change', (e) => this.handleDocumentUpload(e));

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
            this.input.style.height = Math.min(this.input.scrollHeight, 100) + 'px';
        });

        // Listen for context updates from campaign page
        window.addEventListener('recipientDataLoaded', (e) => {
            this.recipientData = e.detail;
            this.addMessage('CSV data loaded! I can now generate personalized emails for each recipient.', 'assistant', 'success');
        });

        window.addEventListener('campaignGoalSet', (e) => {
            this.campaignGoal = e.detail;
            this.addMessage(`Campaign goal set to: ${e.detail}. I'll tailor emails accordingly.`, 'assistant', 'success');
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

        // Add user message
        this.addMessage(message, 'user');
        this.input.value = '';
        this.input.style.height = 'auto';

        // Check for commands
        if (message.startsWith('/')) {
            await this.handleCommand(message);
            return;
        }

        // Regular chat
        await this.chat(message);
    }

    async chat(message) {
        this.setTyping(true);

        const context = this.getPageContext();

        try {
            const response = await fetch('/api/ai/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    message,
                    context: {
                        ...context,
                        campaign_goal: this.campaignGoal,
                        has_recipients: !!this.recipientData
                    }
                })
            });

            const data = await response.json();

            if (data.error) {
                if (data.setup_required) {
                    this.addMessage(
                        'Please set up your Groq API key. The key is already configured in .env file.',
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
            this.setTyping(false);
        }
    }

    async handleCommand(command) {
        const parts = command.toLowerCase().split(' ');
        const cmd = parts[0];
        const args = parts.slice(1).join(' ');

        switch(cmd) {
            case '/help':
                this.showHelp();
                break;

            case '/draft':
                await this.generateDraft(args);
                break;

            case '/improve':
                await this.improveEmail();
                break;

            case '/personalize':
                await this.personalizeForCompany(args);
                break;

            case '/subject':
                await this.generateSubjects();
                break;

            case '/analyze':
                await this.analyzeRecipients();
                break;

            case '/pitch':
                await this.generatePitch();
                break;

            case '/goal':
                this.showGoalOptions();
                break;

            // New campaign control commands
            case '/apply':
                this.applyLastGenerated();
                break;

            case '/fill':
                this.fillField(args);
                break;

            case '/start':
                await this.startCampaign();
                break;

            case '/pause':
                await this.pauseCampaign();
                break;

            case '/resume':
                await this.resumeCampaign();
                break;

            case '/status':
                await this.getCampaignStatus();
                break;

            case '/preview':
                this.previewCurrentEmail();
                break;

            case '/upload':
                this.documentInput.click();
                this.addMessage('Click to select a campaign document (PDF or DOCX)...', 'assistant');
                break;

            case '/parse':
                await this.parseUploadedDocument();
                break;

            default:
                this.addMessage(
                    `Unknown command: ${cmd}. Type /help for available commands.`,
                    'assistant',
                    'warning'
                );
        }
    }

    showHelp() {
        const helpText = `
**Available Commands:**

**Document Management:**
**/upload** - Upload campaign document (PDF/DOCX)
**/parse** - Parse uploaded document and extract campaign info

**Content Generation:**
**/draft** - Generate complete email from CSV context
**/improve** - Enhance current email
**/personalize [company]** - Get company-specific insights
**/subject** - Generate compelling subject lines
**/pitch** - Generate elevator pitch

**Campaign Control:**
**/apply** - Apply last generated content to form
**/fill [field]** - Fill specific field (subject/body)
**/preview** - Preview current email
**/start** - Start the campaign
**/pause** - Pause running campaign
**/resume** - Resume paused campaign
**/status** - Get campaign status

**Settings:**
**/goal** - Set campaign goal
**/analyze** - Analyze uploaded recipients

**Tips:**
• Use paperclip button or /upload to add campaign doc
• Click action buttons to apply content directly
• AI-generated content auto-includes apply buttons
        `;
        this.addMessage(helpText, 'assistant');
    }

    async generateDraft(companyName) {
        if (!this.recipientData || this.recipientData.length === 0) {
            this.addMessage('Please upload a CSV file first to generate personalized emails.', 'assistant', 'warning');
            return;
        }

        this.setTyping(true);

        try {
            // Find company in recipients
            const recipient = companyName
                ? this.recipientData.find(r => r.company?.toLowerCase().includes(companyName.toLowerCase()))
                : this.recipientData[0];

            if (!recipient) {
                this.addMessage(`Company "${companyName}" not found in recipients.`, 'assistant', 'warning');
                this.setTyping(false);
                return;
            }

            // Check if we have campaign data from parsed document
            if (this.campaignData) {
                // Use new personalized generation with CSV company details
                const response = await fetch('/api/ai/generate-personalized-email', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        csv_row: recipient,
                        campaign_info: this.campaignData,
                        email_template: this.emailTemplate || ''
                    })
                });

                const data = await response.json();

                if (data.success) {
                    this.lastGeneratedContent = {
                        subject: data.subject,
                        body: data.body,
                        company: recipient.company || recipient.Company_Name
                    };

                    const personalizationInfo = data.personalization_data
                        ? `\n**Personalized using:** ${data.personalization_data.industry} company, ${data.personalization_data.company_size}`
                        : '';

                    const message = `
**Personalized Email for ${recipient.Company_Name || recipient.company}:**

**Subject:** ${data.subject}

${data.body}
${personalizationInfo}
                    `;

                    const messageId = 'msg-' + Date.now();
                    this.addMessageWithActions(message, 'assistant', 'success', [
                        { text: 'Apply to Campaign', action: 'apply-email', data: { subject: data.subject, body: data.body } },
                        { text: 'Use Subject Only', action: 'apply-subject', data: { subject: data.subject } },
                        { text: 'Use Body Only', action: 'apply-body', data: { body: data.body } }
                    ], messageId);
                } else {
                    this.addMessage(`Error generating email: ${data.error}`, 'assistant', 'error');
                }
            } else {
                // Fallback to old method if no campaign data
                const productInfo = document.getElementById('product-info')?.value || '';
                const ourCompany = document.getElementById('company-info')?.value || '';
                const audience = document.getElementById('audience-select')?.value || 'VCs';
                const emailStyle = document.getElementById('email-style-select')?.value || 'professional';
                const subjectTemplate = document.getElementById('subject-template')?.value || '';

                const response = await fetch('/api/ai/generate-email', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        company: recipient,
                        product: productInfo,
                        audience: audience,
                        email_style: emailStyle,
                        subject_template: subjectTemplate,
                        our_company: ourCompany,
                        campaign_goal: this.campaignGoal
                    })
                });

                const data = await response.json();

                if (data.success) {
                    this.lastGeneratedContent = {
                        subject: data.subject,
                        body: data.body,
                        company: recipient.company
                    };

                    const message = `
**Generated Email for ${recipient.company}:**

**Subject:** ${data.subject}

${data.body}

${data.why_analysis ? `\n**Why they need it:** ${data.why_analysis}` : ''}
                    `;

                    const messageId = 'msg-' + Date.now();
                    this.addMessageWithActions(message, 'assistant', 'success', [
                        { text: 'Apply to Campaign', action: 'apply-email', data: { subject: data.subject, body: data.body } },
                        { text: 'Use Subject Only', action: 'apply-subject', data: { subject: data.subject } },
                        { text: 'Use Body Only', action: 'apply-body', data: { body: data.body } }
                    ], messageId);
                } else {
                    this.addMessage(`Error generating email: ${data.error}`, 'assistant', 'error');
                }
            }

        } catch (error) {
            this.addMessage(`Error: ${error.message}`, 'assistant', 'error');
        } finally {
            this.setTyping(false);
        }
    }

    async improveEmail() {
        const emailBody = document.getElementById('message-template')?.value ||
                         document.getElementById('modal-body')?.value;

        if (!emailBody) {
            this.addMessage('No email found to improve. Please write an email first.', 'assistant', 'warning');
            return;
        }

        const company = this.getCurrentCompany();
        const audience = document.getElementById('audience-select')?.value || 'VCs';

        this.setTyping(true);

        try {
            const response = await fetch('/api/ai/enhance-email', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    body: emailBody,
                    company: company || 'Target Company',
                    audience: audience
                })
            });

            const data = await response.json();

            if (data.success) {
                const message = `
**Improved Email:**

**Subject:** ${data.subject}

${data.body}
                `;
                this.addMessage(message, 'assistant', 'success');
            } else {
                this.addMessage(`Error: ${data.error}`, 'assistant', 'error');
            }

        } catch (error) {
            this.addMessage(`Error: ${error.message}`, 'assistant', 'error');
        } finally {
            this.setTyping(false);
        }
    }

    async personalizeForCompany(companyName) {
        if (!this.recipientData || this.recipientData.length === 0) {
            this.addMessage('Please upload a CSV file first.', 'assistant', 'warning');
            return;
        }

        const recipient = companyName
            ? this.recipientData.find(r => r.company?.toLowerCase().includes(companyName.toLowerCase()))
            : this.recipientData[0];

        if (!recipient) {
            this.addMessage(`Company "${companyName}" not found. Available companies:`, 'assistant');
            const companies = this.recipientData.slice(0, 10).map(r => r.company).join(', ');
            this.addMessage(companies, 'assistant');
            return;
        }

        this.setTyping(true);

        try {
            const response = await fetch('/api/ai/analyze-company', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ company: recipient })
            });

            const data = await response.json();

            if (data.success) {
                const message = `
**Insights for ${recipient.company}:**

**Recommended Tone:** ${data.tone}

**Focus Areas:**
${data.focus_areas.map(a => `• ${a}`).join('\n')}

**Talking Points:**
${data.talking_points.map(p => `• ${p}`).join('\n')}

${recipient.details ? `\n**Company Details:** ${recipient.details}` : ''}
                `;
                this.addMessage(message, 'assistant', 'success');
            } else {
                this.addMessage(`Error: ${data.error}`, 'assistant', 'error');
            }

        } catch (error) {
            this.addMessage(`Error: ${error.message}`, 'assistant', 'error');
        } finally {
            this.setTyping(false);
        }
    }

    async generateSubjects() {
        const company = this.getCurrentCompany() || 'Target Company';
        const audience = document.getElementById('audience-select')?.value || 'VCs';
        const product = document.getElementById('product-info')?.value || '';

        this.setTyping(true);

        try {
            const prompt = `Generate 5 compelling email subject lines for ${company} (${audience} audience). Product: ${product}`;

            const response = await fetch('/api/ai/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    message: prompt,
                    context: {
                        page: 'campaign',
                        company_name: company,
                        audience_type: audience,
                        campaign_goal: this.campaignGoal
                    }
                })
            });

            const data = await response.json();

            if (data.success || data.response) {
                this.addMessage('**Subject Line Suggestions:**\n\n' + (data.response || data.success), 'assistant', 'success');
            } else {
                this.addMessage(`Error: ${data.error}`, 'assistant', 'error');
            }

        } catch (error) {
            this.addMessage(`Error: ${error.message}`, 'assistant', 'error');
        } finally {
            this.setTyping(false);
        }
    }

    async analyzeRecipients() {
        if (!this.recipientData || this.recipientData.length === 0) {
            this.addMessage('No recipients loaded. Please upload a CSV file first.', 'assistant', 'warning');
            return;
        }

        const analysis = `
**Recipients Analysis:**

**Total Recipients:** ${this.recipientData.length}

**Sample Companies:**
${this.recipientData.slice(0, 5).map(r => `• ${r.company} - ${r.email}`).join('\n')}

**Available Data Fields:**
${Object.keys(this.recipientData[0]).map(k => `• ${k}`).join('\n')}

**Campaign Goal:** ${this.campaignGoal || 'Not set (use /goal to set)'}

Ready to generate personalized emails for all recipients!
        `;
        this.addMessage(analysis, 'assistant', 'success');
    }

    async generatePitch() {
        const product = document.getElementById('product-info')?.value || '';
        const company = document.getElementById('company-info')?.value || '';

        if (!product) {
            this.addMessage('Please add product description in the campaign form first.', 'assistant', 'warning');
            return;
        }

        this.setTyping(true);

        try {
            const prompt = `Generate a 30-second elevator pitch for: ${product}. Company: ${company}. Make it compelling for ${this.campaignGoal || 'investors'}.`;

            const response = await fetch('/api/ai/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    message: prompt,
                    context: {
                        campaign_goal: this.campaignGoal
                    }
                })
            });

            const data = await response.json();

            if (data.success || data.response) {
                this.addMessage('**Elevator Pitch:**\n\n' + (data.response || data.success), 'assistant', 'success');
            } else {
                this.addMessage(`Error: ${data.error}`, 'assistant', 'error');
            }

        } catch (error) {
            this.addMessage(`Error: ${error.message}`, 'assistant', 'error');
        } finally {
            this.setTyping(false);
        }
    }

    showGoalOptions() {
        const message = `
**Select Campaign Goal:**

Click to set your campaign goal:

**1. Seeking VC Funding** - Pitch to investors
**2. Selling AI/Robotics Services** - B2B sales
**3. Partnership Opportunities** - Strategic alliances
**4. Customer Acquisition** - Direct sales

Current goal: ${this.campaignGoal || 'Not set'}
        `;
        this.addMessage(message, 'assistant');
    }

    addMessage(text, sender, type = '') {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${sender}${type ? ' ' + type : ''}`;

        const bubble = document.createElement('div');
        bubble.className = 'chat-bubble';

        // Format text (markdown-style)
        let formattedText = text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n/g, '<br>');

        bubble.innerHTML = formattedText;
        messageDiv.appendChild(bubble);
        this.messages.appendChild(messageDiv);

        // Scroll to bottom
        this.messages.scrollTop = this.messages.scrollHeight;
    }

    setTyping(isTyping) {
        this.isTyping = isTyping;
        this.send.disabled = isTyping;

        if (isTyping) {
            this.setStatus('AI is thinking...');

            // Add typing indicator
            const typingDiv = document.createElement('div');
            typingDiv.className = 'chat-message assistant';
            typingDiv.id = 'typing-indicator';
            typingDiv.innerHTML = `
                <div class="chat-bubble">
                    <div class="chatbot-typing">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                </div>
            `;
            this.messages.appendChild(typingDiv);
            this.messages.scrollTop = this.messages.scrollHeight;
        } else {
            this.setStatus('Ready');

            // Remove typing indicator
            const typing = document.getElementById('typing-indicator');
            if (typing) typing.remove();
        }
    }

    setStatus(text) {
        if (this.status) {
            this.status.textContent = text;
        }
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

    async handleDocumentUpload(event) {
        const file = event.target.files[0];
        if (!file) return;

        // Validate file type
        const validTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword'];
        if (!validTypes.includes(file.type) && !file.name.match(/\.(pdf|docx|doc)$/i)) {
            this.addMessage('Invalid file type. Please upload a PDF or DOCX file.', 'assistant', 'error');
            return;
        }

        // Validate file size (10MB limit)
        if (file.size > 10 * 1024 * 1024) {
            this.addMessage('File too large. Please upload a file smaller than 10MB.', 'assistant', 'error');
            return;
        }

        this.addMessage(`Uploading **${file.name}**...`, 'assistant');
        this.uploadBtn.classList.add('uploading');
        this.setTyping(true);

        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch('/api/chatbot/upload-document', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                this.uploadedDocument = data.filename;
                this.addMessage(
                    `✅ **Document uploaded:** ${file.name}\n\nType **/parse** to extract campaign information.`,
                    'assistant',
                    'success'
                );
            } else {
                this.addMessage(`Upload failed: ${data.error}`, 'assistant', 'error');
            }

        } catch (error) {
            this.addMessage(`Upload error: ${error.message}`, 'assistant', 'error');
        } finally {
            this.uploadBtn.classList.remove('uploading');
            this.setTyping(false);
            // Reset file input
            this.documentInput.value = '';
        }
    }

    async parseUploadedDocument() {
        if (!this.uploadedDocument) {
            this.addMessage('No document uploaded. Use **/upload** or click the paperclip button first.', 'assistant', 'warning');
            return;
        }

        this.addMessage('Parsing document with AI...', 'assistant');
        this.setTyping(true);

        try {
            const response = await fetch('/api/chatbot/parse-document', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    filepath: `uploads/documents/${this.uploadedDocument}`
                })
            });

            const data = await response.json();

            if (data.success) {
                this.campaignData = data.campaign_data;
                this.emailTemplate = data.email_template;

                const summary = `
**📄 Campaign Document Parsed Successfully!**

**Company:** ${data.campaign_data.company}
**Product:** ${data.campaign_data.product}
**Value Props:** ${data.campaign_data.value_props}
**Metrics:** ${data.campaign_data.metrics}
**Goal:** ${data.campaign_data.goal}

**Description:** ${data.campaign_data.description}

**Email Template:**
${data.email_template.substring(0, 150)}...

**Would you like me to update the campaign form with this information?**
                `;

                const messageId = 'msg-parse-' + Date.now();
                this.addMessageWithActions(summary, 'assistant', 'success', [
                    {
                        text: '✓ Update Form',
                        action: 'update-campaign-form',
                        data: {
                            campaign_data: data.campaign_data,
                            email_template: data.email_template
                        }
                    },
                    {
                        text: '✗ Ignore',
                        action: 'ignore',
                        data: {}
                    }
                ], messageId);

            } else {
                this.addMessage(`Parsing failed: ${data.error}`, 'assistant', 'error');
            }

        } catch (error) {
            this.addMessage(`Parsing error: ${error.message}`, 'assistant', 'error');
        } finally {
            this.setTyping(false);
        }
    }

    getPageContext() {
        const pathname = window.location.pathname;
        let page = 'campaign';

        if (pathname.includes('inbox')) page = 'inbox';
        else if (pathname.includes('analytics')) page = 'analytics';

        return {
            page: page,
            company_name: this.getCurrentCompany(),
            audience_type: document.getElementById('audience-select')?.value || 'VCs',
            has_data: !!this.recipientData
        };
    }

    getCurrentCompany() {
        // Try multiple sources
        const modalCompany = document.getElementById('modal-company-name');
        if (modalCompany) return modalCompany.textContent;

        if (this.recipientData && this.recipientData.length > 0) {
            return this.recipientData[0].company;
        }

        return null;
    }

    // Field Injection Methods
    injectToField(fieldId, value) {
        const field = document.getElementById(fieldId);
        if (field) {
            field.value = value;
            field.dispatchEvent(new Event('input', { bubbles: true }));
            this.addMessage(`✓ Updated ${fieldId}`, 'assistant', 'success');
            return true;
        }
        this.addMessage(`Field ${fieldId} not found`, 'assistant', 'error');
        return false;
    }

    applyGeneratedEmail(subject, body) {
        let success = true;
        if (subject) success = this.injectToField('subject-template', subject) && success;
        if (body) success = this.injectToField('message-template', body) && success;

        if (success) {
            this.addMessage('✓ Email content applied to campaign!', 'assistant', 'success');
            // Navigate to compose step if not there
            if (typeof showStep === 'function') {
                showStep(2);
            }
        }
    }

    applyLastGenerated() {
        if (!this.lastGeneratedContent) {
            this.addMessage('No generated content to apply. Use /draft first.', 'assistant', 'warning');
            return;
        }

        this.applyGeneratedEmail(
            this.lastGeneratedContent.subject,
            this.lastGeneratedContent.body
        );
    }

    fillField(fieldName) {
        if (!this.lastGeneratedContent) {
            this.addMessage('No generated content available. Use /draft first.', 'assistant', 'warning');
            return;
        }

        if (fieldName.includes('subject')) {
            this.injectToField('subject-template', this.lastGeneratedContent.subject);
        } else if (fieldName.includes('body') || fieldName.includes('message')) {
            this.injectToField('message-template', this.lastGeneratedContent.body);
        } else {
            this.addMessage(`Unknown field: ${fieldName}. Use 'subject' or 'body'.`, 'assistant', 'warning');
        }
    }

    previewCurrentEmail() {
        const subject = document.getElementById('subject-template')?.value;
        const body = document.getElementById('message-template')?.value;

        if (!subject && !body) {
            this.addMessage('No email content to preview. Please compose an email first.', 'assistant', 'warning');
            return;
        }

        const preview = `
**Current Email Preview:**

**Subject:** ${subject || '[No subject]'}

${body || '[No body]'}
        `;
        this.addMessage(preview, 'assistant');
    }

    // Campaign Control Methods
    async startCampaign() {
        const btn = document.getElementById('start-campaign-btn');
        if (!btn) {
            this.addMessage('Campaign not ready. Please complete setup first.', 'assistant', 'warning');
            return;
        }

        if (typeof emailsData === 'undefined' || emailsData.length === 0) {
            this.addMessage('Please generate emails first before starting campaign.', 'assistant', 'warning');
            return;
        }

        this.addMessage('Starting campaign...', 'assistant');
        btn.click();

        setTimeout(() => {
            this.addMessage(`✓ Campaign started with ${emailsData.length} recipients!`, 'assistant', 'success');
        }, 1000);
    }

    async pauseCampaign() {
        const response = await fetch('/api/campaign/pause', { method: 'POST' });
        const data = await response.json();

        if (data.success) {
            this.addMessage('✓ Campaign paused', 'assistant', 'success');
        } else {
            this.addMessage(`Error: ${data.error}`, 'assistant', 'error');
        }
    }

    async resumeCampaign() {
        const response = await fetch('/api/campaign/resume', { method: 'POST' });
        const data = await response.json();

        if (data.success) {
            this.addMessage('✓ Campaign resumed', 'assistant', 'success');
        } else {
            this.addMessage(`Error: ${data.error}`, 'assistant', 'error');
        }
    }

    async getCampaignStatus() {
        const response = await fetch('/api/campaign/status');
        const data = await response.json();

        if (data.success) {
            const status = `
**Campaign Status:**
• Status: ${data.status}
• Total: ${data.total}
• Sent: ${data.sent}
• Failed: ${data.failed}
• Progress: ${data.total > 0 ? Math.round((data.sent + data.failed) / data.total * 100) : 0}%
            `;
            this.addMessage(status, 'assistant');
        } else {
            this.addMessage('No active campaign', 'assistant', 'warning');
        }
    }

    // Enhanced message with action buttons
    addMessageWithActions(text, sender, type = '', actions = [], messageId = '') {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${sender}${type ? ' ' + type : ''}`;
        if (messageId) messageDiv.id = messageId;

        const bubble = document.createElement('div');
        bubble.className = 'chat-bubble';

        // Format text
        let formattedText = text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n/g, '<br>');

        bubble.innerHTML = formattedText;

        // Add action buttons if provided
        if (actions && actions.length > 0) {
            const buttonContainer = document.createElement('div');
            buttonContainer.className = 'chat-actions';
            buttonContainer.style.cssText = 'margin-top: 8px; display: flex; gap: 6px; flex-wrap: wrap;';

            actions.forEach(action => {
                const button = document.createElement('button');
                button.className = 'chat-action-btn';
                button.textContent = action.text;
                button.onclick = () => this.handleActionButton(action.action, action.data);
                buttonContainer.appendChild(button);
            });

            bubble.appendChild(buttonContainer);
        }

        messageDiv.appendChild(bubble);
        this.messages.appendChild(messageDiv);
        this.messages.scrollTop = this.messages.scrollHeight;
    }

    handleActionButton(action, data) {
        switch(action) {
            case 'apply-email':
                this.applyGeneratedEmail(data.subject, data.body);
                break;
            case 'apply-subject':
                this.injectToField('subject-template', data.subject);
                break;
            case 'apply-body':
                this.injectToField('message-template', data.body);
                break;
            case 'set-goal':
                if (data.goal) {
                    const goalSelect = document.getElementById('campaign-goal-select');
                    if (goalSelect) {
                        goalSelect.value = data.goal;
                        goalSelect.dispatchEvent(new Event('change'));
                        this.campaignGoal = data.goal;
                        this.addMessage(`✓ Campaign goal set to: ${data.goal}`, 'assistant', 'success');
                    }
                }
                break;
            case 'update-campaign-form':
                this.updateCampaignForm(data.campaign_data, data.email_template);
                break;
            case 'ignore':
                this.addMessage('Okay, I won\'t update the form. The parsed data is still available for later use.', 'assistant');
                break;
            default:
                console.log('Unknown action:', action, data);
        }
    }

    updateCampaignForm(campaignData, emailTemplate) {
        // Update form fields with campaign data
        const yourCompanyField = document.getElementById('your-company');
        const companyInfoField = document.getElementById('company-info');
        const productInfoField = document.getElementById('product-info');
        const subjectField = document.getElementById('subject-template');
        const messageField = document.getElementById('message-template');

        if (yourCompanyField) yourCompanyField.value = campaignData.company || '';
        if (companyInfoField) companyInfoField.value = campaignData.description || '';
        if (productInfoField) {
            const productText = `${campaignData.product}\n\nValue Props: ${campaignData.value_props}\n\nMetrics: ${campaignData.metrics}`;
            productInfoField.value = productText;
        }
        if (messageField && emailTemplate) messageField.value = emailTemplate;

        // Trigger events to update UI
        [yourCompanyField, companyInfoField, productInfoField, messageField].forEach(field => {
            if (field) field.dispatchEvent(new Event('input', { bubbles: true }));
        });

        this.addMessage('✓ Campaign form updated successfully! Upload your CSV to start generating personalized emails.', 'assistant', 'success');
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.aiChatbot = new AIChatbot();
});