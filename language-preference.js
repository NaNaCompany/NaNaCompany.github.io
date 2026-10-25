/* Directory language preference. Static translations remain usable without JS. */
(() => {
    'use strict';
    const languages = ['ko', 'en', 'ja', 'zh', 'es', 'de', 'fr', 'pt', 'ru'];
    const routes = ['', 'apps', 'lectures', 'research', 'papers', 'patents', 'projects', 'feeds'];
    const preferenceKey = 'nanalab-directory-language';
    const countryKey = 'nanalab-directory-country';
    const current = new URL(window.location.href);
    const language = document.documentElement.lang;
    const segments = current.pathname.split('/').filter(Boolean);
    if (language !== 'ko' && segments[0] === language) segments.shift();
    const route = segments.join('/');
    if (!languages.includes(language) || !routes.includes(route)) return;

    const pathFor = code => '/' + [code === 'ko' ? '' : code, route].filter(Boolean).join('/')
        + (code !== 'ko' || route ? '/' : '');
    // Do not affect app repositories or alternate /index.html URLs.
    if (current.pathname !== pathFor(language)) return;

    const read = (storage, key) => {
        try { return window[storage].getItem(key); } catch { return null; }
    };
    const write = (storage, key, value) => {
        try { window[storage].setItem(key, value); } catch { /* Storage is optional. */ }
    };
    const savedLanguage = () => [read('localStorage', preferenceKey), read('sessionStorage', preferenceKey)]
        .find(value => languages.includes(value));
    const remember = code => {
        write('localStorage', preferenceKey, code);
        write('sessionStorage', preferenceKey, code);
    };
    let manuallySelected = false;
    let controller;

    document.querySelectorAll('.language-menu a[hreflang]').forEach(link => {
        const code = link.hreflang;
        if (!languages.includes(code)) return;
        const target = new URL(link.href, current);
        target.search = current.search;
        target.searchParams.delete('lang');
        // Explicit Korean links work even with blocked storage or in a new tab.
        if (code === 'ko') target.searchParams.set('lang', 'ko');
        link.href = target.pathname + target.search + target.hash;
        const select = () => {
            manuallySelected = true;
            remember(code);
            if (controller) controller.abort();
        };
        link.addEventListener('click', select);
        link.addEventListener('auxclick', event => { if (event.button === 1) select(); });
    });

    if (current.searchParams.get('lang') === language) {
        remember(language);
        current.searchParams.delete('lang');
        try { window.history.replaceState(window.history.state, '', current.pathname + current.search + current.hash); } catch { /* Navigation still works. */ }
        return;
    }
    // Explicit /en/, /ja/, etc. URLs are authoritative, including shared links.
    if (language !== 'ko') return;

    const redirect = code => {
        if (manuallySelected || code === language || !languages.includes(code)) return;
        const target = new URL(current);
        target.pathname = pathFor(code);
        target.searchParams.delete('lang');
        let fragment = target.hash.slice(1);
        try { fragment = decodeURIComponent(fragment); } catch { fragment = ''; }
        if (!fragment || !document.getElementById(fragment)) target.hash = '';
        window.location.replace(target.href);
    };
    const saved = savedLanguage();
    if (saved) { redirect(saved); return; }

    const browserLanguages = (navigator.languages?.length ? navigator.languages : [navigator.language])
        .map(value => String(value || '').toLowerCase().split(/[-_]/)[0]);
    const browserLanguage = choices => browserLanguages.find(code => choices.includes(code));
    const countryGroups = {
        ko: 'KR KP', ja: 'JP', zh: 'CN TW HK MO',
        es: 'ES MX AR BO CL CO CR CU DO EC SV GQ GT HN NI PA PY PE PR UY VE',
        de: 'DE AT LI', fr: 'FR MC BF BI BJ CD CF CG CI CM DJ GA GN HT MG ML NE SN TD TG',
        pt: 'PT BR AO CV GW MZ ST TL', ru: 'RU BY KZ KG',
        en: 'US GB IE AU NZ'
    };
    const multilingual = {CA: ['en', 'fr'], CH: ['de', 'fr'], BE: ['fr', 'de'], LU: ['fr', 'de'], SG: ['en', 'zh']};
    const recommend = country => {
        if (multilingual[country]) return browserLanguage(multilingual[country]) || multilingual[country][0];
        return Object.keys(countryGroups).find(code => countryGroups[code].split(' ').includes(country))
            || browserLanguage(languages) || 'en';
    };
    const validCountry = value => typeof value === 'string' && /^[A-Z]{2}$/.test(value);

    const detectCountry = async () => {
        try {
            const cached = JSON.parse(read('sessionStorage', countryKey));
            const age = Date.now() - cached?.time;
            if (validCountry(cached?.country) && age >= 0 && age < 3600000) return cached.country;
        } catch { /* Ignore invalid or inaccessible cache. */ }
        let timer;
        try {
            if (typeof AbortController !== 'undefined') controller = new AbortController();
            const timeout = new Promise(resolve => {
                timer = setTimeout(() => { if (controller) controller.abort(); resolve(''); }, 2200);
            });
            // Same-origin Cloudflare endpoint. Retain only its country code;
            // never store the IP/trace body or contact an external GeoIP service.
            const lookup = fetch('/cdn-cgi/trace', {
                mode: 'same-origin', credentials: 'omit', redirect: 'error',
                cache: 'no-store', referrerPolicy: 'no-referrer', signal: controller?.signal
            }).then(response => response.ok ? response.text() : '')
                .then(trace => /^loc=([A-Z]{2})\r?$/m.exec(trace)?.[1] || '');
            const country = await Promise.race([lookup, timeout]);
            if (country) write('sessionStorage', countryKey, JSON.stringify({country, time: Date.now()}));
            return country;
        } catch { return ''; }
        finally { clearTimeout(timer); }
    };
    void detectCountry().then(country => redirect(savedLanguage() || recommend(country)));
})();
