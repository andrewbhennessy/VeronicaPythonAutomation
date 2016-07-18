# Dependencies:
#
# Python 3.5.1
#   SetupTools
#       python https://bootstrap.pypa.io/ez_setup.py
#   pip
#       python -m pip install --upgrade pip
#   requests
#       pip install requests
#   simplejson
#       pip install simplejson
#   rauth setup for compatibility
#       https://github.com/litl/rauth
#       python setup.py install
#   Windows: set HOME=c:\python35
#
from __future__ import print_function

from rauth.service import OAuth2Service
from rauth.service import OAuth2Session
import simplejson as json
import os
import urllib.parse

from subprocess import call
from datetime import datetime
import logging
import six
import sys
import os
import boto3

import gphoto2 as gp

# TODO: fill in these details - note: access token can be substituted later (when known)
# Run authenticate(), follow the instructions, substitute access token.
# Then re-run without invoking authenticate() - invoke reuseSession() instead
#
BASE_ENDPOINT = "https://developer.api.autodesk.com/photo-to-3d/v1";
clientID = 'u1d6QTrR3ryafCSybAqo7WyYB73dZzMf'
clientSecret = 'XqT068pvGEtlZiGD'
accessToken = 'ZtzbEzraT6WOlfGuXRyb1sHS7HLp'
redirectUrl = 'http://localhost.autodesk.com/callback'
scope = 'data:read data:write'
PHOTO_DIR = '/Volumes/NIKON 1/Master'
S3Bucket = 'veronicaautodeskbuffer'

# TODO: optional - non-critical
#
pid = 'Kc4gD4ToXMRo3xZQ5k6YFIo2J1zN1Ndep8gO4XRSN1I'
sceneName = 'sceneName'


def get_target_dir(timestamp):
    return os.path.join(PHOTO_DIR, timestamp.strftime('%Y/%Y_%m_%d/'))


def list_computer_files():
    result = []
    for root, dirs, files in os.walk(PHOTO_DIR):
        for name in files:
            if '.thumbs' in dirs:
                dirs.remove('.thumbs')
            if name in ('.directory',):
                continue
            ext = os.path.splitext(name)[1].lower()
            if ext in ('.db',):
                continue
            result.append(os.path.join(root, name))
    return result


def get_camera_file_info(camera, context, path):
    folder, name = os.path.split(path)
    return gp.check_result(
        gp.gp_camera_file_get_info(camera, folder, name, context))


def list_files(camera, context, path='/'):
    result = []
    # get files
    for name, value in camera.folder_list_files(path, context):
        result.append(os.path.join(path, name))
    # read folders
    folders = []
    for name, value in camera.folder_list_folders(path, context):
        folders.append(name)
    # recurse over subfolders
    for name in folders:
        result.extend(list_files(camera, context, os.path.join(path, name)))
    return result


def main():
    os.system("sudo killall PTPCamera")
    Name = input('Enter your name: ')
    logging.basicConfig(
        format='%(levelname)s: %(name)s: %(message)s', level=logging.WARNING)
    gp.check_result(gp.use_python_logging())
    context = gp.Context()
    # make a list of all available cameras
    camera_list = []
    for name, addr in context.camera_autodetect():
        camera_list.append((name, addr))
    if not camera_list:
        print('No camera detected')
        return 1
    camera_list.sort(key=lambda x: x[0])
    # ask user to choose one
    # initialise chosen camera
    computer_files = list_computer_files()
    print('Getting list of files from camera...')
    for cam in range(len(camera_list)):
        os.system("sudo killall PTPCamera")
        camera = gp.Camera()
        # search ports for camera port name
        port_info_list = gp.PortInfoList()
        port_info_list.load()
        idx = port_info_list.lookup_path(camera_list[cam][1])
        camera.set_port_info(port_info_list[idx])
        camera.init(context)
        text = camera.get_summary(context)
        print('Summary')
        print('=======')
        # print(str(text))
        camera_files = list_files(camera, context)
        camera_files.reverse()
        print(camera_files[:12])
        if not camera_files:
            print('No files found')
            return 1
        print('Copying files...')
        for path in camera_files[:12]:
            info = get_camera_file_info(camera, context, path)
            timestamp = datetime.fromtimestamp(info.file.mtime)
            folder, name = os.path.split(path)
            dest_dir = os.path.join(PHOTO_DIR, Name)
            dest = os.path.join(dest_dir, name)
            if dest in computer_files:
                continue
            print('%s -> %s' % (path, dest_dir))
            if not os.path.isdir(dest_dir):
                os.makedirs(dest_dir)
            camera_file = gp.check_result(gp.gp_camera_file_get(
                camera, folder, name, gp.GP_FILE_TYPE_NORMAL, context))
            gp.check_result(gp.gp_file_save(camera_file, dest))
        gp.check_result(gp.gp_camera_exit(camera, context))
        camera.exit(context)
    reuseSession(dest_dir,Name)


def get_file_info(camera, context, path):
    folder, name = os.path.split(path)
    return camera.file_get_info(folder, name, context)

def initBoto3():
    s3 = boto3.resource('s3')
    return s3


def Upload(s3Instance, data, key, bucket):
    s3Instance.Bucket(bucket).put_object(Key=key, Body=data)


def reuseSession(dest_dir,name,uploadFlag=True):
    directory = dest_dir
    localBuffer = str(directory) + '/' + str(name)
    print(localBuffer)
    localArray = os.listdir(localBuffer)
    for i in range(len(localArray)):
        # print(localArray[i])
        localArray[i] = str(directory) + '/' + str(name) + '/' + str(localArray[i])

    if uploadFlag == True:
        s3 = initBoto3()

        for item in range(len(localArray)):
            data = open(localArray[item], 'rb')
            key = localArray[item]
            try:
                Upload(s3, data, key, S3Bucket)
                print("Upload of " + key + " Succesful " + str((item / len(localArray)) * 100) + " % Complete")

            except:
                print("Failed uploading " + key)
    else:
        pass

    urlArray = []

    for i in range(95):
        urlArray.append(
            "https://s3.eu-central-1.amazonaws.com/" + str(S3Bucket) + '/' + str(localArray[0]).replace(' ', '+'))
        print(str(urlArray))

reuseSession(PHOTO_DIR,"PAULA")
#main()
