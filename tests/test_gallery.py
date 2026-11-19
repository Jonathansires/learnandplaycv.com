"""Gallery uploads, ordering, persistence, and admin access."""
import io
import json
import os
from pathlib import Path
import re
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from PIL import Image

import employee_admin as admin
from gallery_admin import gallery_photos
from main import app


class GalleryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = str(Path(self.temp.name) / 'site.sqlite3')
        self.env = patch.dict(os.environ, {'EMPLOYEE_DATABASE': self.path,
            'ADMIN_USERNAME': 'owner', 'ADMIN_PASSWORD': 'gallery test password', 'ADMIN_COOKIE_SECURE': 'false'})
        self.env.start()
        self.client = TestClient(app, follow_redirects=False)

    def tearDown(self):
        self.client.close()
        self.env.stop()
        self.temp.cleanup()

    def login(self):
        page = self.client.get('/admin/login')
        csrf = re.search(r'name="csrf" value="([^"]+)"', page.text).group(1)
        response = self.client.post('/admin/login', data={'csrf': csrf, 'username': 'owner', 'password': 'gallery test password'})
        self.assertEqual(response.status_code, 303)
        page = self.client.get('/admin/gallery')
        return re.search(r'name="csrf" value="([^"]+)"', page.text).group(1)

    def image(self):
        output = io.BytesIO()
        Image.new('RGB', (1600, 800), 'skyblue').save(output, format='PNG')
        return ('classroom.png', output.getvalue(), 'image/png')

    def upload(self, csrf, description='Classroom'):
        response = self.client.post('/admin/gallery/new', data={'csrf': csrf, 'description': description}, files={'photo': self.image()})
        self.assertEqual(response.status_code, 303, response.text)
        return gallery_photos()[-1]['id']

    def test_upload_edit_delete_and_persistence(self):
        self.assertIn('Photos are coming soon', self.client.get('/gallery').text)
        csrf = self.login()
        photo_id = self.upload(csrf)
        image_url = f'/gallery/photos/{photo_id}'
        public = self.client.get('/gallery')
        self.assertIn(image_url, public.text)
        self.assertIn('alt="Classroom"', public.text)
        self.assertNotIn('data-gallery-title', public.text)
        response = self.client.get(image_url)
        self.assertEqual(response.headers['content-type'], 'image/jpeg')
        self.assertLessEqual(len(response.content), admin.WEB_PHOTO_BYTES)
        with Image.open(io.BytesIO(response.content)) as image:
            self.assertEqual(image.size, (1200, 600))
        with TestClient(app) as visitor:
            self.assertIn(image_url, visitor.get('/gallery').text)
        self.assertEqual(self.client.get(f'/admin/gallery/{photo_id}/edit').status_code, 200)
        version = gallery_photos()[0]['photo_version']
        response = self.client.post(f'/admin/gallery/{photo_id}/edit', data={'csrf': csrf, 'description': 'Play area'})
        self.assertEqual(response.status_code, 303)
        self.assertEqual(gallery_photos()[0]['photo_version'], version)
        self.assertIn('alt="Play area"', self.client.get('/gallery').text)
        self.client.post(f'/admin/gallery/{photo_id}/edit', data={'csrf': csrf, 'description': 'Play area'}, files={'photo': self.image()})
        self.assertNotEqual(gallery_photos()[0]['photo_version'], version)
        self.assertEqual(self.client.post(f'/admin/gallery/{photo_id}/delete', data={'csrf': csrf}).status_code, 303)
        self.assertEqual(self.client.get(image_url).status_code, 404)
        self.assertNotIn(image_url, self.client.get('/gallery').text)

    def test_arrangement_matches_public_gallery_and_appends_uploads(self):
        csrf = self.login()
        ids = [self.upload(csrf, description) for description in ('First', 'Second', 'Third')]
        response = self.client.post('/admin/gallery/reorder', data={'csrf': csrf, 'order': json.dumps(ids[::-1])})
        self.assertEqual(response.status_code, 303)
        self.assertEqual([p['id'] for p in gallery_photos()], ids[::-1])
        public = self.client.get('/gallery').text
        self.assertLess(public.index('alt="Third"'), public.index('alt="Second"'))
        self.assertLess(public.index('alt="Second"'), public.index('alt="First"'))
        self.client.post(f'/admin/gallery/{ids[0]}/move', data={'csrf': csrf, 'direction': 'earlier'})
        self.assertEqual([p['id'] for p in gallery_photos()], [ids[2], ids[0], ids[1]])
        self.client.post(f'/admin/gallery/{ids[2]}/move', data={'csrf': csrf, 'direction': 'later'})
        self.assertEqual([p['id'] for p in gallery_photos()], [ids[0], ids[2], ids[1]])
        fourth = self.upload(csrf, 'Fourth')
        self.assertEqual(gallery_photos()[-1]['id'], fourth)
        self.client.post(f'/admin/gallery/{ids[0]}/move', data={'csrf': csrf, 'direction': 'earlier'})
        self.assertEqual(gallery_photos()[0]['id'], ids[0])

    def test_invalid_and_stale_reorders_leave_order_unchanged(self):
        csrf = self.login()
        ids = [self.upload(csrf) for _ in range(2)]
        for order, status in [('invalid', 400), ('{}', 400), ('[true]', 400), (json.dumps([ids[0], ids[0]]), 409), (json.dumps([ids[0]]), 409), (json.dumps([ids[0], 999]), 409)]:
            response = self.client.post('/admin/gallery/reorder', data={'csrf': csrf, 'order': order})
            self.assertEqual(response.status_code, status)
            self.assertEqual([p['id'] for p in gallery_photos()], ids)
        self.assertEqual(self.client.post(f'/admin/gallery/{ids[0]}/move', data={'csrf': csrf, 'direction': 'wrong'}).status_code, 400)

    def test_admin_and_csrf_required(self):
        for path in ['/admin/gallery', '/admin/gallery/new', '/admin/gallery/1/edit']:
            self.assertEqual(self.client.get(path).headers['location'], '/admin/login')
        for path in ['/admin/gallery/new', '/admin/gallery/1/edit', '/admin/gallery/1/delete', '/admin/gallery/1/move', '/admin/gallery/reorder']:
            self.assertEqual(self.client.post(path).status_code, 403)
        csrf = self.login()
        photo_id = self.upload(csrf)
        for path in ['/admin/gallery/new', f'/admin/gallery/{photo_id}/edit', f'/admin/gallery/{photo_id}/delete', f'/admin/gallery/{photo_id}/move', '/admin/gallery/reorder']:
            self.assertEqual(self.client.post(path, data={'csrf': 'invalid'}).status_code, 403)
        self.assertEqual(len(gallery_photos()), 1)

    def test_invalid_upload_and_description_are_not_saved(self):
        csrf = self.login()
        for data, files in [({}, None), ({'description': 'x' * 201}, {'photo': self.image()}), ({}, {'photo': ('bad.jpg', b'not a photo', 'image/jpeg')})]:
            response = self.client.post('/admin/gallery/new', data={'csrf': csrf, **data}, files=files)
            self.assertEqual(response.status_code, 400)
            self.assertEqual(len(gallery_photos()), 0)
        photo_id = self.upload(csrf)
        response = self.client.post(f'/admin/gallery/{photo_id}/edit', data={'csrf': csrf, 'description': 'Changed'}, files={'photo': ('bad.jpg', b'bad', 'image/jpeg')})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(gallery_photos()[0]['description'], 'Classroom')
        self.client.post(f'/admin/gallery/{photo_id}/edit', data={'csrf': csrf, 'description': '"><script>alert(1)</script>'})
        self.assertNotIn('<script>alert(1)</script>', self.client.get('/gallery').text)

    def test_existing_employee_database_is_preserved(self):
        with sqlite3.connect(self.path) as db:
            db.execute("CREATE TABLE employees (id INTEGER PRIMARY KEY, name TEXT NOT NULL, title TEXT NOT NULL DEFAULT '', sort_order INTEGER NOT NULL DEFAULT 0, photo BLOB, photo_version TEXT)")
            db.execute("INSERT INTO employees (name) VALUES ('Existing teacher')")
        self.assertEqual(self.client.get('/gallery').status_code, 200)
        self.assertEqual(admin.employees()[0]['name'], 'Existing teacher')
        csrf = self.login()
        self.upload(csrf)
        self.assertEqual(admin.employees()[0]['name'], 'Existing teacher')
