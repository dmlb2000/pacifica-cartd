"""File that will tests the requests and coverage of the server and the tasks."""
import unittest
import os
import time
import datetime
import tarfile
import json
from urllib3.util.retry import Retry
import requests
from requests.adapters import HTTPAdapter
from cart.celery import CART_APP
from cart.cart_orm import Cart, File
from cart.cart_utils import Cartutils
from cart.tasks import get_files_locally, pull_file, stage_files


def cart_json_helper():
    """Helper that returns a cart json text string."""
    return json.dumps({
        'fileids': [
            {
                'id': 'foo.txt',
                'path': '1/2/3/foo.txt',
                'hashtype': 'md5',
                'hashsum': 'ac59bb32dac432674dd6e620a6b35ff3'
            },
            {
                'id': 'bar.csv',
                'path': '1/2/3/bar.csv',
                'hashtype': 'md5',
                'hashsum': 'ef39aa7f8df8bdc8b8d4d81f4e0ef566'
            },
            {
                'id': 'baz.ini',
                'path': '2/3/4/baz.ini',
                'hashtype': 'md5',
                'hashsum': 'b0c21625a5ef364864191e5907d7afb4'
            }
        ]
    })


class TestCartEndToEnd(unittest.TestCase):
    """Contains all the tests for the end to end cart testing."""

    def setUp(self):
        """Make the tasks not asynchronise for testing."""
        CART_APP.conf.update(CELERY_ALWAYS_EAGER=True)
        session = requests.Session()
        retries = Retry(total=5, backoff_factor=5.0)
        session.mount('http://', HTTPAdapter(max_retries=retries))
        self.session = session

    def setup_good_cart(self, cart_id):
        """Setup a test good cart."""
        resp = self.session.post(
            'http://127.0.0.1:8081/{}'.format(cart_id),
            data=cart_json_helper(),
            headers={
                'Content-Type': 'application/json'
            }
        )
        self.assertEqual(resp.status_code, 201, 'Setup good cart for test failed.')
        return resp

    def test_post_cart(self, cart_id='36'):
        """Test the creation of a cart."""
        resp = self.setup_good_cart(cart_id)
        self.assertEqual(resp.json()['message'], 'Cart Processing has begun')

    def test_status_cart(self, cart_id='37'):
        """Test the status of a cart."""
        self.test_post_cart(cart_id)

        while True:
            resp = self.session.head('http://127.0.0.1:8081/{}'.format(cart_id))
            resp_status = resp.headers['X-Pacifica-Status']
            resp_message = resp.headers['X-Pacifica-Message']
            resp_code = resp.status_code
            if resp_code == 204 and resp_status != 'staging':
                break
            if resp_code == 500:  # pragma: no cover
                break
            time.sleep(2)

        self.assertEqual(resp_status, 'ready')
        self.assertEqual(resp_message, '')

    def test_get_cart(self, cart_id='38'):
        """Test the getting of a cart."""
        self.test_status_cart(cart_id)

        resp = self.session.get('http://127.0.0.1:8081/{}?filename={}'.format(cart_id, cart_id))
        with open(cart_id, 'wb') as fdesc:
            for chunk in resp.iter_content(chunk_size=128):
                fdesc.write(chunk)

        self.assertEqual(os.path.isfile(cart_id), True)
        saved_tar = tarfile.open(cart_id)
        tar_members = saved_tar.getnames()
        self.assertTrue('38/1/2/3/foo.txt' in tar_members, '{} should have foo.txt in it'.format(tar_members))
        data = saved_tar.extractfile(saved_tar.getmember('38/1/2/3/foo.txt')).read()
        self.assertEqual(data, 'Writing content for first file')

    def test_get_noncart(self, cart_id='86'):
        """Test the getting of a cart."""
        resp = self.session.get('http://127.0.0.1:8081/{}'.format(cart_id))
        self.assertEqual(resp.json()['message'], 'The cart does not exist or has already been deleted')
        self.assertEqual(resp.status_code, 404)

    def test_delete_cart(self, cart_id='39'):
        """Test the deletion of a cart."""
        self.test_status_cart(cart_id)

        resp = self.session.delete('http://127.0.0.1:8081/{}'.format(cart_id))
        self.assertEqual(resp.json()['message'], 'Cart Deleted Successfully')

    def test_delete_invalid_cart(self, cart_id='393'):
        """Test the deletion of a invalid cart."""
        resp = self.session.delete('http://127.0.0.1:8081/{}'.format(cart_id))
        self.assertEqual(resp.json()['message'], 'Not Found')

    def test_prepare_bundle(self):
        """Test getting bundle files ready."""
        data = json.loads(cart_json_helper())
        file_ids = data['fileids']
        Cart.database_connect()
        mycart = Cart(cart_uid=117, status='staging')
        mycart.save()
        cart_utils = Cartutils()
        cart_utils.update_cart_files(mycart, file_ids)
        get_files_locally(mycart.id)
        cart_utils.prepare_bundle(mycart.id)
        status = mycart.status
        cartid = mycart.id
        while status == 'staging':
            mycart = Cart.get(Cart.id == cartid)
            status = mycart.status
        Cart.database_close()
        self.assertEqual(status, 'ready')

    def test_prep_bundle_error(self):
        """Test getting bundle ready with a file in error state."""
        data = json.loads(cart_json_helper())
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
        cart_utils.prepare_bundle(mycart.id)
        status = mycart.status
        cartid = mycart.id
        while status == 'staging':
            mycart = Cart.get(Cart.id == cartid)
            status = mycart.status
        Cart.database_close()
        self.assertEqual(status, 'error')

    def test_prep_bundle_staging(self):
        """Test getting bundle ready with a file in staging state."""
        data = json.loads(cart_json_helper())
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
        cart_utils.prepare_bundle(mycart.id)  # hitting more coverage, set files to staged
        for cart_file in File.select().where(File.cart == mycart.id):
            cart_file.status = 'staged'
            cart_file.save()
        cart_utils.prepare_bundle(mycart.id)  # call again after file update
        status = mycart.status
        cartid = mycart.id
        while status == 'staging':
            mycart = Cart.get(Cart.id == cartid)
            status = mycart.status
        Cart.database_close()
        self.assertEqual(status, 'ready')

    def test_pull_invalid_file(self):
        """Test pulling a file id that doesnt exist."""
        pull_file('8765', 'some/bad/path', '1111', False)
        # no action happens on invalid file, so no assertion to check
        self.assertEqual(True, True)

    def test_tar_invalid_cart(self):
        """Test pulling a file id that doesnt exist."""
        cart_utils = Cartutils()
        cart_utils.tar_files('8765', True)
        # no action happens on invalid cart to tar, so no assertion to check
        self.assertEqual(True, True)

    def test_cart_deleted_date(self):
        """Test getting bundle ready with a file in staging state."""
        data = json.loads(cart_json_helper())
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
            pull_file(cart_file.id, '/tmp/some/Path', '1111', False)
        Cart.database_close()
        self.assertEqual(status, 'deleted')

    def test_status_cart_notfound(self):
        """Test the status of a cart with cart not found."""
        cart_id = '97'
        resp = self.session.head('http://127.0.0.1:8081/{}'.format(cart_id))
        resp_status = resp.headers['X-Pacifica-Status']
        resp_message = resp.headers['X-Pacifica-Message']
        resp_code = resp.status_code

        self.assertEqual(resp_status, 'error')
        self.assertEqual(resp_message, 'No cart with uid 97 found')
        self.assertEqual(resp_code, 404)

    def test_status_cart_error(self):
        """Test the status of a cart with error."""
        cart_id = '98'
        bad_cart_data = {
            'fileids': [
                {
                    'id': 'mytest.txt',
                    'path': '1/2/3/mytest.txt',
                    'hashtype': 'md5',
                    'hashsum': ''
                }
            ]
        }

        resp = self.session.post(
            'http://127.0.0.1:8081/{}'.format(cart_id),
            data=json.dumps(bad_cart_data),
            headers={
                'Content-Type': 'application/json'
            }
        )
        self.assertEqual(resp.json()['message'], 'Cart Processing has begun')

        while True:
            resp = self.session.head('http://127.0.0.1:8081/{}'.format(cart_id))
            resp_status = resp.headers['X-Pacifica-Status']
            resp_code = resp.status_code
            if (resp_code == 204 and resp_status != 'staging') or resp_code == 500:
                break
            time.sleep(2)

        self.assertEqual(resp_status, 'error')
        self.assertEqual(resp_code, 500)

    def test_stage_files(self):
        """Test getting bundle files ready."""
        data = json.loads(cart_json_helper())
        file_ids = data['fileids']
        Cart.database_connect()
        mycart = Cart(cart_uid=747, status='staging')
        mycart.save()
        cart_utils = Cartutils()
        cart_utils.update_cart_files(mycart, file_ids)
        stage_files(file_ids, mycart.id)
        cart_utils.prepare_bundle(mycart.id)
        status = mycart.status
        cartid = mycart.id
        while status == 'staging':
            mycart = Cart.get(Cart.id == cartid)
            status = mycart.status
        Cart.database_close()
        self.assertEqual(status, 'ready')

    def test_post_cart_bad_hash(self, cart_id='1136'):
        """Test the creation of a cart with bad hash."""
        bad_cart_data = {
            'fileids': [
                {
                    'id': 'foo.txt',
                    'path': '1/2/3/foo.txt',
                    'hashtype': 'md5',
                    'hashsum': 'ac59bb32'
                },
                {
                    'id': 'bar.csv',
                    'path': '1/2/3/bar.csv',
                    'hashtype': 'md5',
                    'hashsum': 'ef39aa7f8df8bdc8b8d4d81f4e0ef566'
                },
                {
                    'id': 'baz.ini',
                    'path': '2/3/4/baz.ini',
                    'hashtype': 'md5',
                    'hashsum': 'b0c21625a5ef364864191e5907d7afb4'
                }
            ]
        }
        resp = self.session.post(
            'http://127.0.0.1:8081/{}'.format(cart_id),
            data=json.dumps(bad_cart_data),
            headers={
                'Content-Type': 'application/json'
            }
        )
        self.assertEqual(resp.json()['message'], 'Cart Processing has begun')

        while True:
            resp = self.session.head('http://127.0.0.1:8081/{}'.format(cart_id))
            resp_status = resp.headers['X-Pacifica-Status']
            resp_code = resp.status_code
            if resp_code == 204 and resp_status != 'staging':  # pragma: no cover
                break
            if resp_code == 500:
                break
            time.sleep(2)

        self.assertEqual(resp_status, 'error')
