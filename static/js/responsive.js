// static/js/responsive.js - Responsive helper functions

document.addEventListener('DOMContentLoaded', function() {
    // Handle responsive elements
    handleResponsiveElements();
    
    // Handle window resize
    let resizeTimeout;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(function() {
            handleResponsiveElements();
        }, 250);
    });
});

function handleResponsiveElements() {
    const width = window.innerWidth;
    
    // Handle tables on mobile
    if (width < 768) {
        document.querySelectorAll('.table-responsive').forEach(function(table) {
            table.style.overflowX = 'auto';
        });
    }
    
    // Handle quick actions on mobile
    if (width < 576) {
        document.querySelectorAll('.quick-action').forEach(function(el) {
            el.style.padding = '0.5rem';
            el.querySelector('i').style.fontSize = '1.2rem';
            if (el.querySelector('span')) {
                el.querySelector('span').style.fontSize = '0.7rem';
            }
        });
    }
    
    // Handle stat cards on mobile
    if (width < 576) {
        document.querySelectorAll('.stat-card').forEach(function(el) {
            const number = el.querySelector('.number');
            if (number) {
                number.style.fontSize = '1.2rem';
            }
            const label = el.querySelector('.label');
            if (label) {
                label.style.fontSize = '0.7rem';
            }
        });
    }
    
    // Handle vehicle cards on mobile
    if (width < 576) {
        document.querySelectorAll('.vehicle-card .vehicle-image').forEach(function(el) {
            el.style.height = '80px';
        });
    } else if (width < 768) {
        document.querySelectorAll('.vehicle-card .vehicle-image').forEach(function(el) {
            el.style.height = '100px';
        });
    } else {
        document.querySelectorAll('.vehicle-card .vehicle-image').forEach(function(el) {
            el.style.height = '150px';
        });
    }
}

// Device detection
function isMobile() {
    return window.innerWidth <= 768;
}

function isTablet() {
    return window.innerWidth > 768 && window.innerWidth <= 992;
}

function isDesktop() {
    return window.innerWidth > 992;
}

// Touch detection
function isTouchDevice() {
    return ('ontouchstart' in window) || (navigator.maxTouchPoints > 0);
}

// Export for use in other scripts
window.responsive = {
    isMobile: isMobile,
    isTablet: isTablet,
    isDesktop: isDesktop,
    isTouchDevice: isTouchDevice
};