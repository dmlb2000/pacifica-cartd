from __future__ import absolute_import
from cart.tasks import write_message
from cart.cart_orm import database_setup

database_setup()
result = write_message.delay("Im a happy message")
print result
print result.get()
