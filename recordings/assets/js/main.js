// mtop Demo Landing Page JavaScript

// DOM Elements
const demoCards = document.querySelectorAll('.demo-card');
const modal = document.getElementById('demo-modal');
const modalTitle = document.getElementById('modal-title');
const modalClose = document.querySelector('.modal-close');
const demoVideo = document.getElementById('demo-video');
const videoSource = document.getElementById('video-source');
const formatButtons = document.querySelectorAll('.format-btn');
const roiForm = document.getElementById('demo-request-form');

// Demo data
const demoData = {
    'cost-optimization': {
        title: 'Cost Optimization - 40% GPU Cost Reduction',
        videos: {
            mp4: 'sales/cost-optimization.mp4',
            webm: 'sales/cost-optimization.webm',
            gif: 'sales/cost-optimization.gif'
        }
    },
    'slo-compliance': {
        title: 'SLO Compliance - Sub-500ms TTFT Guarantee',
        videos: {
            mp4: 'sales/slo-compliance.mp4',
            webm: 'sales/slo-compliance.webm',
            gif: 'sales/slo-compliance.gif'
        }
    },
    'gpu-efficiency': {
        title: 'GPU Efficiency - 3x Model Density',
        videos: {
            mp4: 'sales/gpu-efficiency.mp4',
            webm: 'sales/gpu-efficiency.webm',
            gif: 'sales/gpu-efficiency.gif'
        }
    },
    'load-handling': {
        title: 'Load Handling - Auto-scaling for Traffic Spikes',
        videos: {
            mp4: 'sales/load-handling.mp4',
            webm: 'sales/load-handling.webm',
            gif: 'sales/load-handling.gif'
        }
    },
    'multi-model': {
        title: 'Multi-Model - Unified LLM Portfolio Monitoring',
        videos: {
            mp4: 'sales/multi-model.mp4',
            webm: 'sales/multi-model.webm',
            gif: 'sales/multi-model.gif'
        }
    }
};

// GPU pricing data
const gpuPricing = {
    h100: { cost: 4.10, name: 'NVIDIA H100' },
    a100: { cost: 3.20, name: 'NVIDIA A100' },
    v100: { cost: 2.50, name: 'NVIDIA V100' }
};

// ROI calculation variables
let savingsChart = null;

// Initialize the page
document.addEventListener('DOMContentLoaded', function() {
    initializeDemoCards();
    initializeModal();
    initializeROICalculator();
    initializeContactForm();
    initializeSmoothScrolling();
    updateUtilizationDisplay();
    calculateROI(); // Initial calculation
});

// Demo card interactions
function initializeDemoCards() {
    demoCards.forEach(card => {
        card.addEventListener('click', function() {
            const demoType = this.dataset.demo;
            openDemoModal(demoType);
        });
    });
}

// Modal functionality
function initializeModal() {
    modalClose.addEventListener('click', closeDemoModal);
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            closeDemoModal();
        }
    });

    // Format button listeners
    formatButtons.forEach(button => {
        button.addEventListener('click', function() {
            const format = this.dataset.format;
            const currentDemo = modal.dataset.currentDemo;
            switchVideoFormat(currentDemo, format);
            
            // Update active button
            formatButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
        });
    });

    // Keyboard navigation
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && modal.style.display === 'block') {
            closeDemoModal();
        }
    });
}

function openDemoModal(demoType) {
    const demo = demoData[demoType];
    if (!demo) return;

    modalTitle.textContent = demo.title;
    modal.dataset.currentDemo = demoType;
    
    // Set initial video (MP4)
    switchVideoFormat(demoType, 'mp4');
    
    // Show modal
    modal.style.display = 'block';
    document.body.style.overflow = 'hidden';
    
    // Reset format buttons
    formatButtons.forEach(btn => btn.classList.remove('active'));
    document.querySelector('[data-format="mp4"]').classList.add('active');
}

function closeDemoModal() {
    modal.style.display = 'none';
    document.body.style.overflow = 'auto';
    demoVideo.pause();
}

function switchVideoFormat(demoType, format) {
    const demo = demoData[demoType];
    if (!demo || !demo.videos[format]) return;

    const videoUrl = demo.videos[format];
    
    if (format === 'gif') {
        // For GIF, replace video with img element
        const videoContainer = document.querySelector('.video-container');
        videoContainer.innerHTML = `<img src="${videoUrl}" alt="${demo.title}" style="width: 100%; border-radius: 8px;">`;
    } else {
        // For video formats, restore video element if needed
        const videoContainer = document.querySelector('.video-container');
        if (!videoContainer.querySelector('video')) {
            videoContainer.innerHTML = `
                <video id="demo-video" controls preload="metadata">
                    <source id="video-source" src="" type="video/mp4">
                    Your browser does not support the video tag.
                </video>
            `;
        }
        
        const video = videoContainer.querySelector('video');
        const source = videoContainer.querySelector('source');
        
        source.src = videoUrl;
        source.type = format === 'webm' ? 'video/webm' : 'video/mp4';
        video.load();
    }
}

// ROI Calculator
function initializeROICalculator() {
    const inputs = ['model-count', 'gpu-type', 'utilization', 'monthly-cost'];
    
    inputs.forEach(inputId => {
        const element = document.getElementById(inputId);
        if (element) {
            element.addEventListener('change', calculateROI);
            element.addEventListener('input', function() {
                if (inputId === 'utilization') {
                    updateUtilizationDisplay();
                }
                calculateROI();
            });
        }
    });
}

function updateUtilizationDisplay() {
    const utilizationSlider = document.getElementById('utilization');
    const rangeValue = document.querySelector('.range-value');
    if (utilizationSlider && rangeValue) {
        rangeValue.textContent = utilizationSlider.value + '%';
    }
}

function calculateROI() {
    try {
        // Get input values
        const modelCount = parseInt(document.getElementById('model-count').value) || 10;
        const gpuType = document.getElementById('gpu-type').value || 'h100';
        const utilization = parseInt(document.getElementById('utilization').value) || 60;
        const monthlyCost = parseInt(document.getElementById('monthly-cost').value) || 50000;

        // Calculate savings based on mtop optimizations
        const costSavings = calculateCostSavings(modelCount, gpuType, utilization, monthlyCost);
        const efficiencyGain = calculateEfficiencyGain(utilization);
        const annualROI = costSavings * 12;
        
        // Update display
        document.getElementById('cost-savings').textContent = `$${costSavings.toLocaleString()}`;
        document.getElementById('efficiency-gain').textContent = `${efficiencyGain}%`;
        document.getElementById('annual-roi').textContent = `$${annualROI.toLocaleString()}`;
        document.getElementById('model-density').textContent = '3x';

        // Update breakdown
        const rightsizingSavings = Math.round(costSavings * 0.6);
        const utilizationSavings = Math.round(costSavings * 0.25);
        const scalingSavings = Math.round(costSavings * 0.15);

        document.getElementById('rightsizing-savings').textContent = `$${rightsizingSavings.toLocaleString()}/month`;
        document.getElementById('utilization-savings').textContent = `$${utilizationSavings.toLocaleString()}/month`;
        document.getElementById('scaling-savings').textContent = `$${scalingSavings.toLocaleString()}/month`;

        // Update chart
        updateSavingsChart(costSavings, rightsizingSavings, utilizationSavings, scalingSavings);

    } catch (error) {
        console.error('Error calculating ROI:', error);
    }
}

function calculateCostSavings(modelCount, gpuType, utilization, monthlyCost) {
    // Base savings calculations based on mtop capabilities
    let savingsMultiplier = 0.4; // 40% base savings
    
    // Adjust based on current utilization (lower utilization = more savings potential)
    if (utilization < 50) {
        savingsMultiplier += 0.1; // Additional 10% for low utilization
    } else if (utilization > 80) {
        savingsMultiplier -= 0.05; // Reduce savings for already high utilization
    }
    
    // Adjust based on GPU type (H100 has more optimization potential)
    if (gpuType === 'h100') {
        savingsMultiplier += 0.05;
    }
    
    // Scale savings with model count (more models = more optimization opportunities)
    const modelMultiplier = Math.min(1 + (modelCount - 1) * 0.02, 1.5); // Max 50% bonus
    
    return Math.round(monthlyCost * savingsMultiplier * modelMultiplier);
}

function calculateEfficiencyGain(utilization) {
    // Efficiency gain based on current utilization
    const targetUtilization = 85; // mtop target
    const currentGap = targetUtilization - utilization;
    return Math.max(20, Math.min(60, Math.round(currentGap * 0.8 + 20)));
}

function updateSavingsChart(totalSavings, rightsizing, utilizationOpt, scaling) {
    const ctx = document.getElementById('savingsChart');
    if (!ctx) return;

    // Destroy existing chart
    if (savingsChart) {
        savingsChart.destroy();
    }

    savingsChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['GPU Rightsizing', 'Utilization Optimization', 'Auto-scaling Efficiency'],
            datasets: [{
                data: [rightsizing, utilizationOpt, scaling],
                backgroundColor: [
                    'rgba(59, 130, 246, 0.8)',
                    'rgba(139, 92, 246, 0.8)',
                    'rgba(16, 185, 129, 0.8)'
                ],
                borderColor: [
                    'rgba(59, 130, 246, 1)',
                    'rgba(139, 92, 246, 1)',
                    'rgba(16, 185, 129, 1)'
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#cbd5e1',
                        padding: 20,
                        font: {
                            size: 12
                        }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(30, 41, 59, 0.95)',
                    titleColor: '#f8fafc',
                    bodyColor: '#cbd5e1',
                    borderColor: 'rgba(100, 116, 139, 0.3)',
                    borderWidth: 1,
                    callbacks: {
                        label: function(context) {
                            return context.label + ': $' + context.parsed.toLocaleString() + '/month';
                        }
                    }
                }
            }
        }
    });
}

// Contact form handling
function initializeContactForm() {
    if (roiForm) {
        roiForm.addEventListener('submit', handleFormSubmission);
    }
}

function handleFormSubmission(e) {
    e.preventDefault();
    
    // Get form data
    const formData = new FormData(roiForm);
    const data = Object.fromEntries(formData);
    
    // Simple validation
    if (!data.name || !data.email || !data.company) {
        alert('Please fill in all required fields.');
        return;
    }
    
    if (!isValidEmail(data.email)) {
        alert('Please enter a valid email address.');
        return;
    }
    
    // Simulate form submission
    const submitButton = roiForm.querySelector('button[type="submit"]');
    const originalText = submitButton.textContent;
    
    submitButton.textContent = 'Scheduling...';
    submitButton.disabled = true;
    
    setTimeout(() => {
        alert('Thank you! We\'ll contact you within 24 hours to schedule your personalized demo.');
        roiForm.reset();
        submitButton.textContent = originalText;
        submitButton.disabled = false;
    }, 2000);
}

function isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

// Smooth scrolling for navigation links
function initializeSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                const headerHeight = 80; // Account for fixed header
                const targetPosition = target.offsetTop - headerHeight;
                
                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });
}

// Header background on scroll
window.addEventListener('scroll', function() {
    const header = document.querySelector('.header');
    if (window.scrollY > 50) {
        header.style.background = 'rgba(15, 23, 42, 0.95)';
    } else {
        header.style.background = 'rgba(15, 23, 42, 0.9)';
    }
});

// Intersection Observer for animations
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver(function(entries) {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

// Observe elements for animation
document.addEventListener('DOMContentLoaded', function() {
    const animatedElements = document.querySelectorAll('.demo-card, .result-card, .benefit');
    animatedElements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });
});

// Utility functions
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(amount);
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

// Performance monitoring
if ('performance' in window) {
    window.addEventListener('load', function() {
        setTimeout(function() {
            const perfData = performance.getEntriesByType('navigation')[0];
            console.log('Page load time:', perfData.loadEventEnd - perfData.loadEventStart, 'ms');
        }, 0);
    });
}