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
    
    // Initialize repository listing if on the repos page
    if (document.getElementById('repo-list')) {
        loadRepositories();
    }
    
    // Format dates across the page
    formatDatesOnPage();
    
    // Format sizes across the page
    formatSizesOnPage();
});

/**
 * Format all dates on the page
 */
function formatDatesOnPage() {
    document.querySelectorAll('.date').forEach(element => {
        const originalText = element.textContent;
        const dateText = originalText.replace('Added on ', '').trim();
        if (dateText && !dateText.includes('Unknown')) {
            const formattedDate = formatDate(dateText);
            if (originalText.includes('Added on')) {
                element.textContent = 'Added on ' + formattedDate;
            } else {
                element.textContent = formattedDate;
            }
        }
    });
}

/**
 * Format all sizes on the page
 */
function formatSizesOnPage() {
    document.querySelectorAll('.size').forEach(element => {
        const sizeText = element.textContent.trim();
        if (!sizeText.includes('unknown') && !sizeText.includes('Unknown')) {
            const sizeMatch = sizeText.match(/(\d+)/);
            if (sizeMatch && sizeMatch[1]) {
                const size = parseInt(sizeMatch[1]);
                if (!isNaN(size)) {
                    element.textContent = formatSize(size);
                }
            }
        }
    });
}

/**
 * Initialize form validation for repository upload form
 */
function initFormValidation() {
    const uploadForm = document.getElementById('upload-form');
    
    if (!uploadForm) return;
    
    uploadForm.addEventListener('submit', function(e) {
        const repoTypeSelect = document.getElementById('repo-type');
        const githubUrlInput = document.getElementById('github-url');
        const localPathInput = document.getElementById('local-path');
        const fileInput = document.getElementById('file-input');
        const nameInput = document.getElementById('repo-name');
        
        if (!repoTypeSelect || !nameInput) return;
        
        const repoType = repoTypeSelect.value;
        let isValid = true;
        
        // Clear previous error messages
        document.querySelectorAll('.error-message').forEach(el => el.remove());
        
        // Validate repository name
        if (!nameInput.value.trim()) {
            showError(nameInput, 'Please enter a repository name');
            isValid = false;
        }
        
        // Validate based on repository type
        if (repoType === 'github') {
            // Validate GitHub URL
            if (!githubUrlInput.value.trim() || !githubUrlInput.value.includes('github.com')) {
                showError(githubUrlInput, 'Please enter a valid GitHub repository URL');
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
            if (!localPathInput.value.trim()) {
                showError(localPathInput, 'Please enter a valid local path');
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
    const githubInputGroup = document.getElementById('github-input-group');
    const githubBranchGroup = document.getElementById('github-branch-group');
    const fileInputGroup = document.getElementById('file-input-group');
    const localInputGroup = document.getElementById('local-input-group');
    
    if (!repoTypeSelect) return;
    
    // Show/hide appropriate input fields based on repository type
    repoTypeSelect.addEventListener('change', function() {
        const repoType = repoTypeSelect.value;
        
        // Hide all input groups first
        if (githubInputGroup) githubInputGroup.style.display = 'none';
        if (githubBranchGroup) githubBranchGroup.style.display = 'none';
        if (fileInputGroup) fileInputGroup.style.display = 'none';
        if (localInputGroup) localInputGroup.style.display = 'none';
        
        // Show appropriate input group based on type
        if (repoType === 'github') {
            if (githubInputGroup) githubInputGroup.style.display = 'block';
            if (githubBranchGroup) githubBranchGroup.style.display = 'block';
        } else if (repoType === 'zip') {
            if (fileInputGroup) fileInputGroup.style.display = 'block';
        } else if (repoType === 'local') {
            if (localInputGroup) localInputGroup.style.display = 'block';
        }
    });
    
    // Trigger change event on load to set initial state
    if (repoTypeSelect) {
        repoTypeSelect.dispatchEvent(new Event('change'));
    }
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
        
        // Show typing indicator
        showTypingIndicator();
        
        // Get repository ID from URL
        const repoId = window.location.pathname.split('/')[2];
        
        try {
            // Make API request - updated to use /api/chat endpoint
            const response = await fetch(`/api/chat/${repoId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    message: query, 
                    repo_id: repoId
                })
            });
            
            // Hide typing indicator
            hideTypingIndicator();
            
            if (!response.ok) {
                throw new Error(`Server responded with status: ${response.status}`);
            }
            
            const data = await response.json();
            
            // Check if response contains error message
            if (data.text && data.text.includes('Error generating text:')) {
                addMessage('system', 'Sorry, I encountered an error while processing your request. Please try again later.');
                console.error('Error in LLM response:', data.text);
                return;
            }
            
            // Add system response to chat
            addMessage('system', data.text || 'No response received');
            
            // If there's code in the response, add it
            if (data.code) {
                addCodeBlock(data.code);
            }
            
            // Add referenced files if any
            if (data.referenced_files && data.referenced_files.length > 0) {
                addReferencedFiles(data.referenced_files, repoId);
            }
        } catch (error) {
            // Hide typing indicator if it's still showing
            hideTypingIndicator();
            
            console.error('Error querying repository:', error);
            addMessage('system', 'Sorry, an error occurred while processing your query. Please try again later.');
        }
    });
}

/**
 * Show typing indicator in chat
 */
function showTypingIndicator() {
    const chatMessages = document.getElementById('chat-messages');
    if (!chatMessages) return;
    
    // Check if typing indicator already exists
    if (document.getElementById('typing-indicator')) return;
    
    const indicator = document.createElement('div');
    indicator.className = 'message system-message typing-indicator';
    indicator.id = 'typing-indicator';
    indicator.innerHTML = 'Thinking<span class="dot">.</span><span class="dot">.</span><span class="dot">.</span>';
    
    chatMessages.appendChild(indicator);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // Add animation
    const dots = indicator.querySelectorAll('.dot');
    dots.forEach((dot, index) => {
        dot.style.animation = `typingAnimation 1.4s infinite ${index * 0.2}s`;
    });
}

/**
 * Hide typing indicator in chat
 */
function hideTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) {
        indicator.remove();
    }
}

/**
 * Add a message to the chat interface
 */
function addMessage(type, text) {
    const chatMessages = document.getElementById('chat-messages');
    if (!chatMessages) return;
    
    // Check if there is a welcome message and remove it
    const welcomeMessage = document.querySelector('.welcome-message');
    if (welcomeMessage) {
        welcomeMessage.remove();
    }
    
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
    
    // Add copy button
    const copyBtn = document.createElement('button');
    copyBtn.className = 'copy-btn';
    copyBtn.textContent = 'Copy';
    copyBtn.onclick = function() {
        navigator.clipboard.writeText(code).then(function() {
            copyBtn.textContent = 'Copied!';
            setTimeout(function() {
                copyBtn.textContent = 'Copy';
            }, 2000);
        });
    };
    
    pre.appendChild(codeElement);
    codeDiv.appendChild(pre);
    codeDiv.appendChild(copyBtn);
    
    chatMessages.appendChild(codeDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

/**
 * Add referenced files to the chat interface
 */
function addReferencedFiles(files, repoId) {
    const chatMessages = document.getElementById('chat-messages');
    if (!chatMessages) return;
    
    const filesDiv = document.createElement('div');
    filesDiv.className = 'message system-message referenced-files';
    
    const heading = document.createElement('p');
    heading.textContent = 'Referenced Files:';
    filesDiv.appendChild(heading);
    
    const filesList = document.createElement('ul');
    files.forEach(file => {
        const listItem = document.createElement('li');
        const fileLink = document.createElement('a');
        
        // Handle both string and object formats
        const filePath = typeof file === 'string' ? file : (file.path || file.file_path || '');
        
        if (filePath) {
            fileLink.href = `/repos/${repoId}/file?path=${encodeURIComponent(filePath)}`;
            fileLink.textContent = filePath;
            listItem.appendChild(fileLink);
            filesList.appendChild(listItem);
        }
    });
    
    if (filesList.children.length > 0) {
        filesDiv.appendChild(filesList);
        chatMessages.appendChild(filesDiv);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
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

/**
 * Handle form submission with debugging
 */
function submitForm(event) {
    const form = document.getElementById('upload-form');
    if (!form) return false;
    
    const formData = new FormData(form);
    
    console.log("Form submission initiated");
    console.log("Form action:", form.action);
    console.log("Form method:", form.method);
    console.log("Form enctype:", form.enctype);
    
    // Log form data
    console.log("Form data:");
    for (let [key, value] of formData.entries()) {
        console.log(`${key}: ${value instanceof File ? `File: ${value.name}` : value}`);
    }
    
    // Make the fetch request manually
    fetch(form.action, {
        method: form.method,
        body: formData
    })
    .then(response => {
        console.log("Response status:", response.status);
        console.log("Response headers:", response.headers);
        
        if (!response.ok) {
            return response.json().then(errorData => {
                throw new Error(`Server error: ${errorData.detail || 'Unknown error'}`);
            });
        }
        return response.json();
    })
    .then(data => {
        console.log("Success response:", data);
        // Redirect to the repository page
        window.location.href = `/repos/${data.id}`;
    })
    .catch(error => {
        console.error("Error:", error);
        // Show error on page
        const formElement = document.getElementById('upload-form');
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.style.color = 'red';
        errorDiv.style.padding = '10px';
        errorDiv.style.marginBottom = '20px';
        errorDiv.style.backgroundColor = '#ffeeee';
        errorDiv.style.border = '1px solid #ff0000';
        errorDiv.style.borderRadius = '4px';
        errorDiv.textContent = `Error: ${error.message}`;
        
        formElement.prepend(errorDiv);
    });
    
    // Prevent regular form submission
    return false;
}

/**
 * Format dates or handle invalid dates gracefully
 */
function formatDate(dateString) {
    if (!dateString || dateString === 'Invalid Date' || dateString.includes('Unknown')) {
        return "Unknown date";
    }
    
    try {
        // Try parsing the date string - handle ISO format
        const date = new Date(dateString);
        
        // Check if the date is valid
        if (isNaN(date.getTime())) {
            return "Unknown date";
        }
        
        // Format the date using locale-specific formatting
        const options = { year: 'numeric', month: 'short', day: 'numeric' };
        return date.toLocaleDateString(undefined, options);
    } catch (e) {
        console.error('Error formatting date:', e, 'Original string:', dateString);
        return "Unknown date";
    }
}

/**
 * Handle potentially undefined or NaN values
 */
function formatSize(size) {
    if (size === undefined || size === null || isNaN(size)) {
        return "Unknown size";
    }
    
    if (size < 1024) {
        return `${size} bytes`;
    } else if (size < 1024 * 1024) {
        return `${(size / 1024).toFixed(1)} KB`;
    } else {
        return `${(size / (1024 * 1024)).toFixed(1)} MB`;
    }
}

/**
 * Load repository list from API
 */
async function loadRepositories() {
    const repoList = document.getElementById('repo-list');
    if (!repoList) return;
    
    // Show loading indicator
    repoList.innerHTML = '<div class="loading">Loading repositories...</div>';
    
    try {
        const response = await fetch('/api/repos');
        if (!response.ok) {
            throw new Error(`Error: ${response.status} ${response.statusText}`);
        }
        
        const repositories = await response.json();
        
        // Clear loading message
        repoList.innerHTML = '';
        
        if (!repositories || !Array.isArray(repositories) || repositories.length === 0) {
            // Show empty state
            repoList.innerHTML = '<div class="empty-message">No repositories found. <a href="/upload">Upload a repository</a> to get started.</div>';
            return;
        }
        
        // Create repository cards
        repositories.forEach(repo => {
            const card = document.createElement('div');
            card.className = 'repo-card';
            
            // Format date
            const createdDate = formatDate(repo.created_at);
            
            // Get status display
            const statusClass = repo.status === 'analyzed' ? 'status-ready' : 
                              repo.status === 'error' ? 'status-error' : 
                              'status-processing';
            
            const statusText = repo.status === 'analyzed' ? 'ready' : 
                              repo.status === 'error' ? 'error' : 
                              'processing';
            
            // Get correct repo ID
            const repoId = repo._id || repo.id;
            
            if (!repoId) {
                console.error('Repository missing ID:', repo);
                return;
            }
            
            // Get source type with fallback
            const sourceType = repo.source_type || repo.type || 'github';
            
            card.innerHTML = `
                <h3 class="repo-name">${repo.name || 'Unnamed Repository'}</h3>
                <div class="repo-meta">
                    <span class="source-type">${sourceType}</span>
                    <span class="date">${createdDate} • <span class="${statusClass}">${statusText}</span></span>
                </div>
                <div class="repo-actions">
                    <a href="/repos/${repoId}" class="btn btn-secondary">View Details</a>
                    <a href="/chat/${repoId}" class="btn btn-primary">Chat</a>
                </div>
            `;
            
            repoList.appendChild(card);
        });
        
        // Now format all dates in the repo cards
        formatDatesOnPage();
        
    } catch (error) {
        console.error('Error loading repositories:', error);
        repoList.innerHTML = `<div class="error">Failed to load repositories: ${error.message}</div>`;
    }
}

// Common error handler for fetch requests
function handleFetchError(response) {
    if (!response.ok) {
        throw new Error(`Error: ${response.status} ${response.statusText}`);
    }
    return response.json();
}

// Add CSS for typing indicator if not already in styles.css
function addTypingIndicatorStyles() {
    if (document.getElementById('typing-indicator-styles')) return;
    
    const style = document.createElement('style');
    style.id = 'typing-indicator-styles';
    style.textContent = `
        .typing-indicator {
            display: flex;
            align-items: center;
        }
        
        .typing-indicator .dot {
            display: inline-block;
            margin-left: 2px;
            animation: typingAnimation 1.4s infinite;
        }
        
        @keyframes typingAnimation {
            0%, 100% { opacity: 0.2; }
            50% { opacity: 1; }
        }
        
        .code-block {
            position: relative;
        }
        
        .code-block pre {
            background-color: #2d2d2d;
            color: #f8f8f2;
            padding: 1rem;
            border-radius: 4px;
            overflow-x: auto;
        }
        
        .code-block .copy-btn {
            position: absolute;
            top: 0.5rem;
            right: 0.5rem;
            background-color: rgba(255, 255, 255, 0.2);
            border: none;
            border-radius: 3px;
            padding: 0.25rem 0.5rem;
            color: white;
            cursor: pointer;
        }
        
        .welcome-message {
            background-color: #f8f9fa;
            border-left: 3px solid #007bff;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        
        .welcome-message h4 {
            margin-top: 0;
            color: #007bff;
        }
        
        .welcome-message ul {
            padding-left: 20px;
        }
        
        .welcome-message li {
            margin-bottom: 8px;
        }
    `;
    
    document.head.appendChild(style);
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Add typing indicator styles
    addTypingIndicatorStyles();
    
    // Load repositories if we're on the repos page
    if (document.getElementById('repo-list')) {
        loadRepositories();
    }
    
    // Apply file tree styles if we're on a page that needs them
    if (document.getElementById('file-structure')) {
        if (typeof addFileTreeStyles === 'function') {
            addFileTreeStyles();
        }
        
        // Get repository ID from hidden input
        const repoIdElement = document.getElementById('repository-id');
        if (repoIdElement && repoIdElement.value) {
            if (typeof loadRepositoryStructure === 'function') {
                loadRepositoryStructure(repoIdElement.value);
            }
            
            if (typeof loadKeyComponents === 'function') {
                loadKeyComponents();
            }
        }
    }
    
    // Format dates and sizes across the page
    formatDatesOnPage();
    formatSizesOnPage();
});