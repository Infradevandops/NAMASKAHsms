/**
 * Scroll Timeline - Premium scroll progress indicator
 * Features: Progress bar, timeline dots, smooth animations
 */

class ScrollTimeline {
  constructor() {
    this.sections = [];
    this.dots = [];
    this.progressBar = null;
    this.init();
  }

  init() {
    this.createProgressBar();
    this.createTimeline();
    this.setupScrollListener();
    this.setupResizeListener();
  }

  createProgressBar() {
    const bar = document.createElement('div');
    bar.className = 'scroll-progress-bar';
    document.body.appendChild(bar);
    this.progressBar = bar;
  }

  createTimeline() {
    const timeline = document.createElement('div');
    timeline.className = 'scroll-timeline';

    // Find all sections with data-timeline-section attribute
    const sections = document.querySelectorAll('[data-timeline-section]');
    
    sections.forEach((section, index) => {
      this.sections.push(section);

      const dot = document.createElement('div');
      dot.className = 'timeline-dot';
      dot.setAttribute('data-section', index);

      const label = document.createElement('div');
      label.className = 'timeline-label';
      label.textContent = section.getAttribute('data-timeline-label') || `Section ${index + 1}`;

      dot.appendChild(label);
      dot.addEventListener('click', () => this.scrollToSection(index));

      timeline.appendChild(dot);
      this.dots.push(dot);
    });

    document.body.appendChild(timeline);
  }

  setupScrollListener() {
    window.addEventListener('scroll', () => this.updateProgress());
    this.updateProgress(); // Initial call
  }

  setupResizeListener() {
    window.addEventListener('resize', () => this.updateProgress());
  }

  updateProgress() {
    // Update progress bar
    const scrollHeight = document.documentElement.scrollHeight - window.innerHeight;
    const scrolled = (window.scrollY / scrollHeight) * 100;
    this.progressBar.style.width = scrolled + '%';

    // Update timeline dots
    this.updateActiveDot();
  }

  updateActiveDot() {
    let activeIndex = 0;
    const scrollPosition = window.scrollY + window.innerHeight / 2;

    for (let i = 0; i < this.sections.length; i++) {
      const section = this.sections[i];
      const sectionTop = section.offsetTop;
      const sectionBottom = sectionTop + section.offsetHeight;

      if (scrollPosition >= sectionTop && scrollPosition < sectionBottom) {
        activeIndex = i;
        break;
      }
    }

    // Update dots
    this.dots.forEach((dot, index) => {
      if (index === activeIndex) {
        dot.classList.add('active');
      } else {
        dot.classList.remove('active');
      }
    });
  }

  scrollToSection(index) {
    if (index >= 0 && index < this.sections.length) {
      const section = this.sections[index];
      section.scrollIntoView({ behavior: 'smooth' });
    }
  }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    new ScrollTimeline();
  });
} else {
  new ScrollTimeline();
}
