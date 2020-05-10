#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Handle fixing broken carts with admin functions."""
from os import utime
from tqdm import trange
from .orm import Cart, File
from .utils import Cartutils
from .archive_requests import ArchiveRequests


@Cart.atomic()
def fixit(args):
    """Entrypoint for admin command to fix cartids."""
    for cart_index in trange(len(args.cartids), desc='Total Carts'):
        cart_id = args.cartids[cart_index]
        cart_obj = (Cart
                    .select()
                    .where(
                        (Cart.cart_uid == str(cart_id)) &
                        (Cart.deleted_date.is_null(True)))
                    .order_by(Cart.creation_date.desc())
                    .get())
        cart_obj.status = 'staging'
        cart_obj.save()
        cart_utils = Cartutils()
        archive_request = ArchiveRequests()
        file_list = list(File.select().where(File.cart == cart_obj.id).execute())
        for file_index in trange(len(file_list), desc='Number of Files'):
            c_file = file_list[file_index]
            if c_file.status == 'staged':
                continue
            cart_utils.set_file_status(c_file, cart_obj, 'staging', False)
            ready = False
            while not ready:
                archive_request.stage_file(c_file.file_name)
                response = archive_request.status_file(c_file.file_name)
                ready = cart_utils.check_file_ready_pull(response, c_file, cart_obj)
                if isinstance(ready, int) and ready < 0:  # pragma: no cover hard to get here with error
                    raise c_file.error
                if ready:
                    archive_request.pull_file(
                        c_file.file_name, ready['filepath'], c_file.hash_value, c_file.hash_type)
                    cart_utils.set_file_status(c_file, cart_obj, 'staged', False)
                    modtime = ready['modtime']
                    utime(ready['filepath'], (int(float(modtime)), int(float(modtime))))
        cart_utils.prepare_bundle(cart_obj.id)
