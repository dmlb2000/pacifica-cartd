"""
File used to unit test the pacifica_cart
"""
import unittest
import os
import sys
from json import loads
from tempfile import mkstemp, mkdtemp
from playhouse.test_utils import test_database
from peewee import SqliteDatabase
import cart.cart_orm
from cart.cart_orm import Cart, File
from cart.cart_utils import Cartutils
from cart.cart_interface import fix_cart_uid, is_valid_uid, CartGenerator

TEST_DB = SqliteDatabase(':memory:')
FILE_TEST_DB = SqliteDatabase(mkstemp(suffix='.sqlite3')[1])
cart.cart_orm.DB = TEST_DB

class TestCartUtils(unittest.TestCase):
    """
    Contains all the tests for the CartUtils class
    """

    def test_create_download_path(self):
        """test the creation of the download path for a cart file"""
        with test_database(TEST_DB, (Cart, File)):
            test_cart = Cart.create(cart_uid='1', status="staging")
            test_file = File.create(cart=test_cart, file_name="1.txt",
                                    bundle_path="/tmp/1/1.txt")
            cart_utils = Cartutils()
            success = cart_utils.create_download_path(test_file, test_cart,
                                                      test_file.bundle_path)
            directory_name = os.path.dirname(test_file.bundle_path)
            self.assertEqual(success, True)
            self.assertEqual(os.path.isdir(directory_name), True)

            os.rmdir(directory_name)
            self.assertEqual(os.path.isdir(directory_name), False)

    def test_create_bundle_directories(self):
        """test the creation of direcoties were files will be saved"""
        directory_name = "/tmp/fakedir/"
        cart_utils = Cartutils()
        cart_utils.create_bundle_directories(directory_name)
        self.assertEqual(os.path.isdir(directory_name), True)
        os.rmdir(directory_name)
        self.assertEqual(os.path.isdir(directory_name), False)

    def test_fix_absolute_path(self):
        """test the correct creation of paths by removing absolute paths"""
        cart_utils = Cartutils()
        return_one = cart_utils.fix_absolute_path("tmp/foo.text")
        return_two = cart_utils.fix_absolute_path("/tmp/foo.text")
        return_three = cart_utils.fix_absolute_path("/tmp/foo.text")
        self.assertEqual(return_one, "tmp/foo.text")
        self.assertEqual(return_two, "tmp/foo.text")
        self.assertNotEqual(return_three, "/tmp/foo.text")

    def test_check_file_size_needed(self):
        """test that the file size returned from the archive is parsed right"""
        with test_database(TEST_DB, (Cart, File)):
            response = """{
                            "bytes_per_level": "(24L, 0L, 0L, 0L, 0L)", 
                            "ctime": "1444938166", 
                            "file": "/myemsl-dev/bundle/file.1", 
                            "file_storage_media": "disk", 
                            "filesize": "24", 
                            "message": "File was found", 
                            "mtime": "1444938166"
                            }"""
            test_cart = Cart.create(cart_uid='1', status="staging")
            test_file = File.create(cart=test_cart, file_name="1.txt",
                                    bundle_path="/tmp/1/1.txt")
            cart_utils = Cartutils()
            file_size = cart_utils.check_file_size_needed(response, test_file,
                                                          test_cart)
            self.assertEqual(file_size, 24)
            self.assertNotEqual(test_file.status, "error")

            #now check for an error by sending a bad response
            file_size = cart_utils.check_file_size_needed("", test_file,
                                                          test_cart)
            self.assertEqual(file_size, -1)
            self.assertEqual(test_file.status, "error")

    def test_check_space_requirements(self):
        """test that there is enough space on the volume for the file"""
        with test_database(TEST_DB, (Cart, File)):

            test_cart = Cart.create(cart_uid='1', status="staging")
            test_file = File.create(cart=test_cart, file_name="1.txt",
                                    bundle_path="/tmp/1/1.txt")
            cart_utils = Cartutils()
            rtn = cart_utils.check_space_requirements(test_file, test_cart,
                                                      10, False)
            self.assertEqual(rtn, True)
            self.assertNotEqual(test_file.status, "error")

            #now check for an error by sending a way to large size needed number
            rtn = cart_utils.check_space_requirements(test_file, test_cart,
                                                      9999999999999999999999, False)
            self.assertEqual(rtn, False)
            self.assertEqual(test_file.status, "error")

    def test_get_path_size(self):
        """test to see if the path size of a directory is returned"""

        cart_utils = Cartutils()
        path = os.path.dirname(os.path.realpath(__file__))
        rtn = cart_utils.get_path_size(path)
        self.assertNotEqual(rtn, 0)

    def test_check_file_ready_pull(self):
        """test that checks to see if a file is ready to pull
        by checking the archive response"""
        with test_database(TEST_DB, (Cart, File)):
            response = """{
                            "bytes_per_level": "(24L, 0L, 0L, 0L, 0L)", 
                            "ctime": "1444938166", 
                            "file": "/myemsl-dev/bundle/file.1", 
                            "file_storage_media": "disk", 
                            "filesize": "24", 
                            "message": "File was found", 
                            "mtime": "1444938166"
                            }"""
            test_cart = Cart.create(cart_uid='1', status="staging")
            test_file = File.create(cart=test_cart, file_name="1.txt",
                                    bundle_path="/tmp/1/1.txt")
            cart_utils = Cartutils()
            ready = cart_utils.check_file_ready_pull(response, test_file,
                                                     test_cart)
            self.assertEqual(ready, True)
            self.assertNotEqual(test_file.status, "error")

            #now check for an error by sending a bad response
            ready = cart_utils.check_file_size_needed("", test_file,
                                                      test_cart)
            self.assertEqual(ready, -1)
            self.assertEqual(test_file.status, "error")

    def test_delete_cart_bundle(self):
        """test that trys to delete a cart bundle"""
        with test_database(TEST_DB, (Cart, File)):

            test_cart = Cart.create(cart_uid='1', status="staging",
                                    bundle_path="/tmp/1/")
            cart_utils = Cartutils()
            os.makedirs(test_cart.bundle_path, 0777)
            deleted = cart_utils.delete_cart_bundle(test_cart)
            self.assertEqual(test_cart.status, "deleted")
            self.assertEqual(deleted, True)
            self.assertEqual(os.path.isdir(test_cart.bundle_path), False)

    def test_set_file_status(self):
        """test that trys to set a specific files status"""
        with test_database(TEST_DB, (Cart, File)):

            test_cart = Cart.create(cart_uid='1', status="staging",
                                    bundle_path="/tmp/1/")
            test_file = File.create(cart=test_cart, file_name="1.txt",
                                    bundle_path="/tmp/1/1.txt")
            cart_utils = Cartutils()
            cart_utils.set_file_status(test_file, test_cart, "error", "fake error")
            self.assertEqual(test_file.status, "error")
            self.assertEqual(test_file.error, "fake error")

class TestEnvGlobals(unittest.TestCase):
    """
    Contains the tests for the global config module
    """
    def test_set_logging(self):
        """test that logging gets set for debugging"""
        os.environ['DATABASE_LOGGING'] = 'True'
        import importlib
        # first delete the module from the loaded modules
        del sys.modules['cart.cart_env_globals']
        # then we import the module
        mod = importlib.import_module("cart.cart_env_globals")
        # make sure the LOGGER attribute in the module exists
        self.assertTrue(getattr(mod, 'LOGGER'))

class TestCartInterface(unittest.TestCase):
    """
    Contains all the tests for the Cart Interface
    """
    def test_cart_int_get(self):
        """Testing the cart interface get method"""
        saved_state = {}
        def start_response(*args):
            """stub for start_response to do some checking"""
            self.assertEqual(args[0], '200 OK')
            self.assertEqual(args[1][0][0], 'Content-Type')
            self.assertEqual(args[1][0][1], 'application/octet-stream')
        def file_wrapper(rfd, blksize):
            """stub for file_wrapper to do some checking"""
            self.assertEqual(blksize, 1<<20)
            self.assertEqual(type(rfd), file)
            saved_state['fd'] = rfd
            return iter(lambda: rfd.read(blksize), '')
        env = {
            'PATH_INFO': '/123',
            'wsgi.file_wrapper': file_wrapper
        }
        with test_database(FILE_TEST_DB, (Cart, File)):
            sample_cart = Cart()
            sample_cart.cart_uid = 123
            sample_cart.bundle_path = mkdtemp()
            sample_cart.status = 'ready'
            sample_cart.save(force_insert=True)
            FILE_TEST_DB.close()
            cgen = CartGenerator()
            tarfile_read = cgen.get(env, start_response)
            for buf in tarfile_read:
                self.assertTrue(len(buf) > 0)
            saved_state['fd'].close()

    def test_invalid_cart_uid(self):
        """Testing the cart interface get against not valid cart uid"""
        def start_response(*args):
            """stub for start_response to do some checking"""
            self.assertEqual(args[0], '200 OK')
            self.assertEqual(args[1][0][0], 'Content-Type')
            self.assertEqual(args[1][0][1], 'application/json')
        env = {
            'PATH_INFO': '/'
        }
        with test_database(FILE_TEST_DB, (Cart, File)):
            FILE_TEST_DB.close()
            cgen = CartGenerator()
            data = cgen.get(env, start_response)
            self.assertEqual(loads(data)['message'], "The uid was not valid")

    def test_not_ready_cart(self):
        """Testing the cart interface get against not ready cart"""
        def start_response(*args):
            """stub for start_response to do some checking"""
            self.assertEqual(args[0], '500 OK')
            self.assertEqual(args[1][0][0], 'Content-Type')
            self.assertEqual(args[1][0][1], 'application/json')
        env = {
            'PATH_INFO': '/123'
        }
        with test_database(FILE_TEST_DB, (Cart, File)):
            sample_cart = Cart()
            sample_cart.cart_uid = 123
            sample_cart.bundle_path = mkdtemp()
            sample_cart.save(force_insert=True)
            FILE_TEST_DB.close()
            cgen = CartGenerator()
            data = cgen.get(env, start_response)
            self.assertEqual(loads(data)['message'], "The cart is not ready for download")

    def test_fix_cart_uid(self):
        """ Testing the create filepath cleanup"""
        path = fix_cart_uid('test/')
        self.assertEqual(path, "test/")
        path = fix_cart_uid('test')
        self.assertEqual(path, "test")
        path = fix_cart_uid('/test')
        self.assertEqual(path, "test")

    def test_is_valid_uid(self):
        """ Testing if the passed guids are valid"""
        valid = is_valid_uid('3434')
        self.assertEqual(valid, True)
        valid = is_valid_uid(None)
        self.assertEqual(valid, False)
        valid = is_valid_uid('')
        self.assertEqual(valid, False)
        valid = is_valid_uid('foo')
        self.assertEqual(valid, True)
        valid = is_valid_uid('')
        self.assertEqual(valid, False)
