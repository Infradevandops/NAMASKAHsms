/**
 * Scroll Timeline Module
 * Handles scroll progress tracking, timeline navigation, and animations
 */

export function initScrollTimeline() {
  const timeline = new ScrollTimeline()
  timeline.init()
  return timeline
}

class ScrollTimeline {
  constructor() {
    this.sections = []
    this.currentSection = null
    this.scrollProgress = 0
    this.isScrolling = false
    this.scrollTimeout = null
  }

  init() {
    this.setupElements()
    this.setupEventListeners()
    this.updateProgress()
  }

  setupElements() {
    // Get all timeline sections
    this.sections = Array.from(document.querySelectorAll('[data-timeline-section]'))
    
    if (this.sections.length === 0) {
      console.warn('No timeline sections found')
      return
    }

    // Create timeline container
    this.createTimeline()
    
    // Create progress bar
    this.createProgressBar()
    
    // Create scroll to top button
    this.createScrollToTopButton()
  }

  createTimeline() {
    const container = document.createElement('div')
    container.className = 'scroll-timeline'
    container.id = 'scroll-timeline'

    // Create line
    const line = document.createElement('div')
    line.className = 'scroll-timeline-line'
    
    const lineProgress = document.createElement('div')
    lineProgress.className = 'scroll-timeline-line-progress'
    line.appendChild(lineProgress)
    container.appendChild(line)

    // Create timeline items
    this.sections.forEach((section, index) => {
      const item = document.createElement('div')
      item.className = 'scroll-timeline-item'
      item.dataset.index = index
      item.dataset.sectionId = section.id || `section-${index}`

      const dot = document.createElement('div')
      dot.className = 'scroll-timeline-dot'

      const label = document.createElement('div')
      label.className = 'scroll-timeline-label'
      label.textContent = section.dataset.timelineLabel || `Section ${index + 1}`

      item.appendChild(dot)
      item.appendChild(label)

      item.addEventListener('click', () => this.scrollToSection(index))
      container.appendChild(item)
    })

    document.body.appendChild(container)
    this.timelineContainer = container
  }

  createProgressBar() {
    const bar = document.createElement('div')
    bar.className = 'scroll-progress-bar'
    bar.id = 'scroll-progress-bar'
    document.body.appendChild(bar)
    this.progressBar = bar
  }

  createScrollToTopButton() {
    const button = document.createElement('button')
    button.className = 'scroll-to-top'
    button.id = 'scroll-to-top'
    button.innerHTML = '↑'
    button.setAttribute('aria-label', 'Scroll to top')
    
    button.addEventListener('click', () => this.scrollToTop())
    document.body.appendChild(button)
    this.scrollToTopButton = button
  }

  setupEventListeners() {
    window.addEventListener('scroll', () => this.handleScroll(), { passive: true })
    window.addEventListener('resize', () => this.updateProgress(), { passive: true })
  }

  handleScroll() {
    this.isScrolling = true
    this.updateProgress()
    this.updateTimeline()
    this.updateScrollToTopButton()

    // Clear timeout
    clearTimeout(this.scrollTimeout)
    
    // Set timeout to detect scroll end
    this.scrollTimeout = setTimeout(() => {
      this.isScrolling = false
    }, 150)
  }

  updateProgress() {
    const scrollTop = window.scrollY
    const docHeight = document.documentElement.scrollHeight - window.innerHeight
    const scrolled = docHeight > 0 ? (scrollTop / docHeight) * 100 : 0

    this.scrollProgress = Math.min(scrolled, 100)

    // Update progress bar
    if (this.progressBar) {
      this.progressBar.style.width = `${this.scrollProgress}%`
    }

    // Update timeline line progress
    const lineProgress = this.timelineContainer?.querySelector('.scroll-timeline-line-progress')
    if (lineProgress) {
      lineProgress.style.height = `${this.scrollProgress}%`
    }
  }

  updateTimeline() {
    let activeIndex = -1

    // Find current section
    this.sections.forEach((section, index) => {
      const rect = section.getBoundingClientRect()
      if (rect.top <= window.innerHeight / 2) {
        activeIndex = index
      }
    })

    // Update active state
    if (activeIndex !== this.currentSection) {
      this.currentSection = activeIndex

      // Remove active class from all items
      document.querySelectorAll('.scroll-timeline-item').forEach(item => {
        item.classList.remove('active')
      })

      // Add active class to current item
      if (activeIndex >= 0) {
        const activeItem = document.querySelector(
          `.scroll-timeline-item[data-index="${activeIndex}"]`
        )
        if (activeItem) {
          activeItem.classList.add('active')
        }
      }
    }

    // Add in-view animation to sections
    this.sections.forEach((section, index) => {
      const rect = section.getBoundingClientRect()
      if (rect.top < window.innerHeight * 0.75) {
        section.classList.add('in-view')
      }
    })
  }

  updateScrollToTopButton() {
    if (!this.scrollToTopButton) return

    if (window.scrollY > window.innerHeight) {
      this.scrollToTopButton.classList.add('visible')
    } else {
      this.scrollToTopButton.classList.remove('visible')
    }
  }

  scrollToSection(index) {
    if (index < 0 || index >= this.sections.length) return

    const section = this.sections[index]
    const offsetTop = section.offsetTop - 80 // Account for fixed header

    window.scrollTo({
      top: offsetTop,
      behavior: 'smooth'
    })
  }

  scrollToTop() {
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    })
  }

  destroy() {
    window.removeEventListener('scroll', () => this.handleScroll())
    window.removeEventListener('resize', () => this.updateProgress())
    
    if (this.timelineContainer) {
      this.timelineContainer.remove()
    }
    if (this.progressBar) {
      this.progressBar.remove()
    }
    if (this.scrollToTopButton) {
      this.scrollToTopButton.remove()
    }
  }
}

export { ScrollTimeline }

