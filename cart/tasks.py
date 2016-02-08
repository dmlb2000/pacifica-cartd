from __future__ import absolute_import
from cart.celery import CART_APP
from cart.cart_orm import Cart, File, DB
from os import path
import os
import time
import datetime
from StringIO import StringIO
import errno
import requests

BLOCK_SIZE = 1<<20

try:
    VOLUME_PATH = os.environ['VOLUME_PATH']
    #archive_int = os.getenv("ARCHIVE_INTERFACE_URL")
    if "ARCHIVE_INTERFACE_URL" in os.environ:
        ARCHIVE_INTERFACE_URL = os.getenv("ARCHIVE_INTERFACE_URL")
    else:
        ARCHIVE_INTERFACE_ADDR = os.environ['ARCHIVEI_PORT_8080_TCP_ADDR']
        ARCHIVE_INTERFACE_PORT = os.environ['ARCHIVEI_PORT_8080_TCP_PORT']
        # check if it already exists first, if not do this, else take the part that is filled out
        ARCHIVE_INTERFACE_URL = ('http://' + ARCHIVE_INTERFACE_ADDR + ':' + ARCHIVE_INTERFACE_PORT + '/')
except Exception as ex:
    print "Error with environment variable: " + str(ex)

def fix_absolute_path(filepath):
    """Removes / from front of path"""
    if os.path.isabs(filepath):
        filepath = filepath[1:]
    return filepath

def updateCartFiles(cart, fileIds):
    """Update the files associated to a cart"""
    with DB.atomic():
        for fId in fileIds:
            filepath = fix_absolute_path(fId["path"])
            File.create(cart=cart, file_name=fId["id"], bundle_path=filepath)
            cart.updated_date = datetime.datetime.now()
            cart.save()



@CART_APP.task(ignore_result=True)
def stageFiles(fileIds, uid):
    """Tell the files to be staged on the backend system """
    DB.connect()
    mycart = Cart(cart_uid=uid, status="staging")
    mycart.save()
    #with update or new, need to add in files
    updateCartFiles(mycart, fileIds)

    getFilesLocally.delay(mycart.id)
    prepareBundle.delay(mycart.id)

@CART_APP.task(ignore_result=True)
def getFilesLocally(cartid):
    """Pull the files to the local system from the backend """
    #tell each file to be pulled
    for f in File.select().where(File.cart == cartid):
        pullFile.delay(f.id, False, True)

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
                mycart.updated_date = datetime.datetime.now()
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
def pullFile(fId, record_error, stage_file):
    """Pull a file from the archive  """
    try:
        f = File.get(File.id == fId)
        f.status = "staging"
        f.save
        mycart = f.cart 
    except Exception as ex:
        f = None
        return


    #stage the file if neccasary on the archive
    if (stage_file):
        try:
            archive_stage_file(f.file_name)
        except Exception as ex:
            f.status = "error"
            f.error = "Failed to stage with error: " + str(ex)
            f.save()
            mycart.updated_date = datetime.datetime.now()
            mycart.save()
            return

    #check to see if file is available to pull from archive interface
    try:
        response = archive_status_file(f.file_name)
    except Exception as ex:
        f.status = "error"
        f.error = "Failed to status file with error: " + str(ex)
        f.save()
        mycart.updated_date = datetime.datetime.now()
        mycart.save()
        return


    #make sure to check size here and make sure enough space is available

    try:
              
        abs_cart_file_path = os.path.join(VOLUME_PATH, str(mycart.id), mycart.cart_uid, f.bundle_path)
        cart_file_dirs = os.path.dirname(abs_cart_file_path)
        path_created_flag = create_bundle_directories(cart_file_dirs)
    except Exception as ex:

        f.status = "error"
        f.error = "Failed to create directories with error: " + str(ex)
        f.save()
        mycart.updated_date = datetime.datetime.now()
        mycart.save()
        return

    if path_created_flag:
        try:
            #curl here
            filePullCurl(f.file_name, abs_cart_file_path)
            f.status = "staged"
            f.save()
            mycart.updated_date = datetime.datetime.now()
            mycart.save()
        except IOError as ex:
            #if curl fails...try a second time, if that fails write error
            if(record_error):
                f.status = "error"
                f.error = "Failed to pull with error: " + str(ex)
                f.save()
                mycart.updated_date = datetime.datetime.now()
                mycart.save()
            else:
                pullFile.delay(fId, True, False)
    else:
        f.status = "error"
        f.error = "Failed to create directories inside bundle"
        f.save()
        mycart.updated_date = datetime.datetime.now()
        mycart.save()
        
    


@CART_APP.task(ignore_result=True)
def tarFiles(cartid):
    """Start to bundle all the files together"""
    #make sure to check size here and make sure enough space is available

    #tar file module for python
    #set datetime type, owners

    DB.connect()
    mycart = Cart.get(Cart.id == cartid)
    mycart.status = "bundling"
    mycart.updated_date = datetime.datetime.now()
    mycart.save()
    #get a path to where the tar will be
    #for each file put into bundle here
    #update the carts status and bundle path
    mycart.status = "ready"
    mycart.bundle_path = os.path.join(VOLUME_PATH, str(mycart.id), mycart.cart_uid)
    mycart.updated_date = datetime.datetime.now()
    mycart.save()
    DB.close()


@CART_APP.task
def cartStatus(uid):
    """Get the status of a specified cart"""
    DB.connect()
    status = None
    try:
        mycart = (Cart.select().where(Cart.cart_uid == str(uid)).order_by(Cart.creation_date.desc()).get())
    except Exception as ex:
        #case if no record exists yet in database
        mycart = None
        status = ["error","No cart with uid "+ uid + " found"] 
    
    if mycart:
        status = [mycart.status, ""]

    DB.close()
    return status


@CART_APP.task
def availableCart(uid):
    """Checks if the asked for cart tar is available
       returns the path to tar if yes, false if not"""
    DB.connect()
    cartBundlePath = False
    try:
        mycart = (Cart.select().where(Cart.cart_uid == str(uid)).order_by(Cart.creation_date.desc()).get())
    except Exception as ex:
        #case if no record exists yet in database
        mycart = None

    if mycart and mycart.status == "ready":
        cartBundlePath = mycart.bundle_path
    return cartBundlePath

def filePullCurl(archive_filename, cart_filepath):
    r = requests.get(ARCHIVE_INTERFACE_URL + archive_filename, stream=True)
    with open(cart_filepath, 'w+') as f:
        for chunk in r.iter_content(BLOCK_SIZE):
            f.write(chunk)

def create_bundle_directories(filepath):
    try:
        os.makedirs(filepath, 0777)
    except OSError as exception:
        #dont worry about error if the directory already exists
        #other errors are a problem however.
        if exception.errno != errno.EEXIST:
            return False

    return True

def archive_stage_file(file_name):
    requests.post(str(ARCHIVE_INTERFACE_URL + file_name))

def archive_status_file(file_name):
    r = requests.head(str(ARCHIVE_INTERFACE_URL + file_name))
    print "The head request returns:" + r.text
    return r.text

