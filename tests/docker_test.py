#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Basic cart docker testing."""
from os.path import basename
from time import sleep
from hashlib import sha1
from unittest import TestCase
from json import dumps
import tarfile
import requests


class BasicCartTests(TestCase):
    """Basic cart testing module meant for client to use."""

    cart_url = 'http://127.0.0.1:8081'

    def test_service_started(self):
        """Test the service has started and functional."""
        tries = 40
        wait = 3
        while tries:
            try:
                resp = requests.get('{}/1234'.format(self.cart_url))
            except requests.exceptions.ConnectionError:
                tries -= 1
                sleep(wait)
                continue
            tries = 0
        self.assertEqual(resp.status_code, 404)


class RunCartTests(TestCase):
    """Run more extensive cart tests."""

    files = []
    test_cart_url = 'http://127.0.0.1:8081/test_cart'

    @classmethod
    def setUpClass(cls):
        """Add some files to the archive interface."""
        for local_file in ['../README.md', '../setup.py']:
            file_id = len(local_file)
            file_hash = sha1()
            with open(local_file, 'rb') as local_fd:
                file_data = local_fd.read()
            file_hash.update(file_data)
            requests.put(
                'http://127.0.0.1:8080/{}'.format(file_id), data=file_data)
            cls.files.append({
                'id': file_id,
                'hashtype': 'sha1',
                'hashsum': file_hash.hexdigest(),
                'path': 'a/b/{}'.format(basename(local_file))
            })

    def _setup_good_cart(self):
        """Setup a good cart."""
        resp = requests.post(
            self.test_cart_url, data=dumps({'fileids': self.files}),
            headers={'Content-Type': 'application/json'}
        )
        self.assertEqual(resp.json()['message'], 'Cart Processing has begun')

    def _wait_for_cart(self):
        """Wait for the cart to be ready."""
        tries = 40
        wait = 3
        while tries:
            resp = requests.head(self.test_cart_url)
            resp_status = resp.headers['X-Pacifica-Status']
            resp_code = resp.status_code
            if (resp_code == 204 and resp_status != 'staging') or resp_code == 500:
                break
            tries -= 1
            sleep(wait)

        resp_status = resp.headers['X-Pacifica-Status']
        resp_message = resp.headers['X-Pacifica-Message']
        self.assertEqual(resp_status, 'ready')
        self.assertEqual(resp_message, '')

    def _download_test_cart(self):
        """Download the cart and check it."""
        resp = requests.get('{}?filename=foo.tar'.format(self.test_cart_url))
        with open('foo.tar', 'wb') as fdesc:
            for chunk in resp.iter_content(chunk_size=128):
                fdesc.write(chunk)

        saved_tar = tarfile.open('foo.tar')
        tar_members = saved_tar.getnames()
        self.assertTrue(
            'foo/a/b/README.md' in tar_members,
            '{} should have README.md in it'.format(tar_members)
        )

    def test_cart_end_to_end(self):
        """Test creating, waiting and downloading the cart."""
        self._setup_good_cart()
        self._wait_for_cart()
        self._download_test_cart()
