// Intersection Observer options
const observerOptions = {
    root: null,
    rootMargin: '0px',
    threshold: 0.1
};

// Animation handler
const animateOnScroll = (entries, observer) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            // Handle activities section
            if (entry.target.classList.contains('activities-section')) {
                const activityBoxes = entry.target.querySelectorAll('.activity-box');
                activityBoxes.forEach((box, index) => {
                    setTimeout(() => {
                        box.classList.add('animate');
                    }, index * 150); // Stagger each box animation
                });
            }
            
            // Handle timeline events separately
            if (entry.target.classList.contains('upcoming-events')) {
                const timelineEvents = entry.target.querySelectorAll('.timeline-event');
                timelineEvents.forEach((event, index) => {
                    setTimeout(() => {
                        event.style.opacity = '1';
                        event.style.transform = 'translateY(0)';
                    }, index * 200);
                });
            }
            
            // Handle other animated elements
            entry.target.classList.add('animate');
            observer.unobserve(entry.target);
        }
    });
};

// Create observer
const observer = new IntersectionObserver(animateOnScroll, observerOptions);

// Initialize animations
const initializeAnimations = () => {
    // Initialize activity boxes
    const activityBoxes = document.querySelectorAll('.activity-box');
    activityBoxes.forEach(box => {
        box.style.opacity = '0';
        box.style.transform = 'translateY(30px)';
        box.style.transition = 'all 0.6s cubic-bezier(0.4, 0, 0.2, 1)';
    });

    // Initialize timeline events
    const timelineEvents = document.querySelectorAll('.timeline-event');
    timelineEvents.forEach(event => {
        event.style.opacity = '0';
        event.style.transform = 'translateY(30px)';
        event.style.transition = 'all 0.6s cubic-bezier(0.4, 0, 0.2, 1)';
    });

    // Initialize other animated sections
    const sections = document.querySelectorAll('.animate-on-scroll');
    sections.forEach(section => {
        observer.observe(section);
    });
};

// Run on page load
document.addEventListener('DOMContentLoaded', () => {
    // Short delay to ensure DOM is fully loaded
    setTimeout(initializeAnimations, 100);
});

// Handle visibility changes
document.addEventListener('visibilitychange', () => {
    if (!document.hidden) {
        initializeAnimations();
    }
}); 