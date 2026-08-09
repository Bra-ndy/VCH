// Main Application JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Auto-dismiss alerts after 5 seconds
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // CSRF token for AJAX requests
    const csrfToken = document.querySelector('meta[name="csrf-token"]');
    if (csrfToken) {
        window.csrfToken = csrfToken.getAttribute('content');
    }

    // Handle form submissions with validation
    const forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
            }
        });
    });

    // Phone number formatting
    const phoneInputs = document.querySelectorAll('input[type="tel"], input[name*="phone"]');
    phoneInputs.forEach(function(input) {
        input.addEventListener('input', function(e) {
            let value = this.value.replace(/\D/g, '');
            if (value.length > 0 && !value.startsWith('254')) {
                value = '254' + value;
            }
            this.value = value;
        });
    });

    // Number input formatting for amounts
    const amountInputs = document.querySelectorAll('input[name*="amount"], input[name*="price"]');
    amountInputs.forEach(function(input) {
        input.addEventListener('input', function(e) {
            let value = this.value.replace(/[^0-9.]/g, '');
            const parts = value.split('.');
            if (parts.length > 2) {
                value = parts[0] + '.' + parts.slice(1).join('');
            }
            this.value = value;
        });
    });

    // Copy to clipboard functionality
    document.querySelectorAll('[data-copy]').forEach(function(element) {
        element.addEventListener('click', function(e) {
            const text = this.getAttribute('data-copy');
            navigator.clipboard.writeText(text).then(function() {
                const originalText = element.innerHTML;
                element.innerHTML = '<i class="fas fa-check"></i> Copied!';
                setTimeout(function() {
                    element.innerHTML = originalText;
                }, 2000);
            }).catch(function() {
                // Fallback
                const textarea = document.createElement('textarea');
                textarea.value = text;
                document.body.appendChild(textarea);
                textarea.select();
                document.execCommand('copy');
                document.body.removeChild(textarea);
                
                const originalText = element.innerHTML;
                element.innerHTML = '<i class="fas fa-check"></i> Copied!';
                setTimeout(function() {
                    element.innerHTML = originalText;
                }, 2000);
            });
        });
    });

    // Live activity refresh
    if (document.getElementById('live-activity')) {
        setInterval(function() {
            fetch('/api/live-activity')
                .then(response => response.json())
                .then(data => {
                    const container = document.getElementById('live-activity');
                    if (container) {
                        container.innerHTML = data.html;
                    }
                })
                .catch(error => console.error('Error fetching live activity:', error));
        }, 30000); // Refresh every 30 seconds
    }

    console.log('VCH Platform loaded successfully');
});

// Utility functions
function formatCurrency(amount) {
    return 'KSH ' + parseFloat(amount).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-KE', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function getStatusColor(status) {
    const colors = {
        'pending': 'warning',
        'active': 'success',
        'completed': 'info',
        'cancelled': 'danger',
        'failed': 'danger'
    };
    return colors[status] || 'secondary';
}