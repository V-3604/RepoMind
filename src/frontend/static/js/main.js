/**
 * RepoMind main JavaScript file
 * Handles client-side functionality for the application
 */

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize various UI components
    initFormValidation();
    initRepositoryUpload();
    initChatInterface();
});

/**
 * Initialize form validation for repository upload form
 */
function initFormValidation() {
    const uploadForm = document.getElementById('upload-form');
    
    if (!uploadForm) return;
    
    uploadForm.addEventListener('submit', function(e) {
        const repoTypeSelect = document.getElementById('repo-type');
        const sourceInput = document.getElementById('source-input');
        const fileInput = document.getElementById('file-input');
        
        if (!repoTypeSelect || !sourceInput) return;
        
        const repoType = repoTypeSelect.value;
        let isValid = true;
        
        // Clear previous error messages
        document.querySelectorAll('.error-message').forEach(el => el.remove());
        
        // Validate based on repository type
        if (repoType === 'github') {
            // Validate GitHub URL
            if (!sourceInput.value.trim() || !sourceInput.value.includes('github.com')) {
                showError(sourceInput, 'Please enter a valid GitHub repository URL');
                isValid = false;
            }
        } else if (repoType === 'zip') {
            // Validate ZIP file
            if (!fileInput.files.length) {
                showError(fileInput, 'Please select a ZIP file');
                isValid = false;
            } else if (!fileInput.files[0].name.endsWith('.zip')) {
                showError(fileInput, 'Selected file is not a ZIP file');
                isValid = false;
            }
        } else if (repoType === 'local') {
            // Validate local path
            if (!sourceInput.value.trim()) {
                showError(sourceInput, 'Please enter a valid local path');
                isValid = false;
            }
        }
        
        if (!isValid) {
            e.preventDefault();
        }
    });
}

/**
 * Handle repository upload form type selection
 */
function initRepositoryUpload() {
    const repoTypeSelect = document.getElementById('repo-type');
    const sourceInputGroup = document.getElementById('source-input-group');
    const fileInputGroup = document.getElementById('file-input-group');
    
    if (!repoTypeSelect || !sourceInputGroup || !fileInputGroup) return;
    
    // Show/hide appropriate input fields based on repository type
    repoTypeSelect.addEventListener('change', function() {
        const repoType = repoTypeSelect.value;
        
        if (repoType === 'github' || repoType === 'local') {
            sourceInputGroup.style.display = 'block';
            fileInputGroup.style.display = 'none';
            
            // Update label based on type
            const label = sourceInputGroup.querySelector('label');
            if (label) {
                label.textContent = repoType === 'github' ? 'GitHub URL:' : 'Local Path:';
            }
        } else if (repoType === 'zip') {
            sourceInputGroup.style.display = 'none';
            fileInputGroup.style.display = 'block';
        }
    });
    
    // Trigger change event on load to set initial state
    repoTypeSelect.dispatchEvent(new Event('change'));
}

/**
 * Initialize chat interface for repository queries
 */
function initChatInterface() {
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const chatMessages = document.getElementById('chat-messages');
    
    if (!chatForm || !chatInput || !chatMessages) return;
    
    chatForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const query = chatInput.value.trim();
        if (!query) return;
        
        // Clear input
        chatInput.value = '';
        
        // Add user message to chat
        addMessage('user', query);
        
        // Get repository ID from URL
        const repoId = window.location.pathname.split('/')[2];
        
        try {
            // Make API request
            const response = await fetch(`/api/repos/${repoId}/query`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ query })
            });
            
            if (!response.ok) {
                throw new Error('Failed to get response');
            }
            
            const data = await response.json();
            
            // Add system response to chat
            addMessage('system', data.response.text);
            
            // If there's code in the response, add it
            if (data.response.code) {
                addCodeBlock(data.response.code);
            }
        } catch (error) {
            console.error('Error querying repository:', error);
            addMessage('system', 'Sorry, an error occurred while processing your query.');
        }
    });
}

/**
 * Add a message to the chat interface
 */
function addMessage(type, text) {
    const chatMessages = document.getElementById('chat-messages');
    if (!chatMessages) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;
    messageDiv.textContent = text;
    
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

/**
 * Add a code block to the chat interface
 */
function addCodeBlock(code) {
    const chatMessages = document.getElementById('chat-messages');
    if (!chatMessages) return;
    
    const codeDiv = document.createElement('div');
    codeDiv.className = 'message system-message code-block';
    
    const pre = document.createElement('pre');
    const codeElement = document.createElement('code');
    codeElement.textContent = code;
    
    pre.appendChild(codeElement);
    codeDiv.appendChild(pre);
    chatMessages.appendChild(codeDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

/**
 * Show an error message under an input element
 */
function showError(inputElement, message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.style.color = 'red';
    errorDiv.style.fontSize = '0.8rem';
    errorDiv.style.marginTop = '0.3rem';
    errorDiv.textContent = message;
    
    inputElement.parentNode.appendChild(errorDiv);
    inputElement.style.borderColor = 'red';
} 