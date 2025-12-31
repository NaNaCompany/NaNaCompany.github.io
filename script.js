
// 1. RSS Fetching & Rendering
document.addEventListener("DOMContentLoaded", async () => {
    const container = document.getElementById("blog-list");
    const url = "https://api.nanalab.kr/rss";

    const fallbackThumb = "https://via.placeholder.com/240x144?text=Blog";

    try {
        const raw = await fetch(url).then(r => r.text());
        const parser = new DOMParser();
        const xmlDoc = parser.parseFromString(raw, "text/xml");
        const items = Array.from(xmlDoc.querySelectorAll("item"));

        const validItems = items.map(item => {
            const title = item.querySelector("title")?.textContent || "";
            const link = item.querySelector("link")?.textContent || "";
            const pubDate = item.querySelector("pubDate")?.textContent || "";
            const description = item.querySelector("description")?.textContent || "";

            let isoDate = "";
            if (pubDate) {
                try {
                    isoDate = new Date(pubDate).toISOString().slice(0, 10);
                } catch (e) { /* ignore */ }
            }

            let thumb = fallbackThumb;
            // Try to find an image in description
            const imgMatch = description.match(/<img[^>]+src="([^">]+)"/);
            if (imgMatch) {
                thumb = imgMatch[1];
            }

            return { title, link, date: isoDate, thumb };
        }).slice(0, 15); // Take top 15

        container.innerHTML = "";
        if (validItems.length === 0) console.warn("No items parsed from RSS proxy");

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

        // Add "More Apps" Card
        const moreAppsLink = document.createElement("a");
        moreAppsLink.href = "https://nanalab.kr/apps";
        moreAppsLink.className = "blog-item blink"; // Add blink class
        moreAppsLink.ondragstart = () => false;
        moreAppsLink.innerHTML = `
            <div class="card more-apps-card">
                <span class="more-text">More Apps...</span>
            </div>
        `;
        container.appendChild(moreAppsLink);

        initCoverFlow(container);

    } catch (e) {
        console.error("RSS parsing error:", e);
        container.innerHTML = `<p style="text-align:center; width:100%;">Failed to load apps: ${e.message}</p>`;
    }
});

// 2. Cover Flow Physics
function initCoverFlow(slider) {
    // Initial update
    updateVisuals(slider);

    // Update visuals on native scroll
    slider.addEventListener('scroll', () => {
        requestAnimationFrame(() => updateVisuals(slider));
    }, { passive: true });

    // Update on resize
    window.addEventListener('resize', () => {
        requestAnimationFrame(() => updateVisuals(slider));
    });

    // Optional: Center the first card initially or restore position if needed
    // slider.scrollLeft = 0; 
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
