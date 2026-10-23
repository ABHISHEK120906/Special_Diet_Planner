/**
 * NutriGenAI - Client Logic & Reactive Wizard
 */

// Immediate theme bootstrap before DOM loads to avoid theme flicker
(function () {
    try {
        const saved = localStorage.getItem('nutrigen_theme');
        const theme = saved || (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark');
        document.documentElement.setAttribute('data-theme', theme);
    } catch (e) {}
})();

document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initWizard();
    initRadioCards();
    initLiveCalculator();
    initFormSubmission();
});

/* ==========================================================================
   Theme Management (Dark & Light Mode)
   ========================================================================== */
function initTheme() {
    const current = document.documentElement.getAttribute('data-theme') || 
                    localStorage.getItem('nutrigen_theme') || 'dark';
    applyTheme(current);
}

function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    if (document.body) {
        document.body.setAttribute('data-theme', theme);
    }
    try {
        localStorage.setItem('nutrigen_theme', theme);
    } catch (e) {}

    // Update all theme icons on page (if multiple)
    document.querySelectorAll('#themeIcon').forEach(icon => {
        if (theme === 'light') {
            icon.className = 'fa-solid fa-moon';
        } else {
            icon.className = 'fa-solid fa-sun';
        }
    });
}

function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme') || 'dark';
    const next = current === 'dark' ? 'light' : 'dark';
    applyTheme(next);
}

/* ==========================================================================
   Wizard Navigation
   ========================================================================== */
function initWizard() {
    const nextButtons = document.querySelectorAll('.next-step-btn');
    const prevButtons = document.querySelectorAll('.prev-step-btn');
    const stepIndicators = document.querySelectorAll('.step-indicator');

    nextButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const currentPane = btn.closest('.wizard-pane');
            const nextStep = btn.getAttribute('data-next');

            // Validate inputs in current pane
            const requiredInputs = currentPane.querySelectorAll('input[required], select[required]');
            let isValid = true;
            requiredInputs.forEach(input => {
                if (!input.value) {
                    isValid = false;
                    input.style.borderColor = '#f43f5e';
                    input.focus();
                } else {
                    input.style.borderColor = '';
                }
            });

            if (!isValid) {
                showToast("Please fill in the required fields before continuing.", "warning");
                return;
            }

            goToStep(nextStep);
        });
    });

    prevButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const prevStep = btn.getAttribute('data-prev');
            goToStep(prevStep);
        });
    });

    stepIndicators.forEach(ind => {
        ind.addEventListener('click', () => {
            const step = ind.getAttribute('data-step');
            goToStep(step);
        });
    });
}

function goToStep(stepNum) {
    document.querySelectorAll('.wizard-pane').forEach(p => p.classList.remove('active'));
    const targetPane = document.getElementById(`pane-step-${stepNum}`);
    if (targetPane) targetPane.classList.add('active');

    // Update indicators
    document.querySelectorAll('.step-indicator').forEach(ind => {
        const indStep = parseInt(ind.getAttribute('data-step'));
        ind.classList.remove('active', 'completed');
        if (indStep === parseInt(stepNum)) {
            ind.classList.add('active');
        } else if (indStep < parseInt(stepNum)) {
            ind.classList.add('completed');
        }
    });

    // Scroll to top of form card on mobile
    if (window.innerWidth < 768) {
        document.querySelector('.planner-form-card').scrollIntoView({ behavior: 'smooth' });
    }
}

/* ==========================================================================
   Custom Radio Cards
   ========================================================================== */
function initRadioCards() {
    const radioCards = document.querySelectorAll('.radio-card');
    radioCards.forEach(card => {
        card.addEventListener('click', () => {
            const groupName = card.querySelector('input[type="radio"]').name;
            document.querySelectorAll(`input[name="${groupName}"]`).forEach(r => {
                r.closest('.radio-card').classList.remove('selected');
            });
            card.classList.add('selected');
            const radioInput = card.querySelector('input[type="radio"]');
            radioInput.checked = true;
            triggerLiveCalculation();
        });
    });
}

/* ==========================================================================
   Real-Time Live Bio-Calculator
   ========================================================================== */
let calcDebounceTimer = null;

function initLiveCalculator() {
    const liveInputs = document.querySelectorAll('.live-input');
    liveInputs.forEach(input => {
        input.addEventListener('input', triggerLiveCalculation);
        input.addEventListener('change', triggerLiveCalculation);
    });

    // Run initial calculation on page load
    triggerLiveCalculation();
}

function triggerLiveCalculation() {
    clearTimeout(calcDebounceTimer);
    calcDebounceTimer = setTimeout(performLiveCalculation, 150);
}

async function performLiveCalculation() {
    const weight = parseFloat(document.getElementById('weight')?.value) || 70;
    const height = parseFloat(document.getElementById('height')?.value) || 170;
    const age = parseInt(document.getElementById('age')?.value) || 25;
    const gender = document.getElementById('gender')?.value || 'male';
    
    const actRadio = document.querySelector('input[name="activity_level"]:checked');
    const activity_level = actRadio ? actRadio.value : 'moderately_active';

    const goalRadio = document.querySelector('input[name="goal"]:checked');
    const goal = goalRadio ? goalRadio.value : 'weight_loss';

    const dietaryPref = document.getElementById('dietary_preference')?.value || 'vegetarian';

    try {
        const response = await fetch('/api/calculate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                weight, height, age, gender, activity_level, goal, dietary_preference: dietaryPref
            })
        });
        const result = await response.json();
        if (result.success && result.targets) {
            updatePreviewUI(result.targets);
        }
    } catch (err) {
        // Fallback local calculations if server is unreachable
        computeLocalTargets(weight, height, age, gender, activity_level, goal);
    }
}

function updatePreviewUI(targets) {
    const calEl = document.getElementById('preview-calories');
    if (calEl) calEl.innerText = targets.calorie_target.toLocaleString();

    const goalDescEl = document.getElementById('preview-goal-desc');
    if (goalDescEl) goalDescEl.innerText = targets.goal_description || 'Energy Balance';

    const bmiEl = document.getElementById('preview-bmi');
    if (bmiEl) bmiEl.innerText = targets.bmi;

    const bmiCatEl = document.getElementById('preview-bmi-cat');
    if (bmiCatEl) {
        bmiCatEl.innerText = targets.bmi_category;
        bmiCatEl.style.color = targets.bmi_color || '#10b981';
    }

    const bmrEl = document.getElementById('preview-bmr');
    if (bmrEl) bmrEl.innerText = Math.round(targets.bmr).toLocaleString();

    const tdeeEl = document.getElementById('preview-tdee');
    if (tdeeEl) tdeeEl.innerText = Math.round(targets.tdee).toLocaleString();

    const waterEl = document.getElementById('preview-water');
    if (waterEl) waterEl.innerText = `${targets.water_liters}L`;

    // Step 4 3D Summary Card Elements
    const sumCalEl = document.getElementById('summary-preview-cals');
    if (sumCalEl) sumCalEl.innerText = `${targets.calorie_target.toLocaleString()} kcal`;

    const sumProtEl = document.getElementById('summary-preview-protein');
    if (sumProtEl) sumProtEl.innerText = `${targets.protein_g}g`;

    const sumWaterEl = document.getElementById('summary-preview-water');
    if (sumWaterEl) sumWaterEl.innerText = `${targets.water_liters} Liters`;

    const pEl = document.getElementById('preview-protein');
    if (pEl) pEl.innerText = `${targets.protein_g}g`;
    const pPct = document.getElementById('preview-protein-pct');
    if (pPct) pPct.innerText = `${targets.protein_pct}%`;

    const cEl = document.getElementById('preview-carbs');
    if (cEl) cEl.innerText = `${targets.carbs_g}g`;
    const cPct = document.getElementById('preview-carbs-pct');
    if (cPct) cPct.innerText = `${targets.carbs_pct}%`;

    const fEl = document.getElementById('preview-fats');
    if (fEl) fEl.innerText = `${targets.fat_g}g`;
    const fPct = document.getElementById('preview-fats-pct');
    if (fPct) fPct.innerText = `${targets.fat_pct}%`;

    if (typeof updateMacroBars === 'function') {
        updateMacroBars(targets.protein_pct, targets.carbs_pct, targets.fat_pct);
    }
}

function computeLocalTargets(weight, height, age, gender, activity, goal) {
    // Mifflin-St Jeor local calculation fallback
    let bmr = (10 * weight) + (6.25 * height) - (5 * age);
    bmr += (gender === 'male' ? 5 : -161);
    
    const mults = { sedentary: 1.2, lightly_active: 1.375, moderately_active: 1.55, very_active: 1.725 };
    const mult = mults[activity] || 1.375;
    const tdee = Math.round(bmr * mult);
    
    let cals = tdee - 500;
    if (goal === 'muscle_gain') cals = tdee + 350;
    else if (goal === 'maintenance') cals = tdee;
    cals = Math.max(1200, cals);

    const bmi = (weight / ((height / 100) ** 2)).toFixed(1);
    
    updatePreviewUI({
        calorie_target: cals,
        goal_description: `${goal.replace('_', ' ').toUpperCase()} Target`,
        bmi: bmi,
        bmi_category: bmi < 25 ? 'Normal' : 'Overweight',
        bmi_color: bmi < 25 ? '#10b981' : '#f59e0b',
        bmr: Math.round(bmr),
        tdee: tdee,
        water_liters: (weight * 0.035).toFixed(1),
        protein_g: Math.round((cals * 0.35) / 4),
        protein_pct: 35,
        carbs_g: Math.round((cals * 0.40) / 4),
        carbs_pct: 40,
        fat_g: Math.round((cals * 0.25) / 9),
        fat_pct: 25
    });
}

/* ==========================================================================
   Plan Generation & AJAX Submission
   ========================================================================== */
function initFormSubmission() {
    const form = document.getElementById('diet-wizard-form');
    const submitBtn = document.getElementById('generate-submit-btn');
    if (!form) return;

    const executeSubmission = async (e) => {
        if (e) {
            e.preventDefault();
            e.stopPropagation();
        }

        // Validate essentials before launching generation
        const ageInput = document.getElementById('age');
        const weightInput = document.getElementById('weight');
        const heightInput = document.getElementById('height');

        const age = parseInt(ageInput?.value) || 0;
        const weight = parseFloat(weightInput?.value) || 0;
        const height = parseFloat(heightInput?.value) || 0;

        if (age < 14 || age > 100 || weight < 30 || weight > 300 || height < 100 || height > 250) {
            goToStep(1);
            showToast("Please enter valid vitals (Age, Weight, Height) in Step 1.", "warning");
            if (age < 14 || age > 100) ageInput?.focus();
            else if (weight < 30 || weight > 300) weightInput?.focus();
            else heightInput?.focus();
            return;
        }

        const overlay = document.getElementById('loading-overlay');
        const statusDesc = document.getElementById('loading-status-desc');
        if (overlay) overlay.classList.add('active');

        // Form data extraction
        const formData = new FormData(form);
        const payload = {
            user_name: (formData.get('user_name') || 'Guest').toString().trim(),
            age: age || 25,
            gender: (formData.get('gender') || 'male').toString(),
            weight: weight || 70,
            target_weight: formData.get('target_weight') ? parseFloat(formData.get('target_weight')) : null,
            height: height || 170,
            activity_level: (formData.get('activity_level') || 'moderately_active').toString(),
            goal: (formData.get('goal') || 'weight_loss').toString(),
            dietary_preference: (formData.get('dietary_preference') || 'vegetarian').toString(),
            allergies: (formData.get('allergies') || '').toString(),
            title: (formData.get('title') || 'Personalized AI Diet Plan').toString(),
            gemini_api_key: ''
        };

        // Loading message transitions
        const stepMessages = [
            "Calculating BMR, TDEE, and optimal macronutrient split...",
            "Consulting clinical database & recipe architecture...",
            "Formulating bioavailability tips, grocery items, and hydration schedule..."
        ];

        let msgIndex = 0;
        const msgInterval = setInterval(() => {
            msgIndex = (msgIndex + 1) % stepMessages.length;
            if (statusDesc) statusDesc.innerText = stepMessages[msgIndex];
        }, 1800);

        try {
            const resp = await fetch('/api/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            clearInterval(msgInterval);
            const data = await resp.json();

            if (data.success) {
                const targetUrl = data.redirect_url || (data.plan_id ? `/plan/${data.plan_id}` : '/plan/latest');
                window.location.href = targetUrl;
            } else {
                if (overlay) overlay.classList.remove('active');
                showToast(data.error || "Generation error. Please check inputs.", "warning");
            }
        } catch (err) {
            clearInterval(msgInterval);
            if (overlay) overlay.classList.remove('active');
            showToast("Server connection error: " + err.message, "warning");
        }
    };

    form.addEventListener('submit', executeSubmission);
    if (submitBtn) {
        submitBtn.addEventListener('click', (e) => {
            executeSubmission(e);
        });
    }
}

/* ==========================================================================
   Toast Notification System
   ========================================================================== */
function showToast(message, type = "info") {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    let icon = "fa-circle-info";
    if (type === "success") icon = "fa-circle-check";
    if (type === "warning") icon = "fa-triangle-exclamation";

    toast.innerHTML = `<i class="fa-solid ${icon}"></i> <span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(10px)';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}
