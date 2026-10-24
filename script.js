// App directory: server-rendered cards remain available without JavaScript.
document.addEventListener('DOMContentLoaded', () => {
    const search = document.getElementById('app-search');
    const cards = [...document.querySelectorAll('.directory-card')];
    const filters = [...document.querySelectorAll('[data-filter]')];
    let selected = 'all';
    function update() {
        const query = search.value.trim().normalize('NFKC').toLocaleLowerCase();
        let count = 0;
        cards.forEach(card => {
            const matches = (selected === 'all' || card.dataset.category === selected)
                && `${card.textContent} ${card.dataset.appId || ''}`.normalize('NFKC').toLocaleLowerCase().includes(query);
            card.hidden = !matches;
            if (matches) count++;
        });
        document.getElementById('result-count').textContent = `${selected === 'all' ? '전체' : selected} ${count}개`;
        document.getElementById('empty-results').hidden = count !== 0;
        filters.forEach(button => {
            const active = button.dataset.filter === selected;
            button.classList.toggle('active', active);
            button.setAttribute('aria-pressed', String(active));
        });
    }
    if (search) {
        search.addEventListener('input', update);
        filters.forEach(button => button.addEventListener('click', () => {
            selected = button.dataset.filter;
            update();
        }));
        document.getElementById('reset-filters').addEventListener('click', () => {
            selected = 'all';
            search.value = '';
            update();
            search.focus();
        });
        document.addEventListener('keydown', event => {
            if (event.key === '/' && !event.ctrlKey && !event.metaKey && !event.altKey
                && !event.target.closest('input,textarea,select,[contenteditable]')) {
                event.preventDefault();
                search.focus();
            }
        });
    }
    const menu = document.querySelector('.directory-menu');
    const nav = document.getElementById('main-nav');
    if (menu && nav) {
        const close = () => { nav.classList.remove('open'); menu.setAttribute('aria-expanded', 'false'); };
        menu.addEventListener('click', () => {
            const open = nav.classList.toggle('open');
            menu.setAttribute('aria-expanded', String(open));
        });
        nav.addEventListener('click', event => { if (event.target.closest('a')) close(); });
        document.addEventListener('keydown', event => { if (event.key === 'Escape') close(); });
    }
    document.querySelectorAll('.card-visual img').forEach(img => {
        img.addEventListener('error', () => { img.hidden = true; });
    });
    const archiveSearch = document.getElementById('archive-search');
    if (archiveSearch) {
        const entries = [...document.querySelectorAll('.singleLectureContainer')];
        const categoryButtons = [...document.querySelectorAll('[data-lecture-category]')];
        let lectureCategory = '전체';
        const filterArchive = () => {
            const query = archiveSearch.value.trim().normalize('NFKC').toLocaleLowerCase();
            let count = 0;
            entries.forEach(card => {
                card.hidden = (lectureCategory !== '전체' && card.dataset.category !== lectureCategory)
                    || !card.textContent.normalize('NFKC').toLocaleLowerCase().includes(query);
                if (!card.hidden) count++;
            });
            document.getElementById('archive-count').textContent = `${lectureCategory} ${count}건 · 최신 강의순`;
            categoryButtons.forEach(button => {
                const active = button.dataset.lectureCategory === lectureCategory;
                button.classList.toggle('active', active);
                button.setAttribute('aria-pressed', String(active));
            });
            const empty = document.getElementById('lecture-empty');
            if (empty) empty.hidden = count !== 0;
        };
        categoryButtons.forEach(button => button.addEventListener('click', () => {
            lectureCategory = button.dataset.lectureCategory;
            filterArchive();
        }));
        archiveSearch.addEventListener('input', filterArchive);
        filterArchive();
    }
});

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
