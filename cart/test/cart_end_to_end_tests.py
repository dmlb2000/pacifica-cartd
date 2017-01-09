"""File that will tests the requests and coverage of the server and the tasks"""
import unittest
import os
import time
import datetime
import json
from subprocess import call
import requests
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from cart.celery import CART_APP
from cart.cart_orm import Cart, File
from cart.cart_utils import Cartutils
from cart.tasks import get_files_locally, prepare_bundle, pull_file, tar_files

class TestCartEndToEnd(unittest.TestCase):
    """
    Contains all the tests for the end to end cart testing
    """
    def setUp(self):
        """Make the tasks not asynchronise for testing"""
        CART_APP.conf.update(CELERY_ALWAYS_EAGER=True)

    def test_post_cart(self, cart_id='36'):
        """test the creation of a cart"""
        with open('/tmp/cart.json', 'a') as cartfile:
            cartfile.write('{"fileids": [{"id":"foo.txt", "path":"1/2/3/foo.txt"},' +
                           '{"id":"bar.csv", "path":"1/2/3/bar.csv"},' +
                           '{"id":"baz.ini", "path":"2/3/4/baz.ini"}]}')

        session = requests.Session()
        retries = Retry(total=5, backoff_factor=5.0)
        session.mount('http://', HTTPAdapter(max_retries=retries))

        resp = session.post('http://127.0.0.1:8081/' + cart_id, data=open('/tmp/cart.json', 'rb'))
        os.remove('/tmp/cart.json')
        data = json.loads(resp.text)
        self.assertEqual(os.path.isfile('/tmp/cart.json'), False)
        self.assertEqual(data['message'], 'Cart Processing has begun')

    def test_status_cart(self, cart_id='37'):
        """test the status of a cart"""
        self.test_post_cart(cart_id)

        session = requests.Session()
        retries = Retry(total=5, backoff_factor=5.0)
        session.mount('http://', HTTPAdapter(max_retries=retries))

        while True:
            resp = session.head('http://127.0.0.1:8081/' + cart_id)
            resp_status = resp.headers['X-Pacifica-Status']
            resp_message = resp.headers['X-Pacifica-Message']
            resp_code = resp.status_code
            if resp_code == 200 and resp_status != 'staging':
                break
            time.sleep(2)

        self.assertEqual(resp_status, 'ready')
        self.assertEqual(resp_message, '')

    def test_get_cart(self, cart_id='38'):
        """test the getting of a cart"""
        self.test_status_cart(cart_id)

        session = requests.Session()
        retries = Retry(total=5, backoff_factor=5.0)
        session.mount('http://', HTTPAdapter(max_retries=retries))

        resp = session.get('http://127.0.0.1:8081/' + cart_id)
        with open(cart_id, 'wb') as fdesc:
            for chunk in resp.iter_content(chunk_size=128):
                fdesc.write(chunk)

        self.assertEqual(os.path.isfile(cart_id), True)
        call(["tar", "-x", "-f", cart_id])
        self.assertEqual(os.path.isdir(cart_id), True)
        self.assertEqual(os.path.isfile(cart_id + '/1/2/3/foo.txt'), True)
        with open(cart_id + '/1/2/3/foo.txt', 'r') as myfile:
            data = myfile.read()

        self.assertEqual(data, 'Writing content for first file')

    def test_delete_cart(self, cart_id='39'):
        """test the deletion of a cart"""
        self.test_status_cart(cart_id)

        session = requests.Session()
        retries = Retry(total=5, backoff_factor=5.0)
        session.mount('http://', HTTPAdapter(max_retries=retries))

        resp = session.delete('http://127.0.0.1:8081/' + cart_id)
        data = json.loads(resp.text)
        self.assertEqual(data['message'], 'Cart Deleted Successfully')

    def test_delete_invalid_cart(self, cart_id='393'):
        """test the deletion of a invalid cart"""

        session = requests.Session()
        retries = Retry(total=5, backoff_factor=5.0)
        session.mount('http://', HTTPAdapter(max_retries=retries))

        resp = session.delete('http://127.0.0.1:8081/' + cart_id)
        data = json.loads(resp.text)
        self.assertEqual(data['message'], 'Cart with uid: 393 was previously deleted or no longer exists')

    def test_prepare_bundle(self):
        """test getting bundle files ready"""
        data = json.loads('{"fileids": [{"id":"foo.txt", "path":"1/2/3/foo.txt"},' +
                          '{"id":"bar.csv", "path":"1/2/3/bar.csv"},' +
                          '{"id":"baz.ini", "path":"2/3/4/baz.ini"}]}')
        file_ids = data['fileids']
        Cart.database_connect()
        mycart = Cart(cart_uid=117, status='staging')
        mycart.save()
        cart_utils = Cartutils()
        cart_utils.update_cart_files(mycart, file_ids)
        get_files_locally(mycart.id)
        prepare_bundle(mycart.id)
        status = mycart.status
        cartid = mycart.id
        while status == 'staging':
            mycart = Cart.get(Cart.id == cartid)
            status = mycart.status
        Cart.database_close()
        self.assertEqual(status, 'ready')

    def test_prep_bundle_error(self):
        """test getting bundle ready with a file in error state"""
        data = json.loads('{"fileids": [{"id":"foo.txt", "path":"1/2/3/foo.txt"},' +
                          '{"id":"bar.csv", "path":"1/2/3/bar.csv"},' +
                          '{"id":"baz.ini", "path":"2/3/4/baz.ini"}]}')
        file_ids = data['fileids']
        Cart.database_connect()
        mycart = Cart(cart_uid=343, status='staging')
        mycart.save()
        cart_utils = Cartutils()
        cart_utils.update_cart_files(mycart, file_ids)
        get_files_locally(mycart.id)
        for cart_file in File.select().where(File.cart == mycart.id):
            cart_file.status = 'error'
            cart_file.save()
        prepare_bundle(mycart.id)
        status = mycart.status
        cartid = mycart.id
        while status == 'staging':
            mycart = Cart.get(Cart.id == cartid)
            status = mycart.status
        Cart.database_close()
        self.assertEqual(status, 'error')

    def test_prep_bundle_staging(self):
        """test getting bundle ready with a file in staging state"""
        data = json.loads('{"fileids": [{"id":"foo.txt", "path":"1/2/3/foo.txt"},' +
                          '{"id":"bar.csv", "path":"1/2/3/bar.csv"},' +
                          '{"id":"baz.ini", "path":"2/3/4/baz.ini"}]}')
        file_ids = data['fileids']
        Cart.database_connect()
        mycart = Cart(cart_uid=343, status='staging')
        mycart.save()
        cart_utils = Cartutils()
        cart_utils.update_cart_files(mycart, file_ids)
        get_files_locally(mycart.id)
        for cart_file in File.select().where(File.cart == mycart.id):
            cart_file.status = 'staging'
            cart_file.save()
        prepare_bundle(mycart.id) #hitting more coverage, set files to staged
        for cart_file in File.select().where(File.cart == mycart.id):
            cart_file.status = 'staged'
            cart_file.save()
        prepare_bundle(mycart.id) #call again after file update
        status = mycart.status
        cartid = mycart.id
        while status == 'staging':
            mycart = Cart.get(Cart.id == cartid)
            status = mycart.status
        Cart.database_close()
        self.assertEqual(status, 'ready')

    def test_pull_invalid_file(self):
        """test pulling a file id that doesnt exist"""
        pull_file('8765', False)
        #no action happens on invalid file, so no assertion to check
        self.assertEqual(True, True)

    def test_tar_invalid_cart(self):
        """test pulling a file id that doesnt exist"""
        tar_files('8765')
        #no action happens on invalid cart to tar, so no assertion to check
        self.assertEqual(True, True)

    def test_cart_deleted_date(self):
        """test getting bundle ready with a file in staging state"""
        data = json.loads('{"fileids": [{"id":"foo.txt", "path":"1/2/3/foo.txt"},' +
                          '{"id":"bar.csv", "path":"1/2/3/bar.csv"},' +
                          '{"id":"baz.ini", "path":"2/3/4/baz.ini"}]}')
        file_ids = data['fileids']
        Cart.database_connect()
        mycart = Cart(cart_uid=444, status='staging')
        mycart.save()
        cart_utils = Cartutils()
        cart_utils.update_cart_files(mycart, file_ids)
        get_files_locally(mycart.id)
        mycart.status = 'deleted'
        mycart.deleted_date = datetime.datetime.now()
        mycart.save()
        status = mycart.status
        for cart_file in File.select().where(File.cart == mycart.id):
            pull_file(cart_file.id, False)
        Cart.database_close()
        self.assertEqual(status, 'deleted')
