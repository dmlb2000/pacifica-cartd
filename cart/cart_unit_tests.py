"""
File used to unit test the pacifica_cart
"""
import unittest
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
            self.assertEqual(success, True)

if __name__ == '__main__':
    unittest.main()
