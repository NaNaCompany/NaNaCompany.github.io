"""Associate split repositories with one directory card and verified sitemap routes."""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
SITE = 'https://nanalab.kr/'


def validate_groups(data, app_ids):
    assert data.get('schema_version') == '1.0', 'Unknown repository group schema'
    parents, children, rows = set(), set(), []
    for group in data['groups']:
        parent = group['app_id']
        assert parent in app_ids and parent not in parents, 'Missing or duplicate parent app: ' + parent
        parents.add(parent)
        assert group['repositories'], 'Empty repository group: ' + parent
        for member in group['repositories']:
            slug = member['id']
            assert re.fullmatch(r'[a-z0-9]+(?:[-_][a-z0-9]+)*', slug), 'Invalid child repository: ' + slug
            assert slug not in app_ids and slug not in children, 'Duplicate child or app card: ' + slug
            children.add(slug)
            assert member['status'] in {'published', 'preparing'}, 'Unknown child publication status: ' + slug
            if member['status'] == 'published':
                assert member['url'] == SITE + slug + '/', 'Noncanonical child URL: ' + slug
                assert re.fullmatch(r'[a-f0-9]{40}', member['verified_commit']), 'Missing verified commit: ' + slug
                assert re.fullmatch(r'\d{4}-\d{2}-\d{2}', member['verified_on']), 'Missing verification date: ' + slug
                languages = member['languages']
                assert languages and len(languages) == len(set(languages)), 'Missing or duplicate child languages: ' + slug
                for language in languages:
                    assert re.fullmatch(r'[a-z]{2}(?:-[A-Z]{2})?', language), 'Invalid child language: ' + slug
                    path = member.get('language_paths', {}).get(language, language + '/')
                    assert path in {'', language + '/'}, 'Invalid child language route: ' + slug
                assert set(member.get('language_paths', {})) <= set(languages), 'Unknown child language path: ' + slug
            else:
                assert not any(key in member for key in ['url', 'languages', 'language_paths']), 'Unpublished child exposes speculative routes: ' + slug
            rows.append({**member, 'directory_app_id': parent})
    return rows


def grouped_repositories(apps=None):
    if apps is None:
        apps = json.loads((ROOT / 'content/apps.json').read_text(encoding='utf8'))
    data = json.loads((ROOT / 'content/repository-groups.json').read_text(encoding='utf8'))
    return validate_groups(data, {app['id'] for app in apps})


def sitemap_repositories(apps):
    return [*apps, *[row for row in grouped_repositories(apps) if row['status'] == 'published']]


def grouped_landing_urls(apps=None):
    urls = set()
    for row in grouped_repositories(apps):
        if row['status'] == 'published':
            urls.add(row['url'])
            urls.update(row['url'] + row.get('language_paths', {}).get(language, language + '/') for language in row['languages'])
    return urls
