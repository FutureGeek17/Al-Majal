// Loading Screen
document.addEventListener('DOMContentLoaded', () => {
    const loadingScreen = document.querySelector('.loading-screen');
    
    // Hide loading screen when page is fully loaded
    window.addEventListener('load', () => {
        setTimeout(() => {
            loadingScreen.classList.add('fade-out');
        }, 500); // Short delay to ensure smooth animation
    });

    // Show loading screen before page unload
    window.addEventListener('beforeunload', () => {
        loadingScreen.classList.remove('fade-out');
    });
});

// Scroll Animation for Booking Info Section
document.addEventListener('DOMContentLoaded', () => {
    const bookingSection = document.querySelector('.booking-info');
    const infoCards = document.querySelectorAll('.info-card');
    const ctaSection = document.querySelector('.cta-section');
    
    // Set initial card indices for staggered animation
    infoCards.forEach((card, index) => {
        card.style.setProperty('--card-index', index);
    });

    // Create an Intersection Observer for the booking section
    const bookingObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // Add animation class to all cards when section is visible
                infoCards.forEach(card => {
                    card.style.visibility = 'visible';
                });
                bookingObserver.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.2,
        rootMargin: '50px'
    });

    // Create an Intersection Observer for the CTA section
    const ctaObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                ctaObserver.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.2,
        rootMargin: '50px'
    });

    // Observe the booking section
    if (bookingSection) {
        bookingObserver.observe(bookingSection);
    }

    // Observe the CTA section
    if (ctaSection) {
        ctaObserver.observe(ctaSection);
    }

    // Add hover animations for info cards
    infoCards.forEach(card => {
        const icon = card.querySelector('i');
        
        card.addEventListener('mouseenter', () => {
            icon.style.transform = 'scale(1.1) rotate(5deg)';
        });
        
        card.addEventListener('mouseleave', () => {
            icon.style.transform = 'scale(1) rotate(0deg)';
        });
    });

    // Add ripple effect to CTA buttons
    const ctaButtons = document.querySelectorAll('.cta-btn');
    
    ctaButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const rect = this.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            const ripple = document.createElement('span');
            ripple.classList.add('btn-ripple');
            ripple.style.left = `${x}px`;
            ripple.style.top = `${y}px`;
            
            this.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 800);
        });
    });
});

// Hero Section Slider
document.addEventListener('DOMContentLoaded', () => {
    const slides = document.querySelectorAll('.slide');
    const sliderDots = document.querySelector('.slider-dots');
    let currentSlide = 0;
    let slideInterval;

    // Create dots for each slide
    if (slides.length > 0 && sliderDots) {
        slides.forEach((_, index) => {
            const dot = document.createElement('div');
            dot.classList.add('dot');
            if (index === 0) dot.classList.add('active');
            dot.addEventListener('click', () => goToSlide(index));
            sliderDots.appendChild(dot);
        });
    }

    function updateDots() {
        const dots = document.querySelectorAll('.dot');
        dots.forEach((dot, index) => {
            dot.classList.toggle('active', index === currentSlide);
        });
    }

    function goToSlide(index) {
        slides.forEach(slide => slide.classList.remove('active'));
        slides[index].classList.add('active');
        currentSlide = index;
        updateDots();
        resetSlideInterval();
    }

    function nextSlide() {
        goToSlide((currentSlide + 1) % slides.length);
    }

    function prevSlide() {
        goToSlide((currentSlide - 1 + slides.length) % slides.length);
    }

    function resetSlideInterval() {
        clearInterval(slideInterval);
        slideInterval = setInterval(nextSlide, 5000);
    }

    // Initialize slider
    if (slides.length > 0) {
        // Add click events for navigation buttons
        const prevBtn = document.querySelector('.slider-nav.prev');
        const nextBtn = document.querySelector('.slider-nav.next');

        if (prevBtn) prevBtn.addEventListener('click', (e) => {
            e.preventDefault();
            prevSlide();
        });

        if (nextBtn) nextBtn.addEventListener('click', (e) => {
            e.preventDefault();
            nextSlide();
        });

        // Start automatic sliding
        resetSlideInterval();

        // Pause slider on hover
        const heroSection = document.querySelector('.hero-section');
        if (heroSection) {
            heroSection.addEventListener('mouseenter', () => {
                clearInterval(slideInterval);
            });

            heroSection.addEventListener('mouseleave', () => {
                resetSlideInterval();
            });
        }

        // Handle keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowLeft') prevSlide();
            if (e.key === 'ArrowRight') nextSlide();
        });

        // Handle touch events
        let touchStartX = 0;
        let touchEndX = 0;

        heroSection?.addEventListener('touchstart', (e) => {
            touchStartX = e.changedTouches[0].screenX;
        }, { passive: true });

        heroSection?.addEventListener('touchend', (e) => {
            touchEndX = e.changedTouches[0].screenX;
            if (touchEndX < touchStartX) nextSlide(); // Swipe left
            if (touchEndX > touchStartX) prevSlide(); // Swipe right
        }, { passive: true });
    }
});

// Mobile Menu Toggle
document.addEventListener('DOMContentLoaded', () => {
    const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
    const navLinks = document.querySelector('.nav-links');
    const dropdowns = document.querySelectorAll('.dropdown');

    // Mobile menu toggle
    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener('click', () => {
            navLinks.classList.toggle('active');
            mobileMenuBtn.classList.toggle('active');
            document.body.style.overflow = navLinks.classList.contains('active') ? 'hidden' : '';
        });
    }

    // Handle dropdowns on mobile
    dropdowns.forEach(dropdown => {
        const link = dropdown.querySelector('a');
        
        if (window.innerWidth <= 1024) {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                dropdown.classList.toggle('active');
                
                // Close other dropdowns
                dropdowns.forEach(other => {
                    if (other !== dropdown) {
                        other.classList.remove('active');
                    }
                });
            });
        }
    });

    // Close mobile menu when clicking outside
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.nav-links') && !e.target.closest('.mobile-menu-btn')) {
            navLinks?.classList.remove('active');
            mobileMenuBtn?.classList.remove('active');
            document.body.style.overflow = '';
            
            // Close all dropdowns
            dropdowns.forEach(dropdown => {
                dropdown.classList.remove('active');
            });
        }
    });

    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (href !== '#') {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                    // Close mobile menu after clicking a link
                    navLinks?.classList.remove('active');
                    mobileMenuBtn?.classList.remove('active');
                    document.body.style.overflow = '';
                }
            }
        });
    });

    // Activities Section Animations
    const activityBoxes = document.querySelectorAll('.activity-box');
    
    const activityObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
                activityObserver.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.2,
        rootMargin: '50px'
    });

    activityBoxes.forEach(box => {
        box.style.opacity = '0';
        box.style.transform = 'translateY(30px)';
        activityObserver.observe(box);
    });

    // Add hover effect for activity images
    activityBoxes.forEach(box => {
        const image = box.querySelector('.activity-image img');
        if (image) {
            box.addEventListener('mouseenter', () => {
                image.style.transform = 'scale(1.1)';
            });
            box.addEventListener('mouseleave', () => {
                image.style.transform = 'scale(1)';
            });
        }
    });

    // Book button hover effect
    const bookButtons = document.querySelectorAll('.book-btn');
    bookButtons.forEach(btn => {
        btn.addEventListener('mouseenter', () => {
            const icon = btn.querySelector('i');
            if (icon) {
                icon.style.transform = 'translateX(5px)';
            }
        });
        btn.addEventListener('mouseleave', () => {
            const icon = btn.querySelector('i');
            if (icon) {
                icon.style.transform = 'translateX(0)';
            }
        });
    });
});

document.addEventListener('DOMContentLoaded', function() {
    // Handle dropdown menus on mobile
    const dropdowns = document.querySelectorAll('.dropdown');
    
    dropdowns.forEach(dropdown => {
        const link = dropdown.querySelector('a');
        const content = dropdown.querySelector('.dropdown-content');
        
        if (window.innerWidth <= 1024) {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                content.style.display = content.style.display === 'block' ? 'none' : 'block';
            });
        }
    });
});

// Hero Section Animations
document.addEventListener('DOMContentLoaded', () => {
    const heroContent = document.querySelector('.hero-content');
    const heroButtons = document.querySelectorAll('.hero-btn');
    
    // Add hover animation for hero content
    if (heroContent) {
        heroContent.addEventListener('mousemove', (e) => {
            const rect = heroContent.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            // Calculate rotation based on mouse position
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            const rotateX = (y - centerY) / 20;
            const rotateY = (centerX - x) / 20;
            
            heroContent.style.transform = `
                perspective(1000px)
                rotateX(${rotateX}deg)
                rotateY(${rotateY}deg)
                translateY(-10px)
            `;
        });

        heroContent.addEventListener('mouseleave', () => {
            heroContent.style.transform = 'translateY(0)';
        });
    }

    // Add ripple effect for buttons
    heroButtons.forEach(button => {
        button.addEventListener('mouseenter', (e) => {
            const ripple = document.createElement('div');
            ripple.classList.add('btn-ripple');
            button.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 1000);
        });
    });
});

// Activities Section Animations
document.addEventListener('DOMContentLoaded', () => {
    const activitiesContainer = document.querySelector('.activities-container');
    const activityBoxes = document.querySelectorAll('.activity-box');
    
    // Fade in animation for activities container
    if (activitiesContainer) {
        const activitiesObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    activitiesContainer.style.opacity = '1';
                    activitiesContainer.style.transform = 'translateY(0)';
                    activitiesObserver.unobserve(entry.target);
                }
            });
        }, {
            threshold: 0.2,
            rootMargin: '50px'
        });
        
        activitiesObserver.observe(activitiesContainer);
    }

    // Individual activity box animations
    activityBoxes.forEach((box, index) => {
        // Add staggered animation delay
        box.style.transitionDelay = `${index * 0.1}s`;
        
        // Hover effects
        box.addEventListener('mouseenter', () => {
            const image = box.querySelector('.activity-image img');
            const badge = box.querySelector('.activity-badge');
            const btn = box.querySelector('.book-btn');
            
            if (image) {
                image.style.transform = 'scale(1.15)';
            }
            if (badge) {
                badge.style.transform = 'translateY(-2px) scale(1.05)';
            }
            if (btn) {
                const icon = btn.querySelector('i');
                if (icon) {
                    icon.style.transform = 'translateX(5px)';
                }
            }
        });
        
        box.addEventListener('mouseleave', () => {
            const image = box.querySelector('.activity-image img');
            const badge = box.querySelector('.activity-badge');
            const btn = box.querySelector('.book-btn');
            
            if (image) {
                image.style.transform = 'scale(1)';
            }
            if (badge) {
                badge.style.transform = 'translateY(0) scale(1)';
            }
            if (btn) {
                const icon = btn.querySelector('i');
                if (icon) {
                    icon.style.transform = 'translateX(0)';
                }
            }
        });
    });

    // Book button ripple effect
    const bookButtons = document.querySelectorAll('.book-btn');
    bookButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            const rect = this.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            const ripple = document.createElement('span');
            ripple.classList.add('btn-ripple');
            ripple.style.left = `${x}px`;
            ripple.style.top = `${y}px`;
            
            this.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 800);
        });
    });
});

// Intersection Observer for scroll animations
const observerOptions = {
    root: null,
    rootMargin: '0px',
    threshold: 0.2
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('visible');
            // Once the animation is triggered, we can stop observing this element
            observer.unobserve(entry.target);
        }
    });
}, observerOptions);

// Observe sections with scroll animations
document.addEventListener('DOMContentLoaded', () => {
    const sectionsToAnimate = [
        '.booking-info',
        '.activities-section',
        '.features-section',
        '.amenities-section'
    ];
    
    sectionsToAnimate.forEach(selector => {
        const section = document.querySelector(selector);
        if (section) {
            observer.observe(section);
        }
    });
});

// Scroll Animation Observer
const scrollObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('animate');
            
            // For sections that need the 'visible' class
            if (entry.target.classList.contains('activities-section') ||
                entry.target.classList.contains('booking-info')) {
                entry.target.classList.add('visible');
            }
        }
    });
}, {
    threshold: 0.2,
    rootMargin: '0px 0px -50px 0px'
});

// Observe all elements with scroll animation classes
document.addEventListener('DOMContentLoaded', () => {
    // Observe sections
    const sections = document.querySelectorAll('.activities-section, .booking-info');
    sections.forEach(section => scrollObserver.observe(section));

    // Observe individual elements
    const scrollElements = document.querySelectorAll('.scroll-fade, .scroll-slide-up, .info-card');
    scrollElements.forEach(el => scrollObserver.observe(el));
});

// Hero Slider
function initHeroSlider() {
    const slides = document.querySelectorAll('.hero-slider .slide');
    let currentSlide = 0;
    const slideInterval = 5000; // Change slide every 5 seconds

    function nextSlide() {
        slides[currentSlide].classList.remove('active');
        currentSlide = (currentSlide + 1) % slides.length;
        slides[currentSlide].classList.add('active');
    }

    // Start the slider
    setInterval(nextSlide, slideInterval);
}

// Initialize all animations when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    initHeroSlider();
    
    // Scroll animations
    const scrollObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate');
                
                // For sections that need the 'visible' class
                if (entry.target.classList.contains('activities-section') ||
                    entry.target.classList.contains('booking-info')) {
                    entry.target.classList.add('visible');
                }
            }
        });
    }, {
        threshold: 0.2,
        rootMargin: '0px 0px -50px 0px'
    });

    // Observe all elements with scroll animation classes
    const scrollElements = document.querySelectorAll('.scroll-fade, .scroll-slide-up, .info-card, .activities-section, .booking-info');
    scrollElements.forEach(el => scrollObserver.observe(el));
}); 