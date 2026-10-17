/**
 * Macro Distribution Bar & Metric Visualization
 */

function updateMacroBars(proteinPct, carbsPct, fatPct) {
    const pBar = document.getElementById('bar-protein');
    const cBar = document.getElementById('bar-carbs');
    const fBar = document.getElementById('bar-fats');

    if (pBar) pBar.style.width = `${proteinPct}%`;
    if (cBar) cBar.style.width = `${carbsPct}%`;
    if (fBar) fBar.style.width = `${fatPct}%`;
}

function animateNumber(elementId, start, end, duration = 400, suffix = "") {
    const el = document.getElementById(elementId);
    if (!el) return;
    
    const range = end - start;
    let current = start;
    const increment = end > start ? 1 : -1;
    const stepTime = Math.abs(Math.floor(duration / (range || 1)));
    
    if (range === 0) {
        el.innerText = end.toLocaleString() + suffix;
        return;
    }

    const timer = setInterval(() => {
        current += Math.ceil((end - current) / 6);
        if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
            current = end;
            clearInterval(timer);
        }
        el.innerText = current.toLocaleString() + suffix;
    }, Math.max(20, stepTime));
}
