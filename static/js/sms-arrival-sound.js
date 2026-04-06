/**
 * Namaskah — SMS Arrival Sound
 * Web Audio API — no external files, no dependencies
 */

function playArrivalSound() {
    try {
        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        // Two-tone chime: C5 → E5
        [[523.25, 0], [659.25, 0.18]].forEach(([freq, delay]) => {
            const osc  = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.type = 'sine';
            osc.frequency.value = freq;
            gain.gain.setValueAtTime(0, ctx.currentTime + delay);
            gain.gain.linearRampToValueAtTime(0.28, ctx.currentTime + delay + 0.02);
            gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + delay + 0.45);
            osc.start(ctx.currentTime + delay);
            osc.stop(ctx.currentTime + delay + 0.5);
        });
    } catch (e) { /* silent fail — sound is non-critical */ }
}
