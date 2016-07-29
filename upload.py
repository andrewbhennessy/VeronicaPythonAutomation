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

from tqdm import tqdm
import time
import pickle


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
PHOTO_DIR = '/Volumes/Veronica 3/Master'
#LocalScanDriveFactum
#PHOTO_DIR = '/Volumes/Archivo06/PROYECTOS/FACTUM/16F0025_Veronica_Scanner/Production/Process/scans'
S3Bucket = 'veronicastandard'
numScans= 10
passthruName = "Quinner"

# TODO: optional - non-critical
#
pid = 'Kc4gD4ToXMRo3xZQ5k6YFIo2J1zN1Ndep8gO4XRSN1I'
sceneName = 'sceneName'


def nameSwap(name, position):
    types = []
    name = name.replace("_", "")
    for i in range(len(name)):
        try:
            str(type(int(name[i])))
            types.append("int")
        except:
            str(type(name[i]))
            types.append("char")
    # print(str(types))

    locList = []
    for value in range(len(types)):
        buffer = types[value]
        try:
            if types[value + 1] == buffer:
                pass
            else:
                locations = value + 1
                locList.append(locations)
        except:
            pass

    # print(locList)

    begin = locList[0]
    end = locList[1]
    there = str(name[begin:end])
    str.strip(name[begin:end])
    name = name[:begin] + str(position) + name[end:]
    # print(str(name))
    return name

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

def scanMe(starting,ending,passthruName):
    #Start Counter
    counter = 0

    #Tell the user we are killing the Camera BS in the background
    print("Killing Camera Interupts...")

    #create a cute tqdm progress bar. Stricly aesthetic.
    for i in tqdm(range(10)):
        time.sleep(.02)

    os.system("sudo killall PTPCamera")


    if passthruName != "":
        print("No Name!!, Using Name: "+str(passthruName)+" #"+str((starting/12)))
        Name = str(passthruName)+" #"+str((starting/12))
    else:
        print("")
        Name = input('Enter your name: ')
        os.system("clear")
        print("Processing for: " + str(Name))
        print("Loading Assets and Compilers & Reticulating Splines ",end="")
        for i in tqdm(range(20)):
            time.sleep(.05)
        print("")


    logging.basicConfig(
        format='%(levelname)s: %(name)s: %(message)s', level=logging.CRITICAL)

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
    print("")
    print('Getting list of files from camera...')
    time.sleep(1)
    os.system("clear")
    print("Processing for: " + str(Name))
    with tqdm(total=8) as pbar:
        for cam in range(len(camera_list)):
            counter = 0
            os.system("clear")
            print("Processing for: " + str(Name))
            #os.system("sudo killall PTPCamera")



            camera = gp.Camera()

            # search ports for camera port name
            port_info_list = gp.PortInfoList()

            port_info_list.load()

            idx = port_info_list.lookup_path(camera_list[cam][1])

            camera.set_port_info(port_info_list[idx])

            camera.init(context)

            text = camera.get_summary(context)

            print('Camera Progress Currently on Camera: #'+str(cam))
            print('')
            pbar.update(1)
            # print(str(text))
            camera_files = list_files(camera, context)
            camera_files.reverse()
            #print(camera_files[starting:ending])
            if not camera_files:
                print('No files found')
                return 1
            print("")
            print('Files Progress for Camera: #'+str(cam))
            for path in tqdm(camera_files[starting:ending]):
                info = get_camera_file_info(camera, context, path)
                timestamp = datetime.fromtimestamp(info.file.mtime)
                folder, name = os.path.split(path)

                dest_dir = os.path.join(PHOTO_DIR, Name)
                dest = os.path.join(dest_dir, name)
                if dest in computer_files:
                    continue
                #print('%s -> %s' % (path, dest_dir))
                if not os.path.isdir(dest_dir):
                    os.makedirs(dest_dir)
                camera_file = gp.check_result(gp.gp_camera_file_get(
                    camera, folder, name, gp.GP_FILE_TYPE_NORMAL, context))
                #print("Starting to Save.")
                gp.check_result(gp.gp_file_save(camera_file, dest))
                os.rename(dest, os.path.join(dest_dir,nameSwap(name,11-counter)))
                #print("Saved")
                #print("Percent Complete "+str((counter/96)*100))
                #print((str(152 - (((counter / 96) * 100) * 152) / 100) + " Seconds Remaining."),end="r")
                counter += 1


            gp.check_result(gp.gp_camera_exit(camera, context))
            camera.exit(context)
            os.system("clear")
        #reuseSession(dest_dir,Name)

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
    for i in tqdm(range(len(localArray))):
        # print(localArray[i])
        localArray[i] = str(directory) + '/' + str(name) + '/' + str(localArray[i])

    if uploadFlag == True:
        s3 = initBoto3()

        for item in tqdm(range(len(localArray))):
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

    for i in tqdm(range(95)):
        urlArray.append(
            "https://s3.website-us-east-1.amazonaws.com/" + str(S3Bucket) + '/' + str(localArray[0]).replace(' ', '+'))
        #print(str(urlArray))


def multiscan(numScans,name):
    for scans in range(numScans):
        scanMe(scans*12,(scans*12+12),passthruName)

def multiscanEXEC(numScans,name):
    for scans in range(numScans):
        scanMe(scans * 12, (scans * 12 + 12), name)

def singleScan():
    scanMe(0,12,"")

def singleScanAPI(name):
    scanMe(0,12,name)


def begin():
    welcome()
    print("At any time to stop cancel or 'go home' hold the control and z key down. Then rerun the program")
    print('')
    print("Delete last 1 picture taken on each Camera [a] ")
    print("Delete last 12 pictures taken on each Camera [b] ")
    print("Initiate Scan [c] ")
    print("Format SD Cards [d] ")
    print("Initiate Multi-Scan [e] ")
    print("Launch image download configurator [f] ")
    print("")
    Action=input("Run a task by typing its corresponding letter in either upper or lower case: ")
    if Action == "a":

        os.system("clear")
        welcome()
        print("")
        delete(1)
        return 1
    elif Action == "b":

        os.system("clear")
        welcome()
        print("")
        delete(12)
        return 1
    elif Action == "c":

        os.system("clear")
        welcome()
        print("")
        singleScan()
        print("Done. Aborting. COPY TO NTFS DRIVE IF ON MAC")
        return
    elif Action == "d":

        os.system("clear")
        welcome()
        print("")
        delete(True)
        return 1
    elif Action == "e":
        os.system("clear")
        welcome()
        print("")
        subjectName = input("Please enter Pass thru Name: ")
        scanQuant = input("Please enter number of Scans: ")
        scanQuant = int(scanQuant)
        multiScanAPI(subjectName,scanQuant)
        print("We are still building this functionality")
        pass
    elif Action == "f":

        os.system("clear")
        welcome()
        print("")
        directoryConfig(PHOTO_DIR)
        return 1
    else:
        print("")
        print("I don't understand that, you probably need help. Let me direct you to someone who can help.")
        print("")
        return 1

def directoryConfig(PHOTO_DIR):
    print("")
    save = PHOTO_DIR
    print("Current Directory: " + str(PHOTO_DIR))
    print("")
    decide = input("would you like to change the directory [y/n] ")
    if decide == "y":
        PHOTO_DIR = input("Drag the MASTER folder you wish to deposit photos here: ")
        try:
            os.system("cd "+str(PHOTO_DIR))
            print("This Folder Exists!!")
        except:
            print("Is this the right directory....Reverting to old.")
            PHOTO_DIR = save
    else:
        return 1

def get_file_info(camera, context, path):
    folder, name = os.path.split(path)
    return gp.check_result(
        gp.gp_camera_file_get_info(camera, folder, name, context))

def delete_file(camera, context, path):
    folder, name = os.path.split(path)
    gp.check_result(gp.gp_camera_file_delete(camera, folder, name, context))

def delete(deleteNum,all=False):

    # Tell the user we are killing the Camera BS in the background
    print("Killing Camera Interupts...")

    # create a cute tqdm progress bar. Stricly aesthetic.
    for i in tqdm(range(10)):
        time.sleep(.02)

    os.system("sudo killall PTPCamera")


    logging.basicConfig(
        format='%(levelname)s: %(name)s: %(message)s', level=logging.CRITICAL)

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
    print("")
    print('Getting list of files from camera...')
    time.sleep(1)
    os.system("clear")
    with tqdm(total=8) as pbar:
        for cam in range(len(camera_list)):
            os.system("clear")
            # os.system("sudo killall PTPCamera")



            camera = gp.Camera()

            # search ports for camera port name
            port_info_list = gp.PortInfoList()

            port_info_list.load()

            idx = port_info_list.lookup_path(camera_list[cam][1])

            camera.set_port_info(port_info_list[idx])

            camera.init(context)

            text = camera.get_summary(context)

            print('Camera deletion location is Currently on Camera: #' + str(cam))
            print('')
            pbar.update(1)
            # print(str(text))
            camera_files = list_files(camera, context)
            camera_files.reverse()
            # print(camera_files[starting:ending])
            if not camera_files:
                print('No files found')
                return 1
            print("")
            print('Deleting file progress on cam: #' + str(cam))
            if all == True:
                for path in tqdm(camera_files):
                    #print(str(path))
                    delete_file(camera,context,path)
            elif all == False:
                for path in tqdm(camera_files[0:deleteNum]):
                    #print(str(path))
                    delete_file(camera,context,path)
    os.system("clear")
    welcome()
    print("")
    return 1


def delSingle():
    os.system("clear")
    welcome()
    print("")
    delete(1)
    return 1


def delScan():
    os.system("clear")
    welcome()
    print("")
    delete(12)
    return 1


def scanAPI(name):
    os.system("clear")
    welcome()
    print("")
    singleScanAPI()
    print("Done. Aborting. COPY TO NTFS DRIVE IF ON MAC")
    return

def multiScanAPI(name,numOfScans):
    os.system("clear")
    welcome()
    print("")
    multiscanEXEC(numOfScans,name)
    print("Done. Aborting. COPY TO NTFS DRIVE IF ON MAC")
    return

def delAll():
    os.system("clear")
    welcome()
    print("")
    delete(True)
    return 1


def setDownloadLoc():
    os.system("clear")
    welcome()
    print("")
    directoryConfig(PHOTO_DIR)
    return 1



def welcome():
    os.system("clear")
    print("\t*************************************************************")
    print("\t***       Veronica Scanner CLI - Anrdrew B Hennessy        ***")
    print("\t*************************************************************")
    print("")

begin()













