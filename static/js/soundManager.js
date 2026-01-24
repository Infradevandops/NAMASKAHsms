/**
 * Sound Manager - Handles notification sounds
 * Lightweight, stable, with graceful fallback
 */

class SoundManager {
    constructor() {
        this.enabled = localStorage.getItem('soundEnabled') !== 'false';
        this.volume = parseFloat(localStorage.getItem('soundVolume') || '0.5');
        this.sounds = {};
        this.audioContext = null;
        
        // Initialize Web Audio API for fallback
        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        } catch (e) {
            console.log('Web Audio API not supported');
        }
    }
    
    /**
     * Play a tone using Web Audio API (no files needed)
     */
    playTone(frequency, duration = 0.3, type = 'sine') {
        if (!this.enabled || !this.audioContext) return;
        
        try {
            const oscillator = this.audioContext.createOscillator();
            const gainNode = this.audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(this.audioContext.destination);
            
            oscillator.frequency.value = frequency;
            oscillator.type = type;
            gainNode.gain.value = this.volume;
            
            const now = this.audioContext.currentTime;
            gainNode.gain.setValueAtTime(this.volume, now);
            gainNode.gain.exponentialRampToValueAtTime(0.01, now + duration);
            
            oscillator.start(now);
            oscillator.stop(now + duration);
        } catch (e) {
            console.error('Sound play failed:', e);
        }
    }
    
    /**
     * Play notification sound based on type
     */
    play(type) {
        if (!this.enabled) return;
        
        switch(type) {
            case 'deduction':
            case 'credit_deducted':
                // Subtle ding (440Hz)
                this.playTone(440, 0.3);
                break;
                
            case 'verification_created':
                // Positive chime (C-E-G chord)
                this.playTone(523, 0.15); // C
                setTimeout(() => this.playTone(659, 0.15), 100); // E
                setTimeout(() => this.playTone(784, 0.2), 200); // G
                break;
                
            case 'sms_received':
                // Exciting notification (800Hz)
                this.playTone(800, 0.4, 'square');
                break;
                
            case 'instant_refund':
            case 'refund':
                // Success tone (G-C)
                this.playTone(784, 0.3); // G
                setTimeout(() => this.playTone(523, 0.3), 200); // C
                break;
                
            default:
                // Generic notification
                this.playTone(600, 0.3);
        }
    }
    
    /**
     * Toggle sound on/off
     */
    toggle() {
        this.enabled = !this.enabled;
        localStorage.setItem('soundEnabled', this.enabled);
        return this.enabled;
    }
    
    /**
     * Set volume (0.0 to 1.0)
     */
    setVolume(volume) {
        this.volume = Math.max(0, Math.min(1, volume));
        localStorage.setItem('soundVolume', this.volume);
    }
    
    /**
     * Test sound
     */
    test() {
        this.play('verification_created');
    }
}

// Global instance
window.soundManager = new SoundManager();

// Auto-play sounds when notifications arrive
if (typeof window.addEventListener !== 'undefined') {
    window.addEventListener('notification', (event) => {
        if (event.detail && event.detail.type) {
            window.soundManager.play(event.detail.type);
        }
    });
}
