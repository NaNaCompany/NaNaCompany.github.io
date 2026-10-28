"""Regression checks for single and multiple leaf sources (no network or build)."""
from contextlib import ExitStack
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import io
import json
import unittest
import xml.etree.ElementTree as ET

import check_sitemaps
import sync_sitemaps
from build_site import sitemap_index, sitemap_robots
from sitemap_sources import (NS, SITE, discover_leaf_urls, flattened_sources,
                             local_sitemap_path, parse_leaf, source_urls, validate_location)

BASE = SITE + 'sample/'


def pages(*urls):
    return ('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' +
            ''.join('<url><loc>' + url + '</loc></url>' for url in urls) + '</urlset>').encode()


class SitemapSourcesTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory(dir=Path(__file__).resolve().parent)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repository = self.root / 'sample'
        self.publish = self.repository / 'docs'
        self.publish.mkdir(parents=True)

    def write(self, name, raw):
        path = self.publish / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        return path

    def multi(self):
        urls = [BASE + name for name in ('sitemap-main.xml', 'posts/one.xml', 'posts/two.xml')]
        for i, location in enumerate(urls):
            self.write(location.removeprefix(BASE), pages(BASE + f'page-{i}.html'))
        entry = self.write('sitemap.xml', sitemap_index(urls).encode())
        return entry, urls

    def test_single_leaf_manifest_is_unchanged(self):
        entry = self.write('sitemap.xml', pages(BASE))
        row = {'app_id': 'sample', 'url': BASE + 'sitemap.xml'}
        self.assertEqual(discover_leaf_urls(entry, BASE), [row['url']])
        self.assertEqual(flattened_sources([row]), [row['url']])
        self.assertEqual(local_sitemap_path(self.repository, BASE, row['url']), entry.resolve())

    def test_multiple_leaves_map_to_actual_files(self):
        entry, urls = self.multi()
        self.assertEqual(discover_leaf_urls(entry, BASE), urls)
        row = {'app_id': 'sample', 'url': urls[0], 'additional_urls': urls[1:]}
        self.assertEqual(flattened_sources([row]), urls)
        for i, location in enumerate(urls):
            path = local_sitemap_path(self.repository, BASE, location)
            self.assertNotEqual(path, entry)
            self.assertEqual(parse_leaf(path.read_bytes(), location, BASE), [BASE + f'page-{i}.html'])

    def test_all_supported_publishing_roots(self):
        self.publish.rmdir()
        for directory in ('dist', ''):
            with self.subTest(directory=directory):
                publish = self.repository / directory
                publish.mkdir(parents=True, exist_ok=True)
                entry = publish / 'sitemap.xml'
                entry.write_bytes(pages(BASE))
                self.assertEqual(local_sitemap_path(self.repository, BASE, BASE + 'sitemap.xml'), entry.resolve())
                entry.unlink()

    def test_duplicate_manifest_locations_and_apps_fail(self):
        first = {'app_id': 'sample', 'url': BASE + 'sitemap.xml'}
        for rows in ([first, dict(first)], [first, {**first, 'app_id': 'other'}],
                     [{**first, 'additional_urls': [first['url']]}]):
            with self.subTest(rows=rows), self.assertRaises(AssertionError):
                flattened_sources(rows)

    def test_invalid_manifest_and_reserved_locations_fail(self):
        for extra in ('not-an-array', None):
            with self.subTest(extra=extra), self.assertRaises(AssertionError):
                source_urls({'app_id': 'sample', 'url': BASE + 'sitemap.xml', 'additional_urls': extra})
        for name in ('sitemap.xml', 'sitemap-main.xml', 'sitemap-details.xml'):
            with self.subTest(name=name), self.assertRaises(AssertionError):
                source_urls({'app_id': 'sample', 'url': SITE + name})

    def test_unsafe_and_off_base_locations_fail(self):
        locations = [BASE + '../other.xml', BASE + '%2e%2e/other.xml', BASE + '%252e/other.xml',
                     BASE + 'posts\\other.xml', BASE + '//other.xml', BASE + './other.xml',
                     BASE + 'sitemap.xml?q=1', BASE + 'sitemap.xml#x',
                     BASE.replace('https:', 'http:') + 'sitemap.xml',
                     'https://example.com/sample/sitemap.xml', SITE + 'sample-else/sitemap.xml']
        for location in locations:
            with self.subTest(location=location), self.assertRaises(AssertionError):
                validate_location(location, BASE)

    def test_nested_index_and_self_reference_fail(self):
        for child in (BASE + 'sitemap.xml', BASE + 'nested.xml'):
            with self.subTest(child=child):
                self.write('nested.xml', sitemap_index([BASE + 'real.xml']).encode())
                entry = self.write('sitemap.xml', sitemap_index([child]).encode())
                with self.assertRaises(AssertionError):
                    discover_leaf_urls(entry, BASE)

    def test_index_path_escape_and_duplicate_locations_fail(self):
        for locations in ([BASE + '../outside.xml'], [BASE + 'one.xml'] * 2):
            raw = ('<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' +
                   ''.join('<sitemap><loc>' + url + '</loc></sitemap>' for url in locations) + '</sitemapindex>').encode()
            with self.subTest(locations=locations), self.assertRaises(AssertionError):
                discover_leaf_urls(self.write('sitemap.xml', raw), BASE)

    def test_duplicate_pages_across_leaves_fail(self):
        entry, urls = self.multi()
        self.write('posts/two.xml', pages(BASE + 'page-1.html'))
        with self.assertRaisesRegex(AssertionError, 'Duplicate page URLs across app leaves'):
            discover_leaf_urls(entry, BASE)

    def test_leaf_limits_and_page_scope(self):
        for raw in (pages(), pages(BASE, BASE), pages('http://nanalab.kr/sample/'),
                    pages(SITE + 'sample-else/'), pages(BASE + '../else/'), pages(BASE + '#x')):
            with self.subTest(raw=raw), self.assertRaises(AssertionError):
                parse_leaf(raw, BASE + 'sitemap.xml', BASE)
        valid = [BASE + str(i) + '.html' for i in range(50000)]
        self.assertEqual(len(parse_leaf(pages(*valid), BASE + 'sitemap.xml', BASE)), 50000)
        with self.assertRaises(AssertionError):
            parse_leaf(pages(*valid, BASE + 'extra.html'), BASE + 'sitemap.xml', BASE)
        with patch('sitemap_sources.MAX_BYTES', 1), self.assertRaises(AssertionError):
            parse_leaf(pages(BASE), BASE + 'sitemap.xml', BASE)

    def test_index_and_robots_advertise_every_leaf(self):
        _, urls = self.multi()
        row = {'app_id': 'sample', 'url': urls[0], 'additional_urls': urls[1:]}
        locations = [SITE + 'sitemap-main.xml', *flattened_sources([row])]
        index = ET.fromstring(sitemap_index(locations))
        self.assertEqual([node.findtext(NS + 'loc') for node in index], locations)
        policy = '# Keep verification comment\nUser-agent: *\nAllow: /\nSitemap: ' + SITE + 'sitemap.xml\n'
        robots = sitemap_robots(policy, locations)
        self.assertTrue(robots.startswith(policy))
        advertised = [line.removeprefix('Sitemap: ') for line in robots.splitlines() if line.startswith('Sitemap: ')]
        self.assertEqual(advertised, [SITE + 'sitemap.xml', *locations])
        self.assertNotIn(BASE + 'sitemap.xml', advertised)

    def checker_fixture(self, stack):
        entry, urls = self.multi()
        site = self.root / 'directory'
        (site / 'content').mkdir(parents=True)
        manifest = {'schema_version': '1.0', 'sources': [
            {'app_id': 'sample', 'url': urls[0], 'additional_urls': urls[1:]}], 'supplemental': []}
        (site / 'content/sitemap-sources.json').write_text(json.dumps(manifest), encoding='utf-8')
        app = {'id': 'sample', 'url': BASE}
        (site / 'content/apps.json').write_text(json.dumps([app]), encoding='utf-8')
        main = pages(SITE).decode()
        (site / 'content/sitemap-base.xml').write_text(main, encoding='utf-8')
        locations = [SITE + 'sitemap-main.xml', *urls]
        outputs = {'sitemap.xml': sitemap_index(locations), 'sitemap-main.xml': main,
                   'robots.txt': sitemap_robots('User-agent: *\nAllow: /', locations)}
        for name, body in outputs.items():
            (site / name).write_text(body, encoding='utf-8', newline='\n')
        stack.enter_context(patch.object(check_sitemaps, 'ROOT', site))
        stack.enter_context(patch.object(check_sitemaps, 'build', return_value=(outputs, {})))
        stack.enter_context(patch.object(check_sitemaps, 'sitemap_repositories', return_value=[app]))
        stack.enter_context(patch.object(check_sitemaps, 'grouped_repositories', return_value=[]))
        stack.enter_context(patch.object(check_sitemaps, 'grouped_landing_urls', return_value=set()))
        stack.enter_context(patch('sys.stdout', new_callable=io.StringIO))
        bodies = {url: local_sitemap_path(self.repository, BASE, url).read_bytes() for url in urls}
        return site, urls, outputs, bodies

    def test_checker_local_reads_each_leaf(self):
        with ExitStack() as stack:
            self.checker_fixture(stack)
            result = check_sitemaps.check()
            self.assertEqual((result['registered_apps'], result['app_sitemaps'], result['sitemaps']), (1, 3, 4))

    def test_sync_preserves_existing_rows_and_source_metadata(self):
        with ExitStack() as stack:
            site, urls, _, _ = self.checker_fixture(stack)
            manifest = site / 'content/sitemap-sources.json'
            data = json.loads(manifest.read_text(encoding='utf-8'))
            legacy = {'app_id': 'legacy', 'url': SITE + 'legacy/sitemap.xml', 'verified_on': '2026-10-27'}
            data['sources'].append(legacy)
            data['sources'][0]['verified_commit'] = 'a' * 40
            # Refresh the obsolete single-entry location into actual leaf URLs.
            data['sources'][0]['url'] = BASE + 'sitemap.xml'
            data['sources'][0].pop('additional_urls')
            manifest.write_text(json.dumps(data), encoding='utf-8')
            stack.enter_context(patch.object(sync_sitemaps, 'ROOT', site))
            stack.enter_context(patch.object(sync_sitemaps, 'MANIFEST', manifest))
            stack.enter_context(patch.object(sync_sitemaps, 'grouped_repositories', return_value=[]))
            stack.enter_context(patch.object(sync_sitemaps, 'sitemap_repositories', return_value=[{'id': 'sample', 'url': BASE}]))
            sync_sitemaps.discover()
            result = json.loads(manifest.read_text(encoding='utf-8'))
            rows = {row['app_id']: row for row in result['sources']}
            self.assertEqual(rows['legacy'], legacy)
            self.assertEqual(rows['sample']['verified_commit'], 'a' * 40)
            self.assertEqual(source_urls(rows['sample']), urls)
            # Returning to a single leaf removes stale additional locations.
            self.write('sitemap.xml', pages(BASE))
            sync_sitemaps.discover()
            rows = {row['app_id']: row for row in json.loads(manifest.read_text(encoding='utf-8'))['sources']}
            self.assertEqual(source_urls(rows['sample']), [BASE + 'sitemap.xml'])
            self.assertNotIn('additional_urls', rows['sample'])

    def test_remote_leaves_keep_generated_files_local(self):
        with ExitStack() as stack:
            site, urls, _, bodies = self.checker_fixture(stack)
            # Missing checkouts remain acceptable only when every leaf is fetched.
            for path in sorted(self.repository.rglob('*'), reverse=True):
                if path.is_file():
                    path.unlink()
            fetch = stack.enter_context(patch.object(check_sitemaps, 'fetch', side_effect=lambda url: bodies[url]))
            result = check_sitemaps.check(remote_leaves=True)
            self.assertEqual(result['mode'], 'local-with-remote-leaves')
            self.assertEqual({call.args[0] for call in fetch.call_args_list}, set(urls))
            with self.assertRaisesRegex(AssertionError, 'Source checkout unavailable'):
                check_sitemaps.check()
            (site / 'robots.txt').write_text('stale', encoding='utf-8')
            with self.assertRaisesRegex(AssertionError, 'robots.txt is stale'):
                check_sitemaps.check(remote_leaves=True)

    def test_live_checks_all_generated_and_app_files(self):
        with ExitStack() as stack:
            _, urls, outputs, bodies = self.checker_fixture(stack)
            bodies.update({SITE + name: body.encode() for name, body in outputs.items()})
            fetch = stack.enter_context(patch.object(check_sitemaps, 'fetch', side_effect=lambda url: bodies[url]))
            result = check_sitemaps.check(live=True)
            self.assertEqual(result['mode'], 'live')
            self.assertEqual({call.args[0] for call in fetch.call_args_list}, set(bodies))


if __name__ == '__main__':
    unittest.main()
