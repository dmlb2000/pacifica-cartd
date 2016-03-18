"""
File used to unit test the pacifica_cart
"""
import unittest
import os
from playhouse.test_utils import test_database
from peewee import SqliteDatabase
from cart.cart_orm import Cart, File
from cart.cart_utils import Cartutils

TEST_DB = SqliteDatabase(':memory:')

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
            self.assertEqual(deleted, True)


if __name__ == '__main__':
    unittest.main()
