from __future__ import absolute_import

from cart.celery import cart_app
from cart.cart_orm import Cart

@cart_app.task
def add(x, y):
    return x + y


@cart_app.task
def mul(x, y):
    return x * y


@cart_app.task
def xsum(numbers):
    return sum(numbers)

@cart_app.task
def write_message(message):
    mycart = Cart(status=message)
    mycart.save()
    return "message Inserted"

