
// 1. RSS Fetching & Rendering
document.addEventListener("DOMContentLoaded", async () => {
    const container = document.getElementById("blog-list");
    const rss = "https://bhban.tistory.com/rss";
    const url = "https://r.jina.ai/" + rss;

    const fallbackThumb = "https://via.placeholder.com/240x144?text=Blog";

    try {
        const raw = await fetch(url).then(r => r.text());

        const chunks = raw.split("===============");
        const items = [];

        for (let i = 2; i < chunks.length; i++) {
            const prev = chunks[i - 1];
            const current = chunks[i];

            // Extract Title
            const prevLines = prev.trim().split(/\r?\n/);
            const lastLine = prevLines[prevLines.length - 1].trim();
            const titleParts = lastLine.split(/\s{2,}/);
            const title = titleParts[titleParts.length - 1].trim();

            // Extract Link
            const linkMatch = current.trim().match(/^https?:\/\/[^\s]+/);
            const link = linkMatch ? linkMatch[0] : "";

            // Extract Date
            const dateMatch = current.match(/[a-zA-Z]{3}, \d{1,2} [a-zA-Z]{3} \d{4} \d{2}:\d{2}:\d{2} \+\d{4}/);
            let isoDate = "";
            if (dateMatch) {
                try {
                    isoDate = new Date(dateMatch[0]).toISOString().slice(0, 10);
                } catch (e) { /* ignore */ }
            }

            // Extract Image
            let thumb = fallbackThumb;
            try {
                const doc = new DOMParser().parseFromString(current, 'text/html');
                const img = doc.querySelector('img');
                if (img && img.src) {
                    thumb = img.src;
                } else {
                    const mdImg = current.match(/!\[.*?\]\((.*?)\)/);
                    if (mdImg) thumb = mdImg[1];
                }
            } catch (e) { console.warn("Image parse error", e); }

            if (title && link) {
                items.push({ title, link, date: isoDate, thumb });
            }
        }

        if (items.length > 0) items.shift();
        const validItems = items.slice(0, 10);

        container.innerHTML = "";
        if (validItems.length === 0) console.warn("No items parsed from Jina.ai");

        validItems.forEach(it => {
            const a = document.createElement("a");
            a.href = it.link;
            a.target = "_blank";
            a.rel = "noopener noreferrer";
            a.className = "blog-item";
            a.ondragstart = () => false;

            a.innerHTML = `
                <div class="card">
                    <img class="thumb" src="${it.thumb}" alt="">
                    <div class="meta">
                        <h3>${it.title}</h3>
                        <p class="date">${it.date}</p>
                    </div>
                </div>
            `;
            const img = a.querySelector("img");
            if (img) {
                img.addEventListener("error", e => e.currentTarget.src = fallbackThumb);
            }
            container.appendChild(a);
        });

        initCoverFlow(container);

    } catch (e) {
        console.error("RSS parsing error:", e);
        container.innerHTML = `<p style="text-align:center; width:100%;">Failed to load apps: ${e.message}</p>`;
    }
});

// 2. Cover Flow Physics
function initCoverFlow(slider) {
    let isDown = false;
    let startX;
    let scrollLeft;
    let isDragging = false;

    let currentScroll = slider.scrollLeft;
    let targetScroll = slider.scrollLeft;
    let velocity = 0;
    let isPhysicsActive = false;

    const SENSITIVITY = 4.2;
    const FRICTION = 0.96;
    const LERP_FACTOR = 0.07;
    const MAX_VELOCITY = 48;
    const SNAP_THRESHOLD = 3.0;

    let isSnapping = false;
    let snapTarget = 0;
    let idleTimer;
    const swipeHint = document.getElementById('swipe-hint');

    function resetIdle() {
        if (swipeHint.classList.contains('visible')) {
            swipeHint.classList.remove('visible');
        }
        clearTimeout(idleTimer);
        idleTimer = setTimeout(() => {
            if (!isDown && !isPhysicsActive) {
                swipeHint.classList.add('visible');
            }
        }, 3000);
    }

    resetIdle();

    function render() {
        if (isPhysicsActive) {
            if (swipeHint.classList.contains('visible') && Math.abs(velocity) > 0.5) {
                swipeHint.classList.remove('visible');
            }

            if (isDown) {
                isSnapping = false;
                const diff = targetScroll - currentScroll;
                velocity = diff * LERP_FACTOR;
                if (Math.abs(velocity) > MAX_VELOCITY) velocity = (velocity > 0 ? 1 : -1) * MAX_VELOCITY;
                targetScroll = currentScroll + (velocity / LERP_FACTOR);
                currentScroll += velocity;
            } else {
                if (isSnapping) {
                    const snapDiff = snapTarget - currentScroll;
                    velocity = snapDiff * 0.15;
                    currentScroll += velocity;
                    if (Math.abs(velocity) < 0.1 && Math.abs(snapDiff) < 0.5) {
                        isPhysicsActive = false;
                        velocity = 0;
                        currentScroll = snapTarget;
                        resetIdle();
                    }
                } else {
                    currentScroll += velocity;
                    velocity *= FRICTION;
                    if (Math.abs(velocity) < SNAP_THRESHOLD) {
                        isSnapping = true;
                        const firstCard = slider.querySelector('a');
                        const stepSize = (firstCard ? firstCard.offsetWidth : 360) + 20;
                        const rawIndex = currentScroll / stepSize;
                        let snappedIndex = Math.round(rawIndex);
                        const maxIndex = slider.querySelectorAll('a').length - 1;
                        if (snappedIndex < 0) snappedIndex = 0;
                        if (snappedIndex > maxIndex) snappedIndex = maxIndex;
                        snapTarget = snappedIndex * stepSize;
                    }
                }
            }
            slider.scrollLeft = currentScroll;
        } else {
            if (Math.abs(slider.scrollLeft - currentScroll) > 1) {
                currentScroll = slider.scrollLeft;
                targetScroll = slider.scrollLeft;
                resetIdle();
            }
        }
        updateVisuals(slider);
        requestAnimationFrame(render);
    }

    requestAnimationFrame(render);

    slider.addEventListener('mousedown', (e) => {
        resetIdle();
        isDown = true;
        isDragging = false;
        slider.classList.add('active');
        startX = e.pageX;
        currentScroll = slider.scrollLeft;
        targetScroll = currentScroll;
        isPhysicsActive = true;
    });

    slider.addEventListener('mouseleave', () => {
        isDown = false;
        slider.classList.remove('active');
    });

    slider.addEventListener('mouseup', () => {
        isDown = false;
        slider.classList.remove('active');
    });

    slider.addEventListener('mousemove', (e) => {
        if (!isDown) return;
        e.preventDefault();
        isDragging = true;
        const x = e.pageX;
        const walk = (x - startX) * SENSITIVITY;
        targetScroll = currentScroll - walk;
    });

    // Touch Events
    slider.addEventListener('touchstart', (e) => {
        resetIdle();
        isDown = true;
        isDragging = false;
        slider.classList.add('active');
        startX = e.touches[0].pageX;
        currentScroll = slider.scrollLeft;
        targetScroll = currentScroll;
        isPhysicsActive = true;
    }, { passive: true });

    slider.addEventListener('touchend', () => {
        isDown = false;
        slider.classList.remove('active');
    });

    slider.addEventListener('touchmove', (e) => {
        if (!isDown) return;
        // Prevent page scroll while swiping
        // Using passive: false to allow this
        e.preventDefault();

        const x = e.touches[0].pageX;
        const walk = (x - startX) * SENSITIVITY;

        // Lock scroll if mostly horizontal
        // Simple approach: always prevent default if moving horizontally? 
        // For better UX, we'd calculate slope. 
        // But for this fix, we'll rely on CSS touch-action if possible, or just preventDefault.
        // Since we are not changing CSS, let's just implement the logic.
        // Note: 'passive: false' is needed to use preventDefault()

        isDragging = true;
        targetScroll = currentScroll - walk;
    }, { passive: false });

    window.addEventListener('resize', () => requestAnimationFrame(() => updateVisuals(slider)));

    const items = slider.querySelectorAll('a');
    items.forEach(link => {
        link.addEventListener('click', (e) => {
            if (isDragging) {
                e.preventDefault();
                e.stopPropagation();
                return;
            }
            if (!link.classList.contains('active-card')) {
                e.preventDefault();
                const targetCenter = link.offsetLeft + (link.offsetWidth / 2);
                const containerCenter = slider.offsetWidth / 2;
                targetScroll = targetCenter - containerCenter;
                isPhysicsActive = true;
                resetIdle();
            }
        });
    });

    slider.scrollLeft = 0;
}

function updateVisuals(slider) {
    const center = slider.scrollLeft + (slider.offsetWidth / 2);
    const items = slider.querySelectorAll('a');

    items.forEach(item => {
        const itemCenter = item.offsetLeft + (item.offsetWidth / 2);
        const distance = (center - itemCenter);
        const absDist = Math.abs(distance);
        const maxDist = slider.offsetWidth / 2;

        let scale = 1, rotate = 0, zIndex = 0, opacity = 1, translateX = 0;

        if (absDist < maxDist) {
            const effect = 1 - (absDist / maxDist);
            scale = 0.8 + (effect * 0.2);
            opacity = 0.5 + (effect * 0.5);
            zIndex = Math.floor(effect * 100);
            const overlap = 190 * (1 - effect);

            if (distance > 0) {
                rotate = 45 * (1 - effect);
                translateX = overlap;
            } else {
                rotate = -45 * (1 - effect);
                translateX = -overlap;
            }
        } else {
            scale = 0.8; opacity = 0.5; zIndex = 0;
            const overlap = 190;
            if (distance > 0) {
                rotate = 45; translateX = overlap;
            } else {
                rotate = -45; translateX = -overlap;
            }
        }

        if (absDist < 40) {
            item.classList.add('active-card');
            rotate = 0; translateX = 0; opacity = 1; scale = 1.05; zIndex = 200;
        } else {
            item.classList.remove('active-card');
        }

        item.style.transform = `translateX(${translateX}px) scale(${scale}) rotateY(${rotate}deg)`;
        item.style.opacity = opacity;
        item.style.zIndex = zIndex;
    });
}

// 3. Form Handling (IIFE)
(function () {
    const nameInput = document.getElementById('mail_name');
    if (!nameInput) return; // Guard if not present
    const instInput = document.getElementById('mail_institution');
    const phoneInput = document.getElementById('mail_phone');
    const divInst = document.getElementById('div-institution');
    const divPhone = document.getElementById('div-phone');
    const divEmail = document.getElementById('div-email');

    function handleReveal(input, targetDiv, nextOverflowDiv = null) {
        if (input.value.trim().length > 0) {
            targetDiv.classList.add('active');
            if (nextOverflowDiv) {
                setTimeout(() => {
                    nextOverflowDiv.classList.add('overflow-visible');
                }, 500);
            }
        }
    }

    nameInput.addEventListener('input', () => handleReveal(nameInput, divInst));
    instInput.addEventListener('input', () => handleReveal(instInput, divPhone, divPhone));

    phoneInput.addEventListener('input', (e) => {
        if (divEmail) handleReveal(phoneInput, divEmail);
        const target = e.target;
        let number = target.value.replace(/[^0-9]/g, '');
        let formatted = '';
        if (number.length < 4) {
            formatted = number;
        } else if (number.length < 8) {
            formatted = number.slice(0, -4) + '-' + number.slice(-4);
            if (number.slice(0, -4) === '') formatted = number.slice(-4);
        } else {
            const last4 = number.slice(-4);
            const mid4 = number.slice(-8, -4);
            const prefix = number.slice(0, -8);
            formatted = (prefix ? prefix + '-' : '') + mid4 + '-' + last4;
        }
        if (target.value !== formatted) target.value = formatted;
    });
})();

// 4. EmailJS Init (IIFE)
(function () {
    // emailjs.init("YOUR_PUBLIC_KEY");
})();

// 5. Partners Filter
function filterPartners(category) {
    const buttons = document.querySelectorAll('.category-btn');
    const logos = document.querySelectorAll('.partner-logo');
    let isSameClicked = false;
    buttons.forEach(btn => {
        if (btn.innerText === event.target.innerText && btn.classList.contains('active')) {
            isSameClicked = true;
        }
        btn.classList.remove('active');
    });
    if (isSameClicked) {
        logos.forEach(logo => logo.classList.add('hidden'));
        return;
    }
    event.target.classList.add('active');
    logos.forEach(logo => {
        if (logo.dataset.category === category || category === 'all') {
            logo.classList.remove('hidden');
        } else {
            logo.classList.add('hidden');
        }
    });
}

// 6. Custom Dropdown
document.addEventListener('DOMContentLoaded', function () {
    var x, i, j, l, ll, selElmnt, a, b, c;
    const selectedDiv = document.querySelector(".select-selected");
    const itemsDiv = document.querySelector(".select-items");
    if (!selectedDiv) return;

    const hiddenInput = document.getElementById("country_code");
    const options = itemsDiv.getElementsByTagName("div");

    selectedDiv.addEventListener("click", function (e) {
        e.stopPropagation();
        closeAllSelect(this);
        this.nextElementSibling.classList.toggle("select-hide");
        this.classList.toggle("select-arrow-active");
    });

    for (let i = 0; i < options.length; i++) {
        options[i].addEventListener("click", function (e) {
            e.stopPropagation();
            const value = this.getAttribute("data-value");
            const text = this.innerText;
            selectedDiv.innerHTML = text;
            hiddenInput.value = value;
            selectedDiv.classList.add("active");
            const siblings = this.parentNode.children;
            for (let k = 0; k < siblings.length; k++) {
                siblings[k].classList.remove("same-as-selected");
            }
            this.classList.add("same-as-selected");
            itemsDiv.classList.add("select-hide");
            selectedDiv.classList.remove("select-arrow-active");
        });
    }

    function closeAllSelect(elmnt) {
        if (elmnt == selectedDiv) return;
        itemsDiv.classList.add("select-hide");
        selectedDiv.classList.remove("select-arrow-active");
    }

    document.addEventListener("click", closeAllSelect);
});

// 7. Menu Toggle
// Wrapped in DOMContentLoaded or at end of body in script.js to ensure element exists
document.addEventListener("DOMContentLoaded", () => {
    const toggle = document.querySelector('.menu-toggle');
    if (toggle) {
        toggle.addEventListener('click', function () {
            document.querySelector('.nav').classList.toggle('active');
        });
    }
});
