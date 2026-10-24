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
function setup(archive = false) {
    const cards = archive ? [] : apps.map(app => element({category:app.category}, `${app.name} ${app.description}`));
    const filters = archive ? [] : ['all', ...new Set(apps.map(app => app.category))].map(category => element({filter:category}));
    const entries = archive ? [element({}, '홍익대학교 2026 AI Agent'), element({}, 'LG인화원 업무 자동화')] : [];
    const ids = archive
        ? {'archive-search':element(), 'archive-count':element()}
        : {'app-search':element(), 'result-count':element(), 'empty-results':element(), 'reset-filters':element()};
    const domReady = [];
    const document = {
        getElementById: id => ids[id] || null,
        querySelector: () => null,
        querySelectorAll: selector => ({'.directory-card':cards, '[data-filter]':filters, '.singleLectureContainer':entries}[selector] || []),
        addEventListener(name, callback) { if (name === 'DOMContentLoaded') domReady.push(callback); }
    };
    vm.runInNewContext(fs.readFileSync(path.join(root, 'script.js'), 'utf8'), {document, setTimeout, console});
    domReady.forEach(callback => callback());
    return {cards, filters, entries, ids};
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
assert.equal(cards.filter(card => !card.hidden).length, 3);
ids['app-search'].value = 'astra';
ids['app-search'].emit('input');
assert.equal(cards.filter(card => !card.hidden).length, 1);
const archive = setup(true);
archive.ids['archive-search'].value = '홍익';
archive.ids['archive-search'].emit('input');
assert.equal(archive.entries.filter(card => !card.hidden).length, 1);
assert.equal(archive.ids['archive-count'].textContent, '1건의 강연');
console.log('PASS: search, combined category filter, empty state, reset, accessible filter state, archive search');
