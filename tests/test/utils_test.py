#!/usr/bin/python
# -*- coding: utf-8 -*-
"""File used to unit test the pacifica_cart."""
import unittest
import os
import json
from types import MethodType
import shutil
import mock
import psutil
from pacifica.cartd.orm import Cart
from pacifica.cartd.utils import Cartutils
import pacifica.cartd.orm
# pylint: disable=import-error
from cart_db_setup_test import cart_dbsetup_gen
# pylint: enable=import-error


class TestUtils(cart_dbsetup_gen(unittest.TestCase)):
    """Contains all the tests for the CartUtils class."""

    def test_create_download_path(self):
        """Test the creation of the download path for a cart file."""
        test_cart = self.create_sample_cart()
        test_file = self.create_sample_file(test_cart)
        cart_utils = Cartutils()
        success = cart_utils.create_download_path(
            test_file,
            test_cart,
            test_file.bundle_path
        )
        directory_name = os.path.dirname(test_file.bundle_path)
        self.assertEqual(success, True)
        self.assertEqual(os.path.isdir(directory_name), True)

        os.rmdir(directory_name)
        self.assertEqual(os.path.isdir(directory_name), False)

    @mock.patch.object(Cartutils, 'create_bundle_directories')
    def test_bad_create_download_path(self, mock_create_bundle):
        """Test the creation of the download path for a cart file."""
        test_cart = self.create_sample_cart()
        test_file = self.create_sample_file(test_cart)
        cart_utils = Cartutils()
        mock_create_bundle.side_effect = OSError(mock.Mock(), 'Error')
        success = cart_utils.create_download_path(
            test_file,
            test_cart,
            test_file.bundle_path
        )
        self.assertEqual(success, False)

    def test_create_bundle_directories(self):
        """Test the  creation of directories where files will be saved."""
        directory_name = '/tmp/fakedir/'
        cart_utils = Cartutils()
        cart_utils.create_bundle_directories(directory_name)
        self.assertEqual(os.path.isdir(directory_name), True)
        os.rmdir(directory_name)
        self.assertEqual(os.path.isdir(directory_name), False)

    @mock.patch.object(os, 'makedirs')
    def test_bad_makedirs(self, mock_makedirs):
        """Test a error return from a file not ready to pull."""
        mock_makedirs.side_effect = OSError(mock.Mock(), 'Error')
        c_util = Cartutils()
        self.assertRaises(
            OSError,
            c_util.create_bundle_directories,
            'fakepath'
        )

    def test_fix_absolute_path(self):
        """Test the correct creation of paths by removing absolute paths."""
        cart_utils = Cartutils()
        return_one = cart_utils.fix_absolute_path('tmp/foo.text')
        return_two = cart_utils.fix_absolute_path('/tmp/foo.text')
        return_three = cart_utils.fix_absolute_path('/tmp/foo.text')
        self.assertEqual(return_one, 'tmp/foo.text')
        self.assertEqual(return_two, 'tmp/foo.text')
        self.assertNotEqual(return_three, '/tmp/foo.text')

    def test_check_file_size_needed(self):
        """Test that the file size returned from the archive is parsed right."""
        response = json.dumps({
            'bytes_per_level': '(24L, 0L, 0L, 0L, 0L)',
            'ctime': '1444938166',
            'file': '/myemsl-dev/bundle/file.1',
            'file_storage_media': 'disk',
            'filesize': '24',
            'message': 'File was found',
            'mtime': '1444938166'
        })
        test_cart = self.create_sample_cart()
        test_file = self.create_sample_file(test_cart)
        cart_utils = Cartutils()
        file_size = cart_utils.check_file_size_needed(
            response,
            test_file,
            test_cart
        )
        self.assertEqual(file_size, 24)
        self.assertNotEqual(test_file.status, 'error')

        # now check for an error by sending a bad response
        file_size = cart_utils.check_file_size_needed(
            '',
            test_file,
            test_cart
        )
        self.assertEqual(file_size, -1)
        self.assertEqual(test_file.status, 'error')

    def test_check_space_requirements(self):
        """Test that there is enough space on the volume for the file."""
        test_cart = self.create_sample_cart()
        test_file = self.create_sample_file(test_cart)
        cart_utils = Cartutils()
        rtn = cart_utils.check_space_requirements(
            test_file,
            test_cart,
            10,
            False
        )
        self.assertEqual(rtn, True)
        self.assertNotEqual(test_file.status, 'error')

        # now check for an error by sending a way to large size needed number
        rtn = cart_utils.check_space_requirements(
            test_file,
            test_cart,
            9999999999999999999999,
            True
        )
        self.assertEqual(rtn, False)
        self.assertEqual(test_file.status, 'error')

    @mock.patch.object(psutil, 'disk_usage')
    def test_check_space_bad_path(self, mock_disk_usage):
        """Test that the error when a bad path."""
        test_cart = self.create_sample_cart()
        test_file = self.create_sample_file(test_cart)
        cart_utils = Cartutils()
        mock_disk_usage.side_effect = psutil.Error(mock.Mock())
        rtn = cart_utils.check_space_requirements(
            test_file,
            test_cart,
            10,
            False
        )
        self.assertEqual(rtn, False)
        self.assertEqual(test_file.status, 'error')

    def test_get_path_size(self):
        """Test to see if the path size of a directory is returned."""
        cart_utils = Cartutils()
        path = os.path.dirname(os.path.realpath(__file__))
        rtn = cart_utils.get_path_size(path + '/../')
        self.assertNotEqual(rtn, 0)

    def test_check_file_not_ready_pull(self):
        """Test that checks to see if a file is not ready to pull by checking the archive response."""
        response = json.dumps({
            'bytes_per_level': '(0L, 24L, 0L, 0L, 0L)',
            'ctime': '1444938166',
            'file': '/myemsl-dev/bundle/file.1',
            'file_storage_media': 'tape',
            'filesize': '24',
            'message': 'File was found',
            'mtime': '1444938166'
        })
        resp_bad = json.dumps({
            'bytes_per_level': '(0L, 33L, 33L, 0L, 0L)',
            'ctime': '1444938177',
            'file': '/myemsl-dev/bundle/file.2',
            'filesize': '33',
            'message': 'File was found',
            'mtime': '1444938133'
        })
        test_cart = self.create_sample_cart()
        test_file = self.create_sample_file(test_cart)
        cart_utils = Cartutils()
        ready = cart_utils.check_file_ready_pull(
            response,
            test_file,
            test_cart
        )
        self.assertEqual(ready, False)

        # now check for an error by sending a bad response
        ready = cart_utils.check_file_ready_pull('', test_file, test_cart)
        self.assertEqual(ready, -1)
        self.assertEqual(test_file.status, 'error')

        # now check for an error with storage media
        ready = cart_utils.check_file_ready_pull(
            resp_bad,
            test_file,
            test_cart
        )
        self.assertEqual(ready, -1)
        self.assertEqual(test_file.status, 'error')

    def test_check_file_ready_pull(self):
        """Test that checks to see if a file is ready to pull by checking the archive response."""
        response = json.dumps({
            'bytes_per_level': '(24L, 0L, 0L, 0L, 0L)',
            'ctime': '1444938166',
            'file': '/myemsl-dev/bundle/file.1',
            'file_storage_media': 'disk',
            'filesize': '24',
            'message': 'File was found',
            'mtime': '1444938166'
        })
        test_cart = self.create_sample_cart()
        test_file = self.create_sample_file(test_cart)
        cart_utils = Cartutils()
        ready = cart_utils.check_file_ready_pull(
            response,
            test_file,
            test_cart
        )
        self.assertEqual(ready['enough_space'], True)
        self.assertNotEqual(test_file.status, 'error')

    def test_delete_cart_bundle(self):
        """Test that trys to delete a cart bundle."""
        test_cart = self.create_sample_cart()
        cart_utils = Cartutils()
        os.makedirs(test_cart.bundle_path, 0o777)
        deleted = cart_utils.delete_cart_bundle(test_cart)
        self.assertEqual(deleted, True)
        self.assertEqual(test_cart.status, 'deleted')
        self.assertEqual(os.path.isdir(test_cart.bundle_path), False)

    @mock.patch.object(shutil, 'rmtree')
    def test_delete_cart_bundle_fail(self, mock_rmtree):
        """Test that trys to delete a cart bundle but fails."""
        test_cart = self.create_sample_cart()
        cart_utils = Cartutils()
        os.makedirs(test_cart.bundle_path, 0o777)
        mock_rmtree.side_effect = OSError(mock.Mock(), 'Error')
        deleted = cart_utils.delete_cart_bundle(test_cart)
        self.assertNotEqual(test_cart.status, 'deleted')
        self.assertEqual(deleted, False)
        self.assertEqual(os.path.isdir(test_cart.bundle_path), True)

    def test_set_file_status(self):
        """Test that trys to set a specific files status."""
        test_cart = self.create_sample_cart()
        test_file = self.create_sample_file(test_cart)
        cart_utils = Cartutils()

        cart_utils.set_file_status(
            test_file,
            test_cart,
            'error',
            'fake error'
        )
        self.assertEqual(test_file.status, 'error')
        self.assertEqual(test_file.error, 'fake error')

    def test_status_details_fail(self):
        """Test status details fail."""
        test_cart = self.create_sample_cart()
        test_file = self.create_sample_file(test_cart)
        cart_utils = Cartutils()

        # say file is way to big
        retval = cart_utils.check_status_details(
            test_cart,
            test_file,
            99999999999999999999999999999,
            1
        )
        self.assertEqual(retval, -1)

    def test_cart_no_hash_passed(self):
        """Test error with cart with no hash passed."""
        test_cart = self.create_sample_cart()
        cart_utils = Cartutils()

        data = json.loads(
            '{"fileids": [{"id":"foo.txt", "path":"1/2/3/foo.txt", "hashtype":"md5"}]}'
        )

        file_ids = data['fileids']
        retval = cart_utils.update_cart_files(test_cart, file_ids)
        self.assertNotEqual(retval, None)

    def test_lru_cart_delete(self):
        """Test that trys to delete a cart."""
        test_cart = self.create_sample_cart()
        test_cart2 = Cart.create(
            cart_uid='2',
            status='staging',
            bundle_path='/tmp/2/',
            updated_date=1
        )
        cart_utils = Cartutils()
        os.makedirs(test_cart2.bundle_path, 0o777)
        retval = cart_utils.lru_cart_delete(test_cart)
        self.assertEqual(retval, True)
        test_c2 = Cart.get(Cart.id == test_cart2.id)
        self.assertEqual(test_c2.status, 'deleted')
        # also hit error block when nothing to delete
        retval = cart_utils.lru_cart_delete(test_cart)
        self.assertEqual(retval, False)

    def test_bad_cart_status(self):
        """Test getting a status of a cart that doesnt exist."""
        cart_utils = Cartutils()
        retval = cart_utils.cart_status('2')
        self.assertEqual(retval[0], 'error')

    def test_bad_available_cart(self):
        """Test getting a cart that doesnt exist."""
        cart_utils = Cartutils()
        retval = cart_utils.available_cart('2')
        self.assertEqual(retval, None)

    @mock.patch.object(Cartutils, 'delete_cart_bundle')
    def test_bad_stage(self, mock_delete_cart):
        """Test the bad stage of a archive file."""
        test_cart = Cart.create(cart_uid='1', status='staging')

        def fake_database_connect(cls_name):  # pragma: no cover testing code
            """No error."""
            return cls_name

        def fake_database_close(cls_name):  # pragma: no cover testing code
            """No error."""
            return cls_name
        pacifica.cartd.orm.CartBase.database_close = MethodType(
            fake_database_close, pacifica.cartd.orm.CartBase)
        pacifica.cartd.orm.CartBase.database_connect = MethodType(
            fake_database_connect, pacifica.cartd.orm.CartBase)
        pacifica.cartd.orm.CartBase.throw_error = False
        mock_delete_cart.return_value = False
        cart_util = Cartutils()
        return_val = cart_util.remove_cart(test_cart.id, lambda x, terminate: x)
        self.assertEqual(return_val, None)
