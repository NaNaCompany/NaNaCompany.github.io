// Exercise the directory's event handlers without a browser or network.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const apps = JSON.parse(fs.readFileSync(path.join(root, 'content/apps.json'), 'utf8'));
function element(data = {}, text = '') {
    const handlers = {};
    const classes = new Set();
    return {
        dataset: data, textContent: text, hidden: false, value: '', attributes: {},
        classList: {toggle(c, force) { const active = force ?? !classes.has(c); active ? classes.add(c) : classes.delete(c); return active; }, remove(c) { classes.delete(c); }},
        addEventListener(name, callback) { handlers[name] = callback; },
        emit(name, event = {}) { handlers[name]?.(event); },
        setAttribute(name, value) { this.attributes[name] = value; },
        focus() { this.focused = true; }
    };
}
function setup(archive = false, localized = false) {
    const cards = archive ? [] : apps.map(app => element({category:app.category}, `${app.name} ${app.description}`));
    const filters = archive ? [] : ['all', ...new Set(apps.map(app => app.category))].map(category => element({filter:category}));
    const entries = archive ? [element({category:'교육기관'}, '홍익대학교 2026 AI Agent'), element({category:'기업'}, 'LG인화원 업무 자동화')] : [];
    const lectureFilters = archive ? ['전체','기업','교육기관','공공기관'].map(category => element({lectureCategory:category})) : [];
    const ids = archive
        ? {'archive-search':element(), 'archive-count':element()}
        : {'app-search':element(), 'result-count':element(), 'empty-results':element(), 'reset-filters':element()};
    if (localized) {
        const buttons = archive ? lectureFilters : filters;
        buttons.forEach(button => { button.dataset.label = archive ? (button.dataset.lectureCategory === '기업' ? 'Companies' : 'All') : (button.dataset.filter === 'all' ? 'All' : 'Category'); });
        ids[archive ? 'archive-count' : 'result-count'].dataset.template = archive ? '{label}: {count} · newest first' : '{label}: {count}';
    }
    const domReady = [];
    const languageMenu = localized ? element() : null;
    const languageLinks = localized ? [element(),element()] : [];
    const window = {location:{hash:'#app-search'}};
    const document = {
        getElementById: id => ids[id] || null,
        querySelector: selector => selector === '.language-menu' ? languageMenu : null,
        querySelectorAll: selector => ({'.directory-card':cards, '[data-filter]':filters, '.singleLectureContainer':entries, '[data-lecture-category]':lectureFilters, '.language-menu a':languageLinks}[selector] || []),
        addEventListener(name, callback) { if (name === 'DOMContentLoaded') domReady.push(callback); }
    };
    vm.runInNewContext(fs.readFileSync(path.join(root, 'script.js'), 'utf8'), {document, window, setTimeout, console});
    domReady.forEach(callback => callback());
    return {cards, filters, entries, ids, lectureFilters, languageLinks, languageMenu, window};
}
const {cards, filters, ids} = setup();
ids['app-search'].value = 'PDF';
ids['app-search'].emit('input');
assert.equal(cards.filter(card => !card.hidden).length, apps.filter(app => `${app.name} ${app.description}`.toLowerCase().includes('pdf')).length);
filters.find(filter => filter.dataset.filter === '이미지·미디어').emit('click');
assert.equal(cards.filter(card => !card.hidden).length, 0);
assert.equal(ids['empty-results'].hidden, false);
ids['reset-filters'].emit('click');
assert.equal(cards.filter(card => !card.hidden).length, apps.length);
assert.equal(ids['app-search'].value, '');
assert.equal(ids['app-search'].focused, true);
assert.equal(filters[0].attributes['aria-pressed'], 'true');
filters.find(filter => filter.dataset.filter === 'AI·개발').emit('click');
assert.equal(cards.filter(card => !card.hidden).length, 4);
ids['app-search'].value = 'astra';
ids['app-search'].emit('input');
assert.equal(cards.filter(card => !card.hidden).length, 1);
const archive = setup(true);
archive.ids['archive-search'].value = '홍익';
archive.ids['archive-search'].emit('input');
assert.equal(archive.entries.filter(card => !card.hidden).length, 1);
assert.equal(archive.ids['archive-count'].textContent, '전체 1건 · 최신 강의순');
archive.lectureFilters.find(button => button.dataset.lectureCategory === '기업').emit('click');
assert.equal(archive.entries.filter(card => !card.hidden).length, 0);
archive.ids['archive-search'].value = '';
archive.ids['archive-search'].emit('input');
assert.equal(archive.entries.filter(card => !card.hidden).length, 1);
assert.equal(archive.ids['archive-count'].textContent, '기업 1건 · 최신 강의순');
assert.equal(archive.lectureFilters.find(button => button.dataset.lectureCategory === '기업').attributes['aria-pressed'], 'true');
const english = setup(false, true);
english.ids['app-search'].value = 'astra';
english.ids['app-search'].emit('input');
assert.equal(english.ids['result-count'].textContent, 'All: 1');
assert.equal(english.languageLinks[0].hash, '#app-search');
english.window.location.hash = '#result-count';
english.languageMenu.emit('toggle');
assert.equal(english.languageLinks[0].hash, '#result-count');
english.window.location.hash = '#google_vignette';
english.languageMenu.emit('toggle');
assert.equal(english.languageLinks[0].hash, '');
const englishArchive = setup(true, true);
englishArchive.lectureFilters.find(button => button.dataset.lectureCategory === '기업').emit('click');
assert.equal(englishArchive.ids['archive-count'].textContent, 'Companies: 1 · newest first');
console.log('PASS: search, combined category filter, empty state, reset, accessible filter state, archive search, localized counts and category labels');
