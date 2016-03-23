"""Module that contains all the amqp tasks that support the
cart infrastructure
"""

from __future__ import absolute_import
import os
import datetime
import pycurl
from peewee import DoesNotExist
from cart.celery import CART_APP
from cart.cart_orm import Cart, File, database_connect, database_close
from cart.cart_utils import Cartutils
from cart.cart_env_globals import VOLUME_PATH
from cart.archive_requests import ArchiveRequests


@CART_APP.task(ignore_result=True)
def stage_files(file_ids, uid):
    """Tell the files to be staged on the backend system """
    database_connect()
    mycart = Cart(cart_uid=uid, status="staging")
    mycart.save()
    #with update or new, need to add in files
    cart_utils = Cartutils()
    cart_utils.update_cart_files(mycart, file_ids)

    get_files_locally.delay(mycart.id)
    prepare_bundle.delay(mycart.id)
    database_close()

@CART_APP.task(ignore_result=True)
def get_files_locally(cartid):
    """Pull the files to the local system from the backend """
    #tell each file to be pulled
    database_connect()
    for cart_file in File.select().where(File.cart == cartid):
        pull_file.delay(cart_file.id, False)
    database_close()

@CART_APP.task(ignore_result=True)
def prepare_bundle(cartid):
    """Checks to see if all the files are staged locally
    before calling the bundling action.  If not will call
    itself to continue the waiting process
    """
    database_connect()
    bundle_flag = True
    for c_file in File.select().where(File.cart == cartid):
        if c_file.status == "error":
            #error pulling file so set cart error and return
            try:
                mycart = Cart.get(Cart.id == cartid)
                mycart.status = "error"
                mycart.error = "Failed to pull file(s)"
                mycart.updated_date = datetime.datetime.now()
                mycart.save()
                database_close()
                return
            except DoesNotExist:
                #case if record no longer exists
                database_close()
                return

        elif c_file.status != "staged":
            bundle_flag = False

    if not bundle_flag:
        #if not ready to bundle recall this task
        prepare_bundle.delay(cartid)

    else:
        #All files are local...try to tar
        tar_files.delay(cartid)
    database_close()


@CART_APP.task(ignore_result=True)
def pull_file(file_id, record_error):
    """Pull a file from the archive  """
    database_connect()
    try:
        cart_file = File.get(File.id == file_id)
        mycart = cart_file.cart
        cart_utils = Cartutils()
        cart_utils.set_file_status(cart_file, mycart, "staging", False)
        #make sure cart wasnt deleted before pulling file
        if mycart.deleted_date:
            return
    except DoesNotExist:
        database_close()
        return

    archive_request = ArchiveRequests()
    #stage the file on the archive.  True on success, False on fail
    try:
        archive_request.stage_file(cart_file.file_name)
    except pycurl.error as ex:
        error_msg = "Failed to stage with error: " + str(ex)
        cart_utils.set_file_status(cart_file, mycart, "error", error_msg)

    #check to see if file is available to pull from archive interface
    try:
        response = archive_request.status_file(cart_file.file_name)
    except pycurl.error:
        error_msg = "Failed to status file with error: " + str(ex)
        cart_utils.set_file_status(cart_file, mycart, "error", error_msg)
        response = False

    size_needed = cart_utils.check_file_size_needed(response, cart_file, mycart)
    mod_time = cart_utils.check_file_modified_time(response, cart_file, mycart)
    #Return from function if the values couldnt be parsed (-1 return)
    if size_needed < 0 or mod_time < 0:
        database_close()
        return

    ready_to_pull = cart_utils.check_file_ready_pull(
        response, cart_file, mycart)

    #Check to see if ready to pull.  If not recall this to check again
    # error on less then 0
    if ready_to_pull < 0:
        database_close()
        return
    elif not ready_to_pull:
        pull_file.delay(file_id, False)
        database_close()
        return

    #create the path the file will be downloaded to
    abs_cart_file_path = os.path.join(
        VOLUME_PATH, str(mycart.id), mycart.cart_uid, cart_file.bundle_path)
    path_created = cart_utils.create_download_path(
        cart_file, mycart, abs_cart_file_path)
    #Check size here and make sure enough space is available.
    enough_space = cart_utils.check_space_requirements(
        cart_file, mycart, size_needed, True)

    if path_created and enough_space:
        try:
            #curl here to download from the archive interface
            archive_request.pull_file(cart_file.file_name, abs_cart_file_path)
            cart_utils.set_file_status(cart_file, mycart, "staged", False)
            database_close()
        except pycurl.error as ex:
            #if curl fails...try a second time, if that fails write error
            if record_error:
                error_msg = "Failed to pull with error: " + str(ex)
                cart_utils.set_file_status(
                    cart_file, mycart, "error", error_msg)
                database_close()
            else:
                pull_file.delay(file_id, True)
                database_close()

        os.utime(abs_cart_file_path, (mod_time, mod_time))


@CART_APP.task(ignore_result=True)
def tar_files(cartid):
    """Start to bundle all the files together
    Due to streaming the tar we dont need to try and bundle
    everything together"""

    database_connect()
    try:
        mycart = Cart.get(Cart.id == cartid)
        bundle_path = os.path.join(
            VOLUME_PATH, str(mycart.id), (mycart.cart_uid))
        mycart.status = "ready"
        mycart.bundle_path = bundle_path
        mycart.updated_date = datetime.datetime.now()
        mycart.save()
    except DoesNotExist:
        #case if record no longer exists
        database_close()
        return

    database_close()
