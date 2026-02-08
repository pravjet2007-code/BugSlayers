document.addEventListener('DOMContentLoaded', () => {
    gsap.registerPlugin(ScrollTrigger, TextPlugin);

    const lenis = new Lenis({
        duration: 1.2,
        easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
        direction: 'vertical',
        smooth: true,
    });
    function raf(time) {
        lenis.raf(time);
        requestAnimationFrame(raf);
    }
    requestAnimationFrame(raf);

    function wrapCharacters(element) {
        if (!element) return;
        const text = element.innerText;
        element.innerHTML = text.split('').map(char => `<span class="char">${char}</span>`).join('');
    }

    const heroTitle = document.querySelector('.hero-title');

    const tl = gsap.timeline();
    tl.from('.hero-title', {
        y: 100,
        opacity: 0,
        duration: 1.2,
        ease: 'power4.out',
        delay: 0.2
    })
        .from('.hero-desc', {
            y: 30,
            opacity: 0,
            duration: 1,
            ease: 'power3.out'
        }, '-=0.8')
        .from('.cta-group', {
            y: 20,
            opacity: 0,
            duration: 0.8
        }, '-=0.6')
        .from('.voice-trigger', {
            scale: 0,
            opacity: 0,
            duration: 0.5,
            ease: 'back.out(1.7)'
        }, '-=0.4');

    const features = document.querySelectorAll('.feature-item');
    if (features.length > 0) {
        gsap.from(features, {
            scrollTrigger: {
                trigger: '.feature-list',
                start: 'top 80%',
            },
            y: 50,
            opacity: 0,
            duration: 1,
            stagger: 0.15,
            ease: 'power3.out'
        });
    }

    gsap.from('.demo-section', {
        scrollTrigger: {
            trigger: '.demo-section',
            start: 'top 85%',
        },
        y: 100,
        opacity: 0,
        duration: 1.2,
        ease: 'power2.out'
    });

    const hiddenInput = document.getElementById('persona-select-value');
    const dropdownTrigger = document.getElementById('dropdown-trigger');
    const dropdownOptions = document.querySelector('.dropdown-options');
    const options = document.querySelectorAll('.dropdown-option');
    const selectedText = document.querySelector('.selected-text');
    const formContainer = document.getElementById('dynamic-form-container');
    const forms = {
        shopper: document.getElementById('form-shopper'),
        rider: document.getElementById('form-rider'),
        patient: document.getElementById('form-patient'),
        coordinator: document.getElementById('form-coordinator'),
        foodie: document.getElementById('form-foodie'),
        traveller: document.getElementById('form-traveller')
    };
    const findDealBtn = document.getElementById('find-deal-btn');

    if (dropdownTrigger && dropdownOptions) {
        dropdownTrigger.addEventListener('click', (e) => {
            e.stopPropagation();
            dropdownOptions.classList.toggle('active');
            const arrow = dropdownTrigger.querySelector('.dropdown-arrow');
            gsap.to(arrow, { rotation: dropdownOptions.classList.contains('active') ? 180 : 0, duration: 0.3 });
        });

        document.addEventListener('click', () => {
            dropdownOptions.classList.remove('active');
            const arrow = dropdownTrigger.querySelector('.dropdown-arrow');
            if (arrow) gsap.to(arrow, { rotation: 0, duration: 0.3 });
        });

        options.forEach(option => {
            option.addEventListener('click', () => {
                const value = option.dataset.value;
                const text = option.textContent;

                selectedText.textContent = text;
                hiddenInput.value = value;

                switchForm(value);
            });
        });
    }

    function switchForm(persona) {
        const btnText = findDealBtn.querySelector('.btn-text');
        let newText = "Execute (" + persona + ")";
        if (persona === 'traveller') newText = "Plan Trip";
        if (persona === 'rider') newText = "Find Ride";

        gsap.to(btnText, {
            opacity: 0, duration: 0.2, onComplete: () => {
                btnText.textContent = newText;
                gsap.to(btnText, { opacity: 1, duration: 0.2 });
            }
        });

        Object.values(forms).forEach(f => {
            if (!f.classList.contains('hidden')) {
                gsap.to(f, {
                    opacity: 0, y: -10, duration: 0.3, onComplete: () => {
                        f.classList.add('hidden');
                    }
                });
            }
        });

        const activeForm = forms[persona];
        if (activeForm) {
            setTimeout(() => {
                activeForm.classList.remove('hidden');
                gsap.fromTo(activeForm, { y: 20, opacity: 0 }, { y: 0, opacity: 1, duration: 0.5 });
            }, 300);
        }
    }

    formContainer.addEventListener('click', (e) => {
        if (e.target.closest('#add-guest-btn')) {
            const container = document.getElementById('guest-list-container');
            const div = document.createElement('div');
            div.className = 'guest-item';
            div.style.marginBottom = '10px';
            div.innerHTML = `<input type="text" class="styled-input guest-name" placeholder="Guest Name">`;
            container.appendChild(div);
            gsap.from(div, { opacity: 0, y: 10, duration: 0.3 });
        }
        if (e.target.closest('#add-medicine-btn')) {
            const container = document.getElementById('medicine-list-container');
            const div = document.createElement('div');
            div.className = 'input-group medicine-item';
            div.style.display = 'flex'; div.style.gap = '10px'; div.style.marginBottom = '10px';
            div.innerHTML = `
                <input type="text" class="styled-input med-name" placeholder="Medicine Name" style="flex: 2;">
                <input type="number" class="styled-input med-qty" placeholder="Qty" style="flex: 1;" value="1">
            `;
            container.appendChild(div);
            gsap.from(div, { opacity: 0, y: 10, duration: 0.3 });
        }
    });

    const riderPills = document.querySelectorAll('#rider-preferences .pill-option');
    const riderPrefInput = document.getElementById('rider-preference-value');
    riderPills.forEach(pill => {
        pill.addEventListener('click', () => {
            riderPills.forEach(p => p.classList.remove('active'));
            pill.classList.add('active');
            if (riderPrefInput) riderPrefInput.value = pill.dataset.value;
        });
    });

    if (findDealBtn) {
        findDealBtn.addEventListener('click', async () => {
            const persona = hiddenInput.value;
            if (!persona) {
                alert("Please select a persona first.");
                return;
            }

            const payload = { persona: persona, timestamp: new Date().toISOString() };

            if (persona === 'shopper') {
                payload.product = document.getElementById('product-name').value;
            } else if (persona === 'rider') {
                payload.pickup = document.getElementById('pickup-location').value;
                payload.drop = document.getElementById('drop-location').value;
                if (riderPrefInput) payload.preference = riderPrefInput.value;
                const toggle = document.getElementById('rider-action-toggle');
                payload.action = (toggle && toggle.checked) ? 'book' : 'compare';
            } else if (persona === 'patient') {
                const medItems = document.querySelectorAll('.medicine-item');
                const medList = [];
                medItems.forEach(item => {
                    const name = item.querySelector('.med-name').value;
                    const qty = item.querySelector('.med-qty').value;
                    if (name) medList.push({ name: name, qty: parseInt(qty) || 1 });
                });
                payload.medicine = medList;
            } else if (persona === 'coordinator') {
                payload.event_name = document.getElementById('event-name').value;
                const guests = [];
                document.querySelectorAll('.guest-name').forEach(i => { if (i.value) guests.push(i.value) });
                payload.guest_list = guests;
            } else if (persona === 'foodie') {
                payload.food_item = document.getElementById('food-item').value;
                const toggle = document.getElementById('foodie-action-toggle');
                payload.action = (toggle && toggle.checked) ? 'order' : 'search';
            } else if (persona === 'traveller') {
                payload.source = document.getElementById('trip-source').value;
                payload.destination = document.getElementById('trip-dest').value;
                payload.date = document.getElementById('trip-date').value;
                payload.end_date = document.getElementById('trip-end-date').value;
                payload.user_interests = document.getElementById('trip-interests').value;
            }

            logStatus("Sending task...");
            try {
                await fetch('http://localhost:8002/task', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
            } catch (e) {
                logStatus("Error sending task: " + e.message, 'error');
            }
        });
    }

    function connectWebSocket() {
        const ws = new WebSocket('ws://localhost:8002/ws');
        ws.onopen = () => logStatus('Connected to Neural Core.');
        ws.onmessage = (event) => {
            try {
                const parsed = JSON.parse(event.data);
                if (parsed.type === 'log') {
                    logStatus(parsed.message);
                } else if (parsed.type === 'complete') {
                    showResultUI(parsed.result);
                    if (window.lastVoiceCommand) {
                        speak("Task complete. " + (parsed.result.message || "Operation successful."));
                        window.lastVoiceCommand = false;
                    }
                }
            } catch (e) { console.log(event.data); }
        };
        ws.onclose = () => setTimeout(connectWebSocket, 3000);
    }
    connectWebSocket();

    const voiceTrigger = document.getElementById('voice-trigger');
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (SpeechRecognition && voiceTrigger) {
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.lang = 'en-US';
        recognition.interimResults = false;

        voiceTrigger.addEventListener('click', () => {
            try {
                recognition.start();
                voiceTrigger.classList.add('voice-active');
            } catch (e) {
                console.log("Recognition already started");
            }
        });

        recognition.onresult = async (event) => {
            voiceTrigger.classList.remove('voice-active');
            const transcript = event.results[0][0].transcript;
            console.log("Voice Command:", transcript);
            logStatus(`Voice Input: "${transcript}"`);

            window.lastVoiceCommand = true;

            try {
                const response = await fetch('http://localhost:8002/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        session_id: "voice-web-" + Date.now(),
                        message: transcript
                    })
                });

                const data = await response.json();
                console.log("AI Response:", data);

                if (data.response) {
                    speak(data.response);
                    logStatus("AI: " + data.response);
                }

            } catch (e) {
                logStatus("Voice Error: " + e.message, 'error');
                speak("I'm having trouble connecting to the core.");
            }
        };

        recognition.onerror = (event) => {
            voiceTrigger.classList.remove('voice-active');
            console.error("Speech Error", event.error);
        };

        recognition.onend = () => {
            voiceTrigger.classList.remove('voice-active');
        };
    } else {
        if (voiceTrigger) voiceTrigger.style.display = 'none';
    }

    function speak(text) {
        const utterance = new SpeechSynthesisUtterance(text);
        window.speechSynthesis.speak(utterance);
    }

    function logStatus(msg, type = 'info') {
        const consoleEl = document.getElementById('result-message');
        if (consoleEl) consoleEl.textContent = msg;
        if (type === 'error') consoleEl.style.color = '#ff4d4d';
        else consoleEl.style.color = 'var(--accent)';
    }

    function showResultUI(result) {
        const panel = document.getElementById('result-panel');
        if (panel) {
            panel.classList.remove('hidden');
            logStatus(result.message || "Task Complete");
        }
    }
});
