"""Check feed/API consistency, identities, dates, escaping and deep links."""
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlsplit
import json
import xml.etree.ElementTree as ET

from build_site import build, Cards
from syndication import SITE, Record, record_identity, dated, feeds, order, anchor_cards

ROOT = Path(__file__).resolve().parents[1]


def check():
    outputs, counts = build()
    assert build()[0] == outputs, 'Build is not deterministic'
    catalogs = {key: json.loads(outputs['api/' + key + '.json'])
                for key in ['apps', 'lectures', 'papers', 'patents', 'projects', 'research']}
    expected = {'apps': counts['apps'], 'lectures': counts['lectures'], 'papers': counts['papers'],
                'patents': counts['patents'], 'projects': counts['websites'],
                'research': sum(counts[k] for k in ['papers', 'patents', 'websites'])}
    for key, catalog in catalogs.items():
        rows = catalog['items']
        assert catalog['count'] == len(rows) == expected[key], key
        assert len({row['id'] for row in rows}) == len(rows), key
        assert rows == sorted(rows, key=order, reverse=True), key
        assert 'repository_path' not in outputs['api/' + key + '.json'], 'Local path exposed'
        for row in rows:
            assert row['id'] and row['title'] and row['source_url'] and row['summary'], row['id']
            if row['section'] != 'apps':
                parts = urlsplit(row['url'])
                assert parts.netloc == 'nanalab.kr' and parts.fragment, row['id']
                html = outputs[parts.path.lstrip('/') + 'index.html']
                assert f'id="{parts.fragment}"' in html, row['url']
            if row['date_precision'] in {'year', 'unknown'}:
                assert 'date_published' not in row, 'Invented exact publication date'
    catalog_index = json.loads(outputs['api/index.json'])
    assert catalog_index['total_count'] == sum(expected[k] for k in expected if k != 'research')
    for key, info in catalog_index['catalogs'].items():
        assert info['count'] == expected[key]
    known = {'urn:nanalab:' + row['section'] + ':' + row['id']: row
             for key, catalog in catalogs.items() if key != 'research' for row in catalog['items']}
    feed_counts = {}
    for path in ['/feed', '/feeds/apps', '/feeds/lectures', '/feeds/research']:
        feed = json.loads(outputs[path.lstrip('/') + '.json'])
        rss = ET.fromstring(outputs[path.lstrip('/') + '.xml'])
        assert rss.tag == 'rss' and rss.attrib == {'version': '2.0'}
        channel = rss.find('channel')
        assert all(channel.findtext(k) for k in ['title', 'link', 'description'])
        assert feed['version'] == 'https://jsonfeed.org/version/1.1'
        assert feed['feed_url'] == SITE + path + '.json'
        assert channel.find('{http://www.w3.org/2005/Atom}link').attrib['href'] == SITE + path + '.xml'
        items = channel.findall('item')
        assert len(items) == len(feed['items']) and len(items) <= (200 if path == '/feed' else 100)
        ids = [item['id'] for item in feed['items']]
        assert len(ids) == len(set(ids)) and set(ids) <= known.keys()
        for xml_item, item in zip(items, feed['items']):
            assert xml_item.findtext('guid') == item['id']
            assert xml_item.find('guid').attrib == {'isPermaLink': 'false'}
            assert xml_item.findtext('title') == item['title']
            assert xml_item.findtext('link') == item['url']
            assert xml_item.findtext('description') == item['content_text']
            assert item['content_text'] and item['url'].startswith('https://')
            if item.get('date_published'):
                date = datetime.fromisoformat(item['date_published'].replace('Z', '+00:00'))
                assert parsedate_to_datetime(xml_item.findtext('pubDate')) == date
            else:
                assert xml_item.find('pubDate') is None
            row = known[item['id']]
            if row.get('publication_type') == 'preprint':
                assert '프리프린트' in item['title'] and 'preprint' in item['content_text']
        feed_counts[path] = len(items)
    for path, rows in [('feed', list(known.values())), ('feeds/apps', catalogs['apps']['items']),
                       ('feeds/lectures', catalogs['lectures']['items']), ('feeds/research', catalogs['research']['items'])]:
        expected_rows = sorted(rows, key=order, reverse=True)[:200 if path == 'feed' else 100]
        assert [i['id'] for i in json.loads(outputs[path + '.json'])['items']] == [
            'urn:nanalab:' + row['section'] + ':' + row['id'] for row in expected_rows], path
    for path, text in outputs.items():
        assert (ROOT / path).read_text(encoding='utf-8') == text, 'Stale output: ' + path
        if path.endswith('.html'):
            assert 'type="application/rss+xml"' in text and 'type="application/feed+json"' in text, path
    # Exact source IDs survive title/description edits. Entities round-trip in XML/JSON.
    fixture = '<div data-record-id="fixture"><h5>A &amp; B &lt; C</h5><p class="abstract">One <strong>nested</strong> value.</p></div>'
    original = Record(fixture)
    assert original.fields['title'] == 'A & B < C'
    assert original.fields['abstract'] == 'One nested value.'
    assert record_identity('papers', original) == record_identity('papers', Record(fixture.replace('value', 'updated')))
    legacy = '<!-- version A --><div class="singleProjectContainer"><h5>Same URL</h5></div><!-- version B --><div class="singleProjectContainer"><h5>Same URL</h5></div>'
    one, two = Cards(legacy).cards
    assert Record(one).attrs['data-record-id'] != Record(two).attrs['data-record-id']
    assert anchor_cards('websites', [one, two]) == list(reversed(anchor_cards('websites', [two, one])))
    year_only = {}
    dated(year_only, '2026년')
    assert year_only == {'date_precision': 'year', 'date_text': '2026년', 'year': 2026}
    sample = {'id': 'fixture', 'section': 'papers', 'title': 'A & B < C', 'summary': 'X < Y & Z',
              'url': SITE + '/papers/', 'source_url': SITE}
    escaped = feeds([sample], 'Test & <feed>', '/test', '/')
    assert ET.fromstring(escaped['test.xml']).findtext('channel/item/description') == json.loads(escaped['test.json'])['items'][0]['content_text']
    print(json.dumps({'status': 'passed', 'catalogs': expected, 'feed_items': feed_counts,
                      'checks': ['determinism', 'stable unique IDs', 'source dates', 'deep links',
                                 'RSS/JSON Feed parity', 'escaping', 'attribution', 'freshness']}, ensure_ascii=False))


if __name__ == '__main__':
    check()
