from __future__ import absolute_import
from cart.celery import CART_APP
from cart.cart_orm import Cart, File, DB, database_connect, database_close
from cart.cart_utils import cart_utils
from os import path
from cart.cart_env_globals import VOLUME_PATH, ARCHIVE_INTERFACE_URL, LRU_BUFFER_TIME
from cart.archivei_requests import archivei_requests
import os
import time
import json
import datetime
import errno
import psutil
import pycurl
from StringIO import StringIO
import shutil
import logging

"""Uncomment these lines for database query logging"""
#logger = logging.getLogger('peewee')
#logger.setLevel(logging.DEBUG)
#logger.addHandler(logging.StreamHandler())



@CART_APP.task(ignore_result=True)
def stage_files(fileIds, uid):
    """Tell the files to be staged on the backend system """
    database_connect()
    mycart = Cart(cart_uid=uid, status="staging")
    mycart.save()
    #with update or new, need to add in files
    cart_utils.updateCartFiles(mycart, fileIds)

    get_files_locally.delay(mycart.id)
    prepare_bundle.delay(mycart.id)
    database_close()

@CART_APP.task(ignore_result=True)
def get_files_locally(cartid):
    """Pull the files to the local system from the backend """
    #tell each file to be pulled
    database_connect()
    for f in File.select().where(File.cart == cartid):
        pull_file.delay(f.id, False)
    database_close()

@CART_APP.task(ignore_result=True)
def prepare_bundle(cartid):
    """Checks to see if all the files are staged locally
    before calling the bundling action.  If not will call
    itself to continue the waiting process
    """
    database_connect()
    toBundleFlag = True
    for f in File.select().where(File.cart == cartid):
        if f.status == "error":
            #error pulling file so set cart error and return
            try:
                mycart = Cart.get(Cart.id == cartid)
                mycart.status = "error"
                mycart.error = "Failed to pull file(s)"
                mycart.updated_date = datetime.datetime.now()
                mycart.save()
                database_close()
                return
            except Exception as ex:
                #case if record no longer exists
                database_close()
                return

        elif f.status != "staged":
            toBundleFlag = False

    if toBundleFlag == False:
        #if not ready to bundle recall this task
        prepare_bundle.delay(cartid)

    else:
        #All files are local...try to tar
        tar_files.delay(cartid)
    database_close()


@CART_APP.task(ignore_result=True)
def pull_file(fId, record_error):
    """Pull a file from the archive  """
    database_connect()
    try:
        pulled_file = File.get(File.id == fId)
        pulled_file.status = "staging"
        pulled_file.save()
        mycart = pulled_file.cart
        #make sure cart wasnt deleted before pulling file
        if mycart.deleted_date:
            return
    except Exception as ex:
        pulled_file = None
        database_close()
        return

    #stage the file on the archive.  True on success, False on fail
    try:
        archivei_requests.stage_file(pulled_file.file_name)
    except Exception as ex:
        pulled_file.status = "error"
        pulled_file.error = "Failed to stage with error: " + str(ex)
        pulled_file.save()
        mycart.updated_date = datetime.datetime.now()
        mycart.save()

    #check to see if file is available to pull from archive interface
    try:
        response = archivei_requests.status_file(pulled_file.file_name)
    except Exception as ex:
        cart_file.status = "error"
        cart_file.error = "Failed to status file with error: " + str(ex)
        cart_file.save()
        mycart.updated_date = datetime.datetime.now()
        mycart.save()
        response = False
  
    size_needed = cart_utils.check_file_size_needed(response, pulled_file, mycart)

    #Return from function if the size_needed couldnt be parsed (-1 return)
    if size_needed < 0:
        database_close()
        return

    ready_to_pull = cart_utils.check_file_ready_pull(response, pulled_file, mycart)

    #Check to see if ready to pull.  If not recall this to check again
    # error on less then 0
    if ready_to_pull < 0:
        database_close()
        return
    elif ready_to_pull == False:
        pull_file.delay(fId, False)
        database_close()
        return

    #create the path the file will be downloaded to
    abs_cart_file_path = os.path.join(VOLUME_PATH, str(mycart.id), mycart.cart_uid, pulled_file.bundle_path)
    path_created = cart_utils.create_download_path(pulled_file, mycart, abs_cart_file_path)

    #Check size here and make sure enough space is available.
    enough_space = cart_utils.check_space_requirements(pulled_file, mycart, size_needed, True)

    if path_created and enough_space:
        try:
            #curl here to download from the archive interface
            archivei_requests.pull_file(pulled_file.file_name, abs_cart_file_path)
            pulled_file.status = "staged"
            pulled_file.save()
            mycart.updated_date = datetime.datetime.now()
            mycart.save()
            database_close()
        except IOError as ex:
            #if curl fails...try a second time, if that fails write error
            if record_error:
                pulled_file.status = "error"
                pulled_file.error = "Failed to pull with error: " + str(ex)
                pulled_file.save()
                mycart.updated_date = datetime.datetime.now()
                mycart.save()
                database_close()
            else:
                pullFile.delay(fId, True)
                database_close()

        return

@CART_APP.task(ignore_result=True)
def tar_files(cartid):
    """Start to bundle all the files together
    Due to streaming the tar we dont need to try and bundle
    everything together"""

    database_connect()
    try:
        mycart = Cart.get(Cart.id == cartid)
        bundle_path = os.path.join(VOLUME_PATH, str(mycart.id), (mycart.cart_uid))
        mycart.status = "ready"
        mycart.bundle_path = bundle_path
        mycart.updated_date = datetime.datetime.now()
        mycart.save()
    except Exception as ex:
        #case if record no longer exists
        database_close()
        return

    database_close()