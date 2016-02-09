from __future__ import absolute_import
from cart.celery import CART_APP
from cart.cart_orm import Cart, File, DB, database_connect, database_close
from os import path
import os
import time
import datetime
import errno
import psutil
import pycurl
from StringIO import StringIO

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
    database_connect()
    mycart = Cart(cart_uid=uid, status="staging")
    mycart.save()
    #with update or new, need to add in files
    updateCartFiles(mycart, fileIds)

    getFilesLocally.delay(mycart.id)
    prepareBundle.delay(mycart.id)
    database_close()

@CART_APP.task(ignore_result=True)
def getFilesLocally(cartid):
    """Pull the files to the local system from the backend """
    #tell each file to be pulled
    database_connect()
    for f in File.select().where(File.cart == cartid):
        pullFile.delay(f.id, False)
    database_close()

@CART_APP.task(ignore_result=True)
def prepareBundle(cartid):
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
        prepareBundle.delay(cartid)

    else:
        #All files are local...try to tar
        tarFiles.delay(cartid)
    database_close()


@CART_APP.task(ignore_result=True)
def pullFile(fId, record_error):
    """Pull a file from the archive  """
    database_connect()
    try:
        f = File.get(File.id == fId)
        f.status = "staging"
        f.save
        mycart = f.cart 
    except Exception as ex:
        f = None
        database_close()
        return

    #stage the file on the archive.  True on success, False on fail
    stage_call = archive_stage_file(f, mycart)

    #check to see if file is available to pull from archive interface
    response = archive_status_file(f, mycart)
    print response
    size_needed = check_file_size_needed(response)
    ready_to_pull = check_file_ready_pull(response)

    #Check to see if ready to pull.  If not recall this to check again
    if ready_to_pull == False:
        pullFile.delay(fId, False)
        database_close()
        return

    #create the path the file will be downloaded to
    abs_cart_file_path = os.path.join(VOLUME_PATH, str(mycart.id), mycart.cart_uid, f.bundle_path)
    path_created = create_download_path(f, mycart, abs_cart_file_path)

    #Check size here and make sure enough space is available.
    enough_space = check_space_requirements(f, mycart, size_needed)

    if path_created and enough_space:
        try:
            #curl here to download from the archive interface
            filePullCurl(f.file_name, abs_cart_file_path)
            f.status = "staged"
            f.save()
            mycart.updated_date = datetime.datetime.now()
            mycart.save()
            database_close()
            return
        except IOError as ex:
            #if curl fails...try a second time, if that fails write error
            if(record_error):
                f.status = "error"
                f.error = "Failed to pull with error: " + str(ex)
                f.save()
                mycart.updated_date = datetime.datetime.now()
                mycart.save()
                database_close()
                return
            else:
                pullFile.delay(fId, True)
                database_close()
                return
           


@CART_APP.task(ignore_result=True)
def tarFiles(cartid):
    """Start to bundle all the files together"""
    #make sure to check size here and make sure enough space is available

    #tar file module for python
    #set datetime type, owners

    database_connect
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
    database_close


@CART_APP.task
def cartStatus(uid):
    """Get the status of a specified cart"""
    database_connect()
    status = None
    try:
        mycart = (Cart.select().where(Cart.cart_uid == str(uid)).order_by(Cart.creation_date.desc()).get())
    except Exception as ex:
        #case if no record exists yet in database
        mycart = None
        status = ["error","No cart with uid "+ uid + " found"] 
    
    if mycart:
        status = [mycart.status, ""]

    database_close()
    return status


@CART_APP.task
def availableCart(uid):
    """Checks if the asked for cart tar is available
       returns the path to tar if yes, false if not"""
    database_connect()
    cartBundlePath = False
    try:
        mycart = (Cart.select().where(Cart.cart_uid == str(uid)).order_by(Cart.creation_date.desc()).get())
    except Exception as ex:
        #case if no record exists yet in database
        mycart = None

    if mycart and mycart.status == "ready":
        cartBundlePath = mycart.bundle_path
    database_close()
    return cartBundlePath

def filePullCurl(archive_filename, cart_filepath):
    c = pycurl.Curl()
    c.setopt(c.URL, str(ARCHIVE_INTERFACE_URL + archive_filename))
    with open(cart_filepath, 'w+') as f:
        c.setopt(c.WRITEFUNCTION, f.write)
        c.perform()
    c.close()

def create_bundle_directories(filepath):
    try:
        os.makedirs(filepath, 0777)
    except OSError as exception:
        #dont worry about error if the directory already exists
        #other errors are a problem however so push them up
        if exception.errno != errno.EEXIST:
            raise exception


def archive_stage_file(cart_file, mycart):
    """Sends a post to the archive interface telling it to stage the file """
    try:
        c = pycurl.Curl() 
        c.setopt(c.URL, str(ARCHIVE_INTERFACE_URL + cart_file.file_name))
        c.setopt(c.POST, True)
        c.perform()
        c.close()
        return True
    except Exception as ex:
        cart_file.status = "error"
        cart_file.error = "Failed to stage with error: " + str(ex)
        cart_file.save()
        mycart.updated_date = datetime.datetime.now()
        mycart.save()
        return False



def archive_status_file(cart_file, mycart):
    """Gets a status from the  archive interface via Head and returns response """
    try:
        storage = StringIO()
        c = pycurl.Curl() 
        c.setopt(c.CUSTOMREQUEST, "HEAD")
        c.setopt(c.URL, str(ARCHIVE_INTERFACE_URL + cart_file.file_name))
        c.setopt(c.NOBODY, False)
        c.setopt(c.WRITEFUNCTION, storage.write)
        c.perform()
        c.close()
        content = storage.getvalue()
        return content
    except Exception as ex:
        cart_file.status = "error"
        cart_file.error = "Failed to status file with error: " + str(ex)
        cart_file.save()
        mycart.updated_date = datetime.datetime.now()
        mycart.save()
        return False
    

def check_file_size_needed(response):
    """Checks response (should be from Archive Interface head request) for file size """
    return 10

def check_file_ready_pull(response):
    """Checks response (should be from Archive Interface head request) for bytes per level
       then returns True or False based on if the file is at level 1 (downloadable)"""
    return True

def check_space_requirements(cart_file, mycart, size_needed):
    """Checks to make sure there is enough space available on disk for the file
    to be downloaded """
    try:
        #available space is in bytes
        available_space = psutil.disk_usage(VOLUME_PATH).free
    except Exception as ex:
        f.status = "error"
        f.error = "Failed to get available file space with error: " + str(ex)
        f.save()
        mycart.updated_date = datetime.datetime.now()
        mycart.save()
        return False

    if(size_needed > available_space):
        f.status = "error"
        f.error = "Not enough space to download file"
        f.save()
        mycart.updated_date = datetime.datetime.now()
        mycart.save()
        return False

    #there is enough space so return true
    return True

def create_download_path(f, mycart, abs_cart_file_path):
    """ Create the directories that the file will be pulled to"""
    try:          
        cart_file_dirs = os.path.dirname(abs_cart_file_path)
        create_bundle_directories(cart_file_dirs)
    except Exception as ex:
        f.status = "error"
        f.error = "Failed to create directories with error: " + str(ex)
        f.save()
        mycart.updated_date = datetime.datetime.now()
        mycart.save()
        return False

    return True

