/* Navigation regression checks using real browser-script code and mocked I/O. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '../language-preference.js'), 'utf8');
const languages = ['ko', 'en', 'ja', 'zh', 'es', 'de', 'fr', 'pt', 'ru'];
const preferenceKey = 'nanalab-directory-language';
const countryKey = 'nanalab-directory-country';
const flush = () => new Promise(resolve => setImmediate(resolve));

function visit(options = {}) {
    const current = new URL(options.url || 'https://nanalab.kr/');
    const language = options.language || 'ko';
    const route = current.pathname.replace(new RegExp('^/' + (language === 'ko' ? '' : language + '/')), '').replace(/\/$/, '');
    const links = languages.map(code => ({
        hreflang: code,
        href: '/' + [code === 'ko' ? '' : code, route].filter(Boolean).join('/') + (code !== 'ko' || route ? '/' : ''),
        handlers: {},
        addEventListener(name, fn) { this.handlers[name] = fn; }
    }));
    const local = new Map(options.saved ? [[preferenceKey, options.saved]] : []);
    const session = new Map(options.cache ? [[countryKey, options.cache]] : []);
    const storage = (map, blocked) => ({
        getItem(key) { if (blocked) throw Error('Storage blocked'); return map.get(key) ?? null; },
        setItem(key, value) { if (blocked) throw Error('Storage blocked'); map.set(key, value); }
    });
    const redirects = [], history = [], requests = [], timers = new Map();
    let resolveRequest;
    const window = {
        location: {href: current.href, replace: href => redirects.push(href)},
        localStorage: storage(local, options.blocked),
        sessionStorage: storage(session, options.blocked),
        history: {state: null, replaceState: (_state, _title, href) => history.push(href)}
    };
    vm.runInNewContext(source, {
        window, URL, AbortController: options.noAbortController ? undefined : AbortController,
        navigator: {languages: options.browser || ['ko-KR'], language: 'ko-KR'},
        document: {
            documentElement: {lang: language},
            querySelectorAll: () => links,
            getElementById: id => ['apps', 'app-search', 'lecture-1', '강의'].includes(id) ? {} : null
        },
        setTimeout(fn, duration) { assert.equal(duration, 2200); const id = Symbol(); timers.set(id, fn); return id; },
        clearTimeout: id => timers.delete(id),
        fetch: (url, config) => {
            requests.push({url, config});
            assert.equal(url, '/cdn-cgi/trace', 'Lookup must stay on this site');
            assert.equal(config.mode, 'same-origin');
            assert.equal(config.redirect, 'error');
            assert.equal(config.credentials, 'omit');
            assert.equal(config.cache, 'no-store');
            assert.equal(config.referrerPolicy, 'no-referrer');
            if (options.error) return Promise.reject(Error('Network unavailable'));
            if (options.pending) return new Promise(resolve => { resolveRequest = resolve; });
            return Promise.resolve({ok: options.ok !== false, text: () => options.pendingBody ? new Promise(() => {}) : Promise.resolve(options.trace ?? 'loc=KR\n')});
        }
    });
    return {links, local, session, redirects, history, requests, timers,
        finish: trace => resolveRequest({ok: true, text: async () => trace}),
        timeout: () => [...timers.values()].forEach(fn => fn())};
}

(async () => {
    // IP overrides browser language for supported country groups.
    for (const [country, code] of [['KR','ko'],['JP','ja'],['US','en'],['CN','zh'],['MX','es'],['DE','de'],['FR','fr'],['BR','pt'],['RU','ru']]) {
        const page = visit({url: 'https://nanalab.kr/lectures/?utm_source=test#lecture-1', trace: 'colo=ICN\r\nloc=' + country + '\r\n'});
        await flush();
        assert.deepEqual(page.redirects, code === 'ko' ? [] : ['https://nanalab.kr/' + code + '/lectures/?utm_source=test#lecture-1']);
        assert.deepEqual(Object.keys(JSON.parse(page.session.get(countryKey))).sort(), ['country', 'time']);
        assert.equal(page.timers.size, 0);
    }
    for (const [country, browser, code] of [['CA',['fr-CA'],'fr'],['CH',['de-CH'],'de'],['BE',['nl-BE'],'fr'],['SG',['zh-SG'],'zh'],['IN',['ta-IN','ja-JP'],'ja']]) {
        const page = visit({trace: 'loc=' + country, browser}); await flush();
        assert.deepEqual(page.redirects, ['https://nanalab.kr/' + code + '/']);
    }
    for (const options of [{error:true},{ok:false},{trace:'<html>unavailable</html>'},{trace:'loc=T1'}]) {
        const page = visit({...options, browser:['ja-JP']}); await flush();
        assert.deepEqual(page.redirects, ['https://nanalab.kr/ja/']);
    }
    const unsupported = visit({error:true,browser:['ar','hi']}); await flush();
    assert.deepEqual(unsupported.redirects, ['https://nanalab.kr/en/']);

    for (const pendingBody of [false, true]) {
        const page = visit({pending:!pendingBody,pendingBody,browser:['fr-FR'],noAbortController:true});
        await flush(); page.timeout(); await flush();
        assert.deepEqual(page.redirects, ['https://nanalab.kr/fr/'], 'Timeout must include body download');
    }
    for (const saved of ['ko','es']) {
        const page = visit({saved}); await flush();
        assert.equal(page.requests.length, 0);
        assert.deepEqual(page.redirects, saved === 'ko' ? [] : ['https://nanalab.kr/es/']);
    }
    for (const language of languages.filter(code => code !== 'ko')) {
        const page = visit({url:'https://nanalab.kr/' + language + '/apps/',language,saved:'ko'}); await flush();
        assert.equal(page.requests.length, 0);
        assert.deepEqual(page.redirects, [], 'Explicit language URL must remain accessible');
    }
    for (const url of ['https://nanalab.kr/astra/', 'https://nanalab.kr/apps/index.html']) {
        const page = visit({url}); await flush();
        assert.equal(page.requests.length, 0); assert.deepEqual(page.redirects, []);
    }
    const cached = visit({cache:JSON.stringify({country:'JP',time:Date.now()})}); await flush();
    assert.equal(cached.requests.length, 0); assert.deepEqual(cached.redirects, ['https://nanalab.kr/ja/']);
    for (const cache of ['broken', JSON.stringify({country:'JP',time:Date.now()-3600001}), JSON.stringify({country:'JP',time:Date.now()+3600000})]) {
        const page = visit({cache}); await flush(); assert.equal(page.requests.length, 1);
    }

    const manual = visit({pending:true});
    manual.links.find(link => link.hreflang === 'fr').handlers.click();
    manual.finish('loc=JP'); await flush();
    assert.deepEqual(manual.redirects, [], 'Late lookup must not override a manual selection');
    assert.equal(manual.local.get(preferenceKey), 'fr');
    assert.equal(manual.requests[0].config.signal.aborted, true);

    const tab = visit({url:'https://nanalab.kr/en/apps/?utm_source=menu',language:'en'});
    assert.equal(tab.links[0].href, '/apps/?utm_source=menu&lang=ko');
    tab.links[0].handlers.auxclick({button:1});
    assert.equal(tab.local.get(preferenceKey), 'ko');
    const korean = visit({url:'https://nanalab.kr/apps/?utm_source=menu&lang=ko#apps',blocked:true,trace:'loc=US'});
    await flush();
    assert.equal(korean.requests.length, 0);
    assert.deepEqual(korean.redirects, []);
    assert.deepEqual(korean.history, ['/apps/?utm_source=menu#apps']);
    const blocked = visit({blocked:true,trace:'loc=JP'}); await flush();
    assert.deepEqual(blocked.redirects, ['https://nanalab.kr/ja/']);
    for (const hash of ['#google_vignette','#%invalid']) {
        const page = visit({url:'https://nanalab.kr/apps/' + hash,saved:'en'}); await flush();
        assert.deepEqual(page.redirects, ['https://nanalab.kr/en/apps/']);
    }
    const encoded = visit({url:'https://nanalab.kr/lectures/#%EA%B0%95%EC%9D%98',saved:'en'}); await flush();
    assert.deepEqual(encoded.redirects, ['https://nanalab.kr/en/lectures/#%EA%B0%95%EC%9D%98']);
    console.log('PASS: 9 IP language choices, multilingual countries, fallback/timeout, cached country, explicit URLs, manual priority, blocked storage, route/query/anchor preservation, same-origin-only lookup.');
})().catch(error => { console.error(error); process.exitCode = 1; });
