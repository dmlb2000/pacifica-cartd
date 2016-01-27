from __future__ import absolute_import
from cart.celery import cart_app
from cart.cart_orm import Cart, File, db
from os import path
import os
import time

VOLUME_PATH = os.environ['VOLUME_PATH']
ARCHIVE_INTERFACE_URL = os.environ['ARCHIVE_INTERFACE_URL']

def fix_absolute_path(filepath):
    """Removes / from front of path"""
    if path.isabs(filepath):
        filepath = filepath[1:]
    return filepath

def updateCartFiles(uuid, fileIds):
    """Update the files associated to a cart"""
    with db.atomic():
        for fId in fileIds:
            filepath = fix_absolute_path(fId["path"])
            File.create(cart_uuid=uuid, file_id=fId["id"], bundle_path=filepath)


@cart_app.task(ignore_result=True)
def stageFiles(fileIds, uuid):
    """Tell the files to be staged on the backend system """
    db.connect()
    try:
        mycart = Cart.get(Cart.cart_uuid == str(uuid))
    except Exception as ex:
        #case if no record exists yet in database
        mycart = None 

    if not mycart:
        mycart = Cart(cart_uuid=uuid, status="staging")
        mycart.save()
    #with update or new, need to add in files
    updateCartFiles(uuid, fileIds)

    getFilesLocally.delay(mycart.cart_uuid)
    prepareBundle.delay(mycart.cart_uuid)

    

@cart_app.task(ignore_result=True)
def getFilesLocally(uuid):
    """Pull the files to the local system from the backend """
    #tell each file to be pulled
    for f in File.select().where(File.cart_uuid == uuid):
        pullFile.delay(f.id)

@cart_app.task(ignore_result=True)
def prepareBundle(uuid):
    toBundleFlag = True
    for f in File.select().where(File.cart_uuid == uuid):
        if (f.status == "error"):
            #error pulling file so try again
            toBundleFlag = False
            pullFile.delay(f.id)

        elif (f.status != "staged"):
            toBundleFlag = False

    if (toBundleFlag == False):
        #if not ready to bundle recall this task
        prepareBundle.delay(uuid)

    else:
        #All files are local...try to tar
        tarFiles.delay(uuid)

@cart_app.task(ignore_result=True)
def pullFile(fId):
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
        f.status = "staged"
        f.save()
    except Exception as ex:
        #if curl fails...write error
        f.status = "error"
        f.save()
    return True

@cart_app.task(ignore_result=True)
def tarFiles(uuid):
    """Start to bundle all the files together"""
    #make sure to check size here and make sure enough space is available
    db.connect()
    mycart = Cart.get(Cart.cart_uuid == uuid)
    mycart.status = "bundling"
    mycart.save()
    #get a path to where the tar will be
    #for each file put into bundle here
    #update the carts status and bundle path
    mycart.status = "ready"
    mycart.bundle_path = VOLUME_PATH + mycart.cart_uuid + ".tar"
    mycart.save()
    db.close()

@cart_app.task
def cartStatus(uuid):
    """Get the status of a specified cart""" 
    db.connect()
    status = None
    try:
        mycart = Cart.get(Cart.cart_uuid == str(uuid))
    except Exception as ex:
        #case if no record exists yet in database
        mycart = None
        status = ["error","No cart with uuid "+ uuid + " found"] 
    
    if mycart:
        status = [mycart.status,""]

    db.close()
    return status

@cart_app.task
def availableCart(uuid):
    """Checks if the asked for cart tar is available
       returns the path to tar if yes, false if not"""
    db.connect()
    cartBundlePath = False
    try:
        mycart = Cart.get(Cart.cart_uuid == str(uuid))
    except Exception as ex:
        #case if no record exists yet in database
        mycart = None

    if mycart and mycart.status == "ready":
        cartBundlePath = mycart.bundle_path
        
    return cartBundlePath

