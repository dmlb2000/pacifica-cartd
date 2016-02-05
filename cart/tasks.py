from __future__ import absolute_import
from cart.celery import CART_APP
from cart.cart_orm import Cart, File, DB
from os import path
import os
import time
import pycurl
from StringIO import StringIO

VOLUME_PATH = os.environ['VOLUME_PATH']
ARCHIVE_INTERFACE_URL = os.environ['ARCHIVE_INTERFACE_URL']

def fix_absolute_path(filepath):
    """Removes / from front of path"""
    if path.isabs(filepath):
        filepath = filepath[1:]
    return filepath

def updateCartFiles(cartid, fileIds):
    """Update the files associated to a cart"""
    with DB.atomic():
        for fId in fileIds:
            filepath = fix_absolute_path(fId["path"])
            File.create(cart=cartid, file_id=fId["id"], bundle_path=filepath)


@CART_APP.task(ignore_result=True)
def stageFiles(fileIds, uuid):
    """Tell the files to be staged on the backend system """
    DB.connect()
    try:
        mycart = Cart.get(Cart.cart_uuid == str(uuid))
    except Exception as ex:
        #case if no record exists yet in database
        mycart = None

    if not mycart:
        mycart = Cart(cart_uuid=uuid, status="staging")
        mycart.save()
    #with update or new, need to add in files
    updateCartFiles(mycart.id, fileIds)

    getFilesLocally.delay(mycart.id)
    prepareBundle.delay(mycart.id)

@CART_APP.task(ignore_result=True)
def getFilesLocally(cartid):
    """Pull the files to the local system from the backend """
    #tell each file to be pulled
    for f in File.select().where(File.cart == cartid):
        pullFile.delay(f.id, False)

@CART_APP.task(ignore_result=True)
def prepareBundle(cartid):
    toBundleFlag = True
    for f in File.select().where(File.cart == cartid):
        if f.status == "error":
            #error pulling file so set cart error and return
            try:
                mycart = Cart.get(Cart.id == cartid)
                mycart.status = "error"
                mycart.error = "Failed to pull file(s)"
                mycart.save()
                return
            except Exception as ex:
                #case if record no longer exists
                return

        elif f.status != "staged":
            toBundleFlag = False

    if toBundleFlag == False:
        #if not ready to bundle recall this task
        prepareBundle.delay(cartid)

    else:
        #All files are local...try to tar
        tarFiles.delay(cartid)

@CART_APP.task(ignore_result=True)
def pullFile(fId, record_error):
    """Pull a file from the archive  """
    #make sure to check size here and make sure enough space is available
    try:
        f = File.get(File.id == fId)
        f.status = "staging"
        f.save
    except Exception as ex:
        f = None
        return

    #do the curl to get the file from archive
    try:
        #curl here
        filePullCurl('/shared/' + f.file_id)
        f.status = "staged"
        f.save()
    except Exception as ex:
        #if curl fails...try a second time, if that fails write error
        if record_error:
            f.status = "error"
            f.error = "Failed to pull with error: " + str(ex)
            f.save()
        else:
            pullFile.delay(fId, True)

@CART_APP.task(ignore_result=True)
def tarFiles(cartid):
    """Start to bundle all the files together"""
    #make sure to check size here and make sure enough space is available
    DB.connect()
    mycart = Cart.get(Cart.id == cartid)
    mycart.status = "bundling"
    mycart.save()
    #get a path to where the tar will be
    #for each file put into bundle here
    #update the carts status and bundle path
    mycart.status = "ready"
    mycart.bundle_path = VOLUME_PATH + mycart.cart_uuid + ".tar"
    mycart.save()
    DB.close()

@CART_APP.task
def cartStatus(uuid):
    """Get the status of a specified cart"""
    DB.connect()
    status = None
    try:
        mycart = Cart.get(Cart.cart_uuid == str(uuid))
    except Exception as ex:
        #case if no record exists yet in database
        mycart = None
        status = ["error", "No cart with uuid " + uuid + " found"]
    if mycart:
        status = [mycart.status, ""]

    DB.close()
    return status

@CART_APP.task
def availableCart(uuid):
    """Checks if the asked for cart tar is available
       returns the path to tar if yes, false if not"""
    DB.connect()
    cartBundlePath = False
    try:
        mycart = Cart.get(Cart.cart_uuid == str(uuid))
    except Exception as ex:
        #case if no record exists yet in database
        mycart = None

    if mycart and mycart.status == "ready":
        cartBundlePath = mycart.bundle_path
    return cartBundlePath

def filePullCurl(filepath):
    c = pycurl.Curl()
    c.setopt(c.URL, ARCHIVE_INTERFACE_URL)
    with open(filepath, 'w') as f:
        c.setopt(c.WRITEFUNCTION, f.write)
        c.perform()

