/**
 * StoryKeep Colorization Module
 * Handles AI-powered and traditional colorization features
 */

class ColorizationManager {
    constructor() {
        this.currentPhotoId = null;
        this.isProcessing = false;
        this.apiBase = '/api/colorization';
        this.csrfToken = this.getCSRFToken();
    }

    /**
     * Get CSRF token from meta tag
     */
    getCSRFToken() {
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        return metaTag ? metaTag.getAttribute('content') : '';
    }

    /**
     * Get headers with CSRF token
     */
    getHeaders() {
        return {
            'Content-Type': 'application/json',
            'X-CSRFToken': this.csrfToken
        };
    }

    /**
     * Initialize colorization features for a photo
     */
    init(photoId) {
        this.currentPhotoId = photoId;
        this.setupEventListeners();
        this.checkIfGrayscale();
    }

    /**
     * Set up event listeners for colorization buttons
     */
    setupEventListeners() {
        const colorizeBtn = document.getElementById('colorize-btn');
        const colorizeAiBtn = document.getElementById('colorize-ai-btn');
        const analyzeBtn = document.getElementById('analyze-enhancement-btn');
        
        if (colorizeBtn) {
            colorizeBtn.addEventListener('click', () => this.colorizePhoto('dnn'));
        }
        
        if (colorizeAiBtn) {
            colorizeAiBtn.addEventListener('click', () => this.colorizePhotoAI());
        }
        
        if (analyzeBtn) {
            analyzeBtn.addEventListener('click', () => this.analyzeEnhancement());
        }
    }

    /**
     * Check if the current photo is grayscale
     */
    async checkIfGrayscale() {
        if (!this.currentPhotoId) return;

        try {
            const response = await fetch(`${this.apiBase}/check-grayscale`, {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify({ photo_id: this.currentPhotoId })
            });

            const data = await response.json();
            
            if (data.success && data.is_grayscale) {
                this.enableColorizationOptions();
            } else {
                this.disableColorizationOptions();
            }
        } catch (error) {
            console.error('Error checking grayscale:', error);
            this.disableColorizationOptions();
        }
    }

    /**
     * Enable colorization options in the UI
     */
    enableColorizationOptions() {
        const colorizeBtn = document.getElementById('colorize-btn');
        const colorizeAiBtn = document.getElementById('colorize-ai-btn');
        const analyzeBtn = document.getElementById('analyze-enhancement-btn');
        const hints = document.querySelectorAll('.colorization-hint');
        
        if (colorizeBtn) colorizeBtn.disabled = false;
        if (colorizeAiBtn) colorizeAiBtn.disabled = false;
        if (analyzeBtn) analyzeBtn.disabled = false;
        
        hints.forEach(hint => {
            hint.innerHTML = '<i class="bi bi-check-circle"></i> Black & white photo detected - colorization enabled';
            hint.style.color = '#28a745';
        });
    }

    /**
     * Disable colorization options in the UI
     */
    disableColorizationOptions() {
        const colorizeBtn = document.getElementById('colorize-btn');
        const colorizeAiBtn = document.getElementById('colorize-ai-btn');
        const analyzeBtn = document.getElementById('analyze-enhancement-btn');
        const hints = document.querySelectorAll('.colorization-hint');
        
        if (colorizeBtn) colorizeBtn.disabled = true;
        if (colorizeAiBtn) colorizeAiBtn.disabled = true;
        if (analyzeBtn) analyzeBtn.disabled = true;
        
        hints.forEach(hint => {
            hint.innerHTML = '<i class="bi bi-info-circle"></i> Colorization is only available for black & white photos';
            hint.style.color = '#6c757d';
        });
    }

    /**
     * Colorize photo using traditional DNN method
     */
    async colorizePhoto(method = 'auto') {
        if (this.isProcessing) {
            this.showMessage('Another operation is in progress', 'warning');
            return;
        }

        this.isProcessing = true;
        this.showProgress('Colorizing photo...', 0);

        try {
            const response = await fetch(`${this.apiBase}/colorize`, {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify({
                    photo_id: this.currentPhotoId,
                    method: method
                })
            });

            const data = await response.json();

            if (data.success) {
                this.showMessage(`Photo colorized successfully using ${data.method}!`, 'success');
                this.updatePhotoDisplay(data.edited_url);
            } else {
                this.showMessage(`Error: ${data.error}`, 'error');
            }
        } catch (error) {
            console.error('Colorization error:', error);
            this.showMessage('Failed to colorize photo', 'error');
        } finally {
            this.isProcessing = false;
            this.hideProgress();
        }
    }

    /**
     * Colorize photo using AI
     */
    async colorizePhotoAI() {
        if (this.isProcessing) {
            this.showMessage('Another operation is in progress', 'warning');
            return;
        }

        this.isProcessing = true;
        this.showProgress('AI is analyzing and colorizing your photo...', 0);

        try {
            const response = await fetch(`${this.apiBase}/colorize-ai`, {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify({
                    photo_id: this.currentPhotoId
                })
            });

            const data = await response.json();

            if (response.status === 503) {
                this.showMessage('AI colorization requires OpenAI API key. Use the regular colorization button instead.', 'warning');
                return;
            }

            if (data.success) {
                this.showMessage('Photo AI-colorized successfully!', 'success');
                this.updatePhotoDisplay(data.edited_url);
                
                if (data.ai_guidance) {
                    this.showAIGuidance(data.ai_guidance);
                }
            } else {
                this.showMessage(`Error: ${data.error}`, 'error');
            }
        } catch (error) {
            console.error('AI colorization error:', error);
            this.showMessage('Failed to AI-colorize photo', 'error');
        } finally {
            this.isProcessing = false;
            this.hideProgress();
        }
    }

    /**
     * Analyze photo for enhancement suggestions
     */
    async analyzeEnhancement() {
        if (this.isProcessing) {
            this.showMessage('Another operation is in progress', 'warning');
            return;
        }

        this.isProcessing = true;
        this.showProgress('AI is analyzing your photo...', 0);

        try {
            const response = await fetch(`${this.apiBase}/enhance-analyze`, {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify({
                    photo_id: this.currentPhotoId
                })
            });

            const data = await response.json();

            if (response.status === 503) {
                this.showMessage('AI enhancement analysis requires OpenAI API key. This feature is currently unavailable.', 'warning');
                return;
            }

            if (data.success) {
                this.showEnhancementAnalysis(data.analysis);
            } else {
                this.showMessage(`Error: ${data.error}`, 'error');
            }
        } catch (error) {
            console.error('Enhancement analysis error:', error);
            this.showMessage('Failed to analyze photo', 'error');
        } finally {
            this.isProcessing = false;
            this.hideProgress();
        }
    }

    /**
     * Show AI guidance in a modal or panel
     */
    showAIGuidance(guidance) {
        const modal = document.getElementById('ai-guidance-modal');
        if (modal) {
            const content = modal.querySelector('.ai-guidance-content');
            if (content) {
                content.textContent = guidance;
            }
            const bsModal = new bootstrap.Modal(modal);
            bsModal.show();
        } else {
            alert('AI Guidance:\n\n' + guidance);
        }
    }

    /**
     * Show enhancement analysis results
     */
    showEnhancementAnalysis(analysis) {
        const modal = document.getElementById('enhancement-analysis-modal');
        if (modal) {
            const content = modal.querySelector('.analysis-content');
            if (content) {
                let html = '<h3>Enhancement Analysis</h3>';
                html += `<p><strong>Priority:</strong> ${analysis.priority}</p>`;
                
                if (analysis.issues && analysis.issues.length > 0) {
                    html += '<h4>Detected Issues:</h4><ul>';
                    analysis.issues.forEach(issue => {
                        html += `<li>${issue}</li>`;
                    });
                    html += '</ul>';
                }
                
                if (analysis.suggestions && analysis.suggestions.length > 0) {
                    html += '<h4>Suggestions:</h4><ul>';
                    analysis.suggestions.forEach(suggestion => {
                        html += `<li>${suggestion}</li>`;
                    });
                    html += '</ul>';
                }
                
                content.innerHTML = html;
            }
            const bsModal = new bootstrap.Modal(modal);
            bsModal.show();
        } else {
            let message = `Priority: ${analysis.priority}\n\n`;
            if (analysis.issues) {
                message += 'Issues:\n' + analysis.issues.join('\n') + '\n\n';
            }
            if (analysis.suggestions) {
                message += 'Suggestions:\n' + analysis.suggestions.join('\n');
            }
            alert(message);
        }
    }

    /**
     * Update the photo display with the new edited version
     */
    updatePhotoDisplay(editedUrl) {
        const photoImg = document.getElementById('photo-display');
        if (photoImg) {
            photoImg.src = editedUrl + '?t=' + new Date().getTime();
        }
        
        // Update colorized image display
        const colorizedImg = document.getElementById('colorizedImage');
        if (colorizedImg) {
            colorizedImg.src = editedUrl + '?t=' + new Date().getTime();
        }
        
        // Extract and display filename
        const filenameElement = document.getElementById('colorizedFilename');
        if (filenameElement && editedUrl) {
            const filename = editedUrl.split('/').pop();
            filenameElement.textContent = filename;
        }
        
        // Switch to colorized view
        const colorizedViewBtn = document.querySelector('[data-view="colorized"]');
        if (colorizedViewBtn) {
            colorizedViewBtn.click();
        }
    }

    /**
     * Show progress indicator
     */
    showProgress(message, progress) {
        const progressContainer = document.getElementById('colorization-progress');
        if (progressContainer) {
            progressContainer.style.display = 'block';
            const messageEl = progressContainer.querySelector('.progress-message');
            if (messageEl) {
                messageEl.textContent = message;
            }
        }
    }

    /**
     * Hide progress indicator
     */
    hideProgress() {
        const progressContainer = document.getElementById('colorization-progress');
        if (progressContainer) {
            progressContainer.style.display = 'none';
        }
    }

    /**
     * Show message to user
     */
    showMessage(message, type = 'info') {
        const messageDiv = document.createElement('div');
        messageDiv.className = `alert alert-${type} colorization-message`;
        messageDiv.textContent = message;
        messageDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 5px;
            background-color: ${type === 'success' ? '#d4edda' : type === 'error' ? '#f8d7da' : '#fff3cd'};
            color: ${type === 'success' ? '#155724' : type === 'error' ? '#721c24' : '#856404'};
            border: 1px solid ${type === 'success' ? '#c3e6cb' : type === 'error' ? '#f5c6cb' : '#ffeaa7'};
            z-index: 10000;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        `;

        document.body.appendChild(messageDiv);

        setTimeout(() => {
            messageDiv.style.transition = 'opacity 0.5s';
            messageDiv.style.opacity = '0';
            setTimeout(() => messageDiv.remove(), 500);
        }, 5000);
    }
}

// Export for global use
window.ColorizationManager = ColorizationManager;

// Auto-initialize if photo ID is present
document.addEventListener('DOMContentLoaded', () => {
    const photoIdElement = document.getElementById('current-photo-id');
    if (photoIdElement) {
        const photoId = parseInt(photoIdElement.value || photoIdElement.dataset.photoId);
        if (photoId) {
            const colorizationManager = new ColorizationManager();
            colorizationManager.init(photoId);
            window.colorizationManager = colorizationManager;
        }
    }
});
