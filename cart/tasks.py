from __future__ import absolute_import
from cart.celery import cart_app
from cart.cart_orm import Cart

@cart_app.task
def stageFiles(fileIds, uuid):
    """Tell the files to be staged on the backend system """
    mycart = Cart(cart_uuid=uuid, file_ids=fileIds, status="staging")
    mycart.save()
    #staging code here
    getFilesLocally.delay(mycart.id)
    return "Files are being staged on backend"

@cart_app.task
def getFilesLocally(cartId):
    """Pull the files to the local system from the backend """
    #for each file try to pull it...maybe set that files status
    #pulling code here per file
    #if all files are locally...then try to tar
    #make sure to check size here and make sure enough space is available
    tarFiles.delay(cartId)
    return "Files are being staged locally"

@cart_app.task
def tarFiles(cartId):
    """Start to bundle all the files together"""
    mycart = Cart.get(Cart.id == cartId)
    mycart.status = "bundling"
    mycart.save()
    #get a path to where the tar will be
    #for each file put into bundle here
    #update the carts status and bundle path

    return "Files are being bundled"

