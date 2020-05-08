#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Test cart database setup class."""
import os
from time import sleep
import threading
from tempfile import mkdtemp
import requests
import cherrypy
from celery.bin.celery import main as celery_main
from pacifica.cartd.rest import CartRoot, error_page_default
from pacifica.cartd.orm import Cart, File, CartTasks


class TestCartdBase:
    """Contain all the tests for the Cart Interface."""

    archive_dir = mkdtemp()
    PORT = 8081
    HOST = '127.0.0.1'
    url = 'http://{0}:{1}'.format(HOST, PORT)
    headers = {'content-type': 'application/json'}
    test_files = {
        'foo.txt': b'Writing content for first file',
        'bar.csv': b'Writing,content,for,second,file',
        'baz.ini': b'Writing content for the third and final file'
    }

    # pylint: disable=invalid-name
    @classmethod
    def tearDownClass(cls):
        """Unset the VOLUME_PATH for future tests."""
        if 'VOLUME_PATH' in os.environ:
            del os.environ['VOLUME_PATH']
    # pylint: enable=invalid-name

    @classmethod
    def setup_server(cls):
        """Start all the services."""
        os.environ['VOLUME_PATH'] = '{}{}'.format(mkdtemp(), os.path.sep)
        os.environ['CARTD_CPCONFIG'] = os.path.join(os.path.dirname(
            os.path.realpath(__file__)), '..', 'server.conf')
        cherrypy.config.update({'error_page.default': error_page_default})
        cherrypy.config.update(os.environ['CARTD_CPCONFIG'])
        cherrypy.tree.mount(CartRoot(), '/', os.environ['CARTD_CPCONFIG'])

    @staticmethod
    def create_sample_cart(cart_uid='1', status='staging', bundle_path='1'):
        """Create a sample cart."""
        return Cart.create(
            cart_uid=cart_uid,
            status=status,
            bundle_path=os.path.join(os.getenv('VOLUME_PATH'), bundle_path)
        )

    @staticmethod
    def create_sample_file(test_cart, file_name='1.txt', bundle_path='1'):
        """Create a sample file in cart."""
        return File.create(
            cart=test_cart,
            file_name=file_name,
            bundle_path=os.path.join(os.getenv('VOLUME_PATH'), bundle_path, file_name)
        )

    # pylint: disable=invalid-name
    def setUp(self):
        """Setup the database with in memory sqlite."""
        # pylint: disable=protected-access
        # pylint: disable=no-member
        if os.path.isfile('db.sqlite3'):
            Cart._meta.database.drop_tables([Cart, File, CartTasks])
        Cart._meta.database.create_tables([Cart, File, CartTasks])
        # pylint: enable=no-member

        def run_celery_worker():
            """Run the main solo worker."""
            return celery_main([
                'celery', '-A', 'pacifica.cartd.tasks', 'worker', '--pool', 'solo',
                '--quiet', '-b', 'redis://127.0.0.1:6379/0'
            ])

        self.celery_thread = threading.Thread(target=run_celery_worker)
        self.celery_thread.start()
        archive_url = 'http://127.0.0.1:8080'
        for filename, content in self.test_files.items():
            url = '{}/{}'.format(archive_url, filename)
            resp = requests.head(url)
            if resp.status_code == 204:
                resp = requests.delete(url)
                assert resp.status_code == 200
            resp = requests.put(url, data=content)
            assert resp.status_code == 201
        sleep(3)

    # pylint: disable=invalid-name
    def tearDown(self):
        """Tear down the test and remove local state."""
        try:
            celery_main([
                'celery', '-A', 'pacifica.cartd.tasks', 'control',
                '-b', 'redis://127.0.0.1:6379/0', 'shutdown'
            ])
        except SystemExit:
            pass
        self.celery_thread.join()
        try:
            celery_main([
                'celery', '-A', 'pacifica.cartd.tasks', '-b', 'redis://127.0.0.1:6379/0',
                '--force', 'purge'
            ])
        except SystemExit:
            pass
        for filename, _content in self.test_files.items():
            full_path = os.path.join(self.archive_dir, filename)
            if os.path.isfile(full_path):
                os.unlink(full_path)

        # pylint: enable=protected-access


def create_test_db():
    """Create a simple test DB."""
    test = TestCartdBase()
    test.setUp()
    test_cart = test.create_sample_cart('HELLOWORLD', 'ready', '1')
    test.create_sample_file(test_cart)
    test.create_sample_cart(2, 'staging', '2')
    test_cart = test.create_sample_cart(3, 'deleted', '3')
    test_cart.deleted_date = test_cart.creation_date
    test_cart.save()
    test.tearDown()


if __name__ == '__main__':
    create_test_db()
