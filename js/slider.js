class ImageSlider {
    constructor() {
        this.slides = document.querySelectorAll('.slide');
        this.currentSlide = 0;
        this.slideInterval = null;
        this.isAutoPlaying = true;

        this.initializeSlider();
        this.startAutoPlay();
    }

    initializeSlider() {
        // Create and append navigation arrows
        const sliderContainer = document.querySelector('.slider-container');
        
        const prevButton = document.createElement('button');
        prevButton.className = 'slider-nav prev';
        prevButton.innerHTML = '<i class="fas fa-chevron-left"></i>';
        prevButton.setAttribute('aria-label', 'Previous slide');
        
        const nextButton = document.createElement('button');
        nextButton.className = 'slider-nav next';
        nextButton.innerHTML = '<i class="fas fa-chevron-right"></i>';
        nextButton.setAttribute('aria-label', 'Next slide');
        
        sliderContainer.appendChild(prevButton);
        sliderContainer.appendChild(nextButton);

        // Add event listeners
        prevButton.addEventListener('click', () => this.prevSlide());
        nextButton.addEventListener('click', () => this.nextSlide());

        // Pause auto-play on hover
        sliderContainer.addEventListener('mouseenter', () => this.pauseAutoPlay());
        sliderContainer.addEventListener('mouseleave', () => this.startAutoPlay());
    }

    showSlide(index) {
        // Remove active class from all slides
        this.slides.forEach(slide => slide.classList.remove('active'));
        
        // Add active class to current slide
        this.slides[index].classList.add('active');
    }

    nextSlide() {
        this.currentSlide = (this.currentSlide + 1) % this.slides.length;
        this.showSlide(this.currentSlide);
    }

    prevSlide() {
        this.currentSlide = (this.currentSlide - 1 + this.slides.length) % this.slides.length;
        this.showSlide(this.currentSlide);
    }

    startAutoPlay() {
        if (!this.isAutoPlaying) {
            this.isAutoPlaying = true;
            this.slideInterval = setInterval(() => this.nextSlide(), 3000);
        }
    }

    pauseAutoPlay() {
        if (this.isAutoPlaying) {
            this.isAutoPlaying = false;
            clearInterval(this.slideInterval);
        }
    }
}

// Initialize slider when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ImageSlider();
}); 