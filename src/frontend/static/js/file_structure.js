/**
 * Repository file structure utilities
 */

// Load repository structure
async function loadRepositoryStructure(repoId, containerId = 'file-structure') {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    container.innerHTML = '<p class="loading">Loading repository structure...</p>';
    
    try {
        const response = await fetch(`/api/repos/${repoId}/structure`);
        if (!response.ok) {
            throw new Error(`Failed to load structure: ${response.status}`);
        }
        
        const data = await response.json();
        if (!data || !data.children) {
            container.innerHTML = '<p class="error">Repository structure is empty or invalid.</p>';
            return;
        }
        
        // Create file structure tree
        container.innerHTML = '';
        const tree = createFileTree(data, repoId);
        container.appendChild(tree);
        
        // Add toggle functionality for directories
        addDirectoryToggle();
    } catch (error) {
        console.error('Error loading repository structure:', error);
        container.innerHTML = '<p class="error">Failed to load file structure. Please try again later.</p>';
    }
}

// Create file structure tree
function createFileTree(node, repoId) {
    const treeElement = document.createElement('div');
    treeElement.className = 'file-tree';
    
    const rootList = document.createElement('ul');
    rootList.className = 'file-tree-root';
    
    // Process children
    if (node.children && node.children.length > 0) {
        // Sort directories first, then files
        const sortedChildren = [...node.children].sort((a, b) => {
            if (a.type === b.type) {
                return a.name.localeCompare(b.name);
            }
            return a.type === 'directory' ? -1 : 1;
        });
        
        sortedChildren.forEach(child => {
            const item = createFileTreeItem(child, node.path, repoId);
            rootList.appendChild(item);
        });
    } else {
        const emptyItem = document.createElement('li');
        emptyItem.className = 'file-tree-empty';
        emptyItem.textContent = 'No files found.';
        rootList.appendChild(emptyItem);
    }
    
    treeElement.appendChild(rootList);
    return treeElement;
}

// Create a file tree item (file or directory)
function createFileTreeItem(node, parentPath, repoId) {
    if (!node || !node.type) {
        console.error('Invalid node data:', node);
        return document.createElement('li'); // Return empty element
    }
    
    const item = document.createElement('li');
    item.className = `file-tree-item file-tree-${node.type}`;
    
    const icon = document.createElement('span');
    icon.className = 'file-tree-icon';
    icon.innerHTML = node.type === 'directory' ? '📁' : getFileIcon(node.path || '');
    
    const label = document.createElement('span');
    label.className = 'file-tree-label';
    
    if (node.type === 'directory') {
        label.textContent = node.name || 'Unknown';
        label.className += ' directory-label';
        
        item.appendChild(icon);
        item.appendChild(label);
        
        // Create children container
        if (node.children && node.children.length > 0) {
            const childrenList = document.createElement('ul');
            childrenList.className = 'file-tree-children';
            
            // Sort directories first, then files
            const sortedChildren = [...node.children].sort((a, b) => {
                if (a.type === b.type) {
                    return a.name.localeCompare(b.name);
                }
                return a.type === 'directory' ? -1 : 1;
            });
            
            sortedChildren.forEach(child => {
                const childItem = createFileTreeItem(child, node.path || '', repoId);
                childrenList.appendChild(childItem);
            });
            
            item.appendChild(childrenList);
        }
    } else {
        // Create a link for files
        const link = document.createElement('a');
        if (repoId && node.path) {
            link.href = `/repos/${repoId}/file?path=${encodeURIComponent(node.path)}`;
        } else {
            link.href = '#';
        }
        link.textContent = node.name || 'Unknown';
        
        label.appendChild(link);
        
        item.appendChild(icon);
        item.appendChild(label);
    }
    
    return item;
}

// Get file icon based on file type
function getFileIcon(path) {
    if (!path) return '📄';
    
    const extension = path.split('.').pop().toLowerCase();
    
    const iconMap = {
        'js': '📄 [JS]',
        'py': '📄 [PY]',
        'java': '📄 [JAVA]',
        'html': '📄 [HTML]',
        'css': '📄 [CSS]',
        'json': '📄 [JSON]',
        'md': '📄 [MD]',
        'txt': '📄 [TXT]',
        'git': '📄 [GIT]'
    };
    
    return iconMap[extension] || '📄';
}

// Add toggle functionality for directories
function addDirectoryToggle() {
    try {
        const directoryLabels = document.querySelectorAll('.directory-label');
        
        if (!directoryLabels || directoryLabels.length === 0) {
            console.log('No directory labels found');
            return;
        }
        
        directoryLabels.forEach(label => {
            if (label) {
                label.addEventListener('click', function() {
                    const parent = this.parentElement;
                    if (parent) {
                        parent.classList.toggle('collapsed');
                    }
                });
            }
        });
    } catch (error) {
        console.error('Error setting up directory toggle:', error);
    }
}

// Add CSS styles for file tree
function addFileTreeStyles() {
    const style = document.createElement('style');
    style.textContent = `
        .file-tree {
            font-family: monospace;
            margin: 1rem 0;
        }
        
        .file-tree ul {
            list-style-type: none;
            padding-left: 1.5rem;
        }
        
        .file-tree-root {
            padding-left: 0.5rem;
        }
        
        .file-tree-item {
            margin: 0.2rem 0;
            white-space: nowrap;
        }
        
        .file-tree-directory > .file-tree-children {
            max-height: 1000px;
            overflow: hidden;
            transition: max-height 0.3s ease-out;
        }
        
        .file-tree-directory.collapsed > .file-tree-children {
            max-height: 0;
        }
        
        .file-tree-icon {
            margin-right: 0.5rem;
        }
        
        .directory-label {
            cursor: pointer;
            font-weight: bold;
        }
        
        .directory-label:hover {
            color: #4a6cf7;
        }
        
        .file-tree-file .file-tree-label a {
            text-decoration: none;
            color: inherit;
        }
        
        .file-tree-file .file-tree-label a:hover {
            text-decoration: underline;
            color: #4a6cf7;
        }
        
        .loading, .error {
            padding: 1rem;
            border-radius: 4px;
        }
        
        .loading {
            background-color: #f8f9fa;
            color: #495057;
        }
        
        .error {
            background-color: #f8d7da;
            color: #721c24;
        }
    `;
    
    document.head.appendChild(style);
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    addFileTreeStyles();
    
    // Auto-load repository structure if on repo details page
    const repoIdElement = document.getElementById('repository-id');
    if (repoIdElement) {
        const repoId = repoIdElement.value;
        if (repoId) {
            loadRepositoryStructure(repoId);
        }
    }
}); 