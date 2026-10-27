"""Regression checks for directory aliases and independent app sitemaps."""
import unittest

from site_urls import KOREAN_ROOT_ALIASES, canonical_links, canonical_url
from check_sitemaps import leaf


class CanonicalUrls(unittest.TestCase):
    def test_verified_korean_aliases_prefer_root_in_directory(self):
        for slug in KOREAN_ROOT_ALIASES:
            for suffix in ('/ko', '/ko/', '/ko/index.html'):
                with self.subTest(slug=slug, suffix=suffix):
                    self.assertEqual(canonical_url('https://nanalab.kr/' + slug + suffix),
                                     'https://nanalab.kr/' + slug + '/')

    def test_host_query_and_fragment_are_preserved_correctly(self):
        self.assertEqual(canonical_url('http://www.nanalab.kr/cat-naps/ko/?level=3#play'),
                         'https://nanalab.kr/cat-naps/?level=3#play')
        self.assertEqual(canonical_url('https://nanalab.kr/rebirth_country/ko/r/KR/'),
                         'https://nanalab.kr/rebirth_country/r/KR/')

    def test_other_hosts_languages_and_app_names_are_not_aliases(self):
        for url in ('https://example.com/cat-naps/ko/', 'https://nanalab.kr/cat-naps/en/',
                    'https://nanalab.kr/another-app/ko/', 'https://nanalab.kr/cat-naps-2/ko/',
                    'https://nanalab.kr/cat-naps/korean/'):
            self.assertEqual(canonical_url(url), url)

    def test_app_validation_keeps_own_korean_route(self):
        self.assertEqual(canonical_url('http://www.nanalab.kr/cat-naps/ko', korean_aliases=False),
                         'https://nanalab.kr/cat-naps/ko/')
        self.assertEqual(canonical_url('https://nanalab.kr/app'), 'https://nanalab.kr/apps/')

    def test_rendered_links_keep_stable_ids_and_other_attributes(self):
        source = '<a id="cat-naps-ko" href="https://nanalab.kr/cat-naps/ko/?a=1&amp;b=2">Game</a>'
        self.assertEqual(canonical_links(source),
                         '<a id="cat-naps-ko" href="https://nanalab.kr/cat-naps/?a=1&amp;b=2">Game</a>')

    def test_leaf_policy_distinguishes_directory_and_published_apps(self):
        xml = b'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://nanalab.kr/cat-naps/ko/</loc></url></urlset>'
        self.assertEqual(leaf(xml, 'app leaf'), {'https://nanalab.kr/cat-naps/ko/'})
        with self.assertRaisesRegex(AssertionError, 'Noncanonical'):
            leaf(xml, 'main', directory=True)
        for invalid in (b'http://nanalab.kr/cat-naps/ko/', b'https://other.example/cat-naps/ko/',
                        b'https://nanalab.kr/cat-naps/ko'):
            with self.assertRaises(AssertionError):
                leaf(xml.replace(b'https://nanalab.kr/cat-naps/ko/', invalid), 'app leaf')


if __name__ == '__main__':
    unittest.main()
