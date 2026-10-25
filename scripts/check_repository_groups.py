"""Guard card deduplication and publication boundaries for split repositories."""
from copy import deepcopy
import json
import unittest
from repository_groups import ROOT, grouped_landing_urls, sitemap_repositories, validate_groups


class RepositoryGroups(unittest.TestCase):
    def setUp(self):
        self.apps = json.loads((ROOT / 'content/apps.json').read_text(encoding='utf8'))
        self.data = json.loads((ROOT / 'content/repository-groups.json').read_text(encoding='utf8'))
        self.ids = {row['id'] for row in self.apps}

    def test_published_children_add_routes_without_cards(self):
        rows = validate_groups(self.data, self.ids)
        published = {row['id'] for row in rows if row['status'] == 'published'}
        preparing = {row['id'] for row in rows if row['status'] == 'preparing'}
        self.assertTrue(published)
        self.assertFalse((published | preparing) & self.ids)
        self.assertEqual({row['id'] for row in sitemap_repositories(self.apps)}, self.ids | published)
        urls = grouped_landing_urls(self.apps)
        for row in rows:
            if row['status'] == 'published':
                self.assertIn(row['url'], urls)
                for language in row['languages']:
                    self.assertIn(row['url'] + row.get('language_paths', {}).get(language, language + '/'), urls)
            else:
                self.assertFalse(any('/' + row['id'] + '/' in url for url in urls))

    def test_unknown_parent_cannot_hide_workspace_repo(self):
        self.data['groups'][0]['app_id'] = 'missing-app'
        with self.assertRaises(AssertionError): validate_groups(self.data, self.ids)

    def test_duplicate_card_or_child_rejected(self):
        for duplicate in [self.data['groups'][0]['app_id'], self.data['groups'][0]['repositories'][1]['id']]:
            data = deepcopy(self.data)
            data['groups'][0]['repositories'][0]['id'] = duplicate
            with self.assertRaises(AssertionError): validate_groups(data, self.ids)

    def test_speculative_routes_rejected(self):
        child = self.data['groups'][0]['repositories'][0]
        child['status'] = 'preparing'
        with self.assertRaises(AssertionError): validate_groups(self.data, self.ids)

    def test_invalid_published_metadata_rejected(self):
        for key, value in [('id','../outside'),('status','ready'),('url','https://example.com/'),
                           ('verified_commit','unverified'),('language_paths',{'ko':'../outside/'}),
                           ('languages',['ko','ko'])]:
            data = deepcopy(self.data)
            data['groups'][0]['repositories'][0][key] = value
            with self.subTest(key=key), self.assertRaises(AssertionError): validate_groups(data, self.ids)


if __name__ == '__main__':
    unittest.main(verbosity=1)
