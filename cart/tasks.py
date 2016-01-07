from __future__ import absolute_import
from cart.celery import cart_app
from cart.cart_orm import Cart

@cart_app.task
def write_message(message):
    mycart = Cart(status=message)
    mycart.save()
    return "message Inserted"

