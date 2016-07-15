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
import time


from subprocess import call
from datetime import datetime
import logging
import six
import sys
import os

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

# TODO: optional - non-critical
#
pid = 'Kc4gD4ToXMRo3xZQ5k6YFIo2J1zN1Ndep8gO4XRSN1I'
sceneName='sceneName'


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
    sceneName=Name
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
        time.sleep(1)
        port_info_list.load()
        time.sleep(1)
        idx = port_info_list.lookup_path(camera_list[cam][1])
        time.sleep(1)
        camera.set_port_info(port_info_list[idx])
        time.sleep(1)
        camera.init(context)
        time.sleep(1)
        text = camera.get_summary(context)
        print('Summary')
        print('=======')
        #print(str(text))
        camera_files=list_files(camera,context)
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
            dest_dir = os.path.join(PHOTO_DIR,Name)
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
    os.system("sudo python3 /Users/andrewhennessy/Google\\Drive/Photogrammerty/PhotoTo3D-cli-FactumArte.py"+str(dest_dir))
    reuseSession(PHOTO_DIR,Name)

def get_file_info(camera, context, path):
    folder, name = os.path.split(path)
    return camera.file_get_info(folder, name, context)
# Note: method assumes no access_token - it's obtained from the auth code etc.
#
def authenticate():

    photoTo3D = OAuth2Service(
        client_id=clientID,
        client_secret=clientSecret,
        name='Photo to 3D',
        authorize_url='https://developer.api.autodesk.com/authentication/v1/authorize',
        access_token_url='https://developer.api.autodesk.com/authentication/v1/gettoken',
        base_url='https://developer.api.autodesk.com/')

    print('Visit this URL in your browser: ' + photoTo3D.get_authorize_url() + '&redirect_uri=' + redirectUrl + '&response_type=code' + '&scope=' + urllib.parse.quote(scope))

    # This is a bit cumbersome, but you need to copy the code=something (just the
    # `something` part) out of the URL that's redirected to AFTER you login and
    # authorize the demo application

    code = input('Enter code parameter (code=something) from URL: ')

    # create a dictionary for the data we'll post on the get_access_token request
    #
    data = dict(code=code, redirect_uri=redirectUrl, scope=scope, grant_type="authorization_code")

    # retrieve the authenticated session
    #
    session = photoTo3D.get_auth_session(data=data, decoder=json.loads)

    print(session.access_token)

# Note: method assumes an access_token - calls Photo to 3D endpoints
#
def reuseSession(directory,name):

    

    session = OAuth2Session(client_id=clientID, client_secret=clientSecret, access_token=accessToken)

    # Get Date
    #
    req = session.get(BASE_ENDPOINT + '/service/date',
                      params={'format': 'json'})

    print(req.json())  # {'date': '2016-06-13T11:54:48', 'Usage': '0.41884088516235', 'Resource': '/service/date'}

    # Get A360 Diskspace
    #
    req = session.get(BASE_ENDPOINT + '/service/diskspace',
                      params={'format': 'json'})

    print(req.json())  # {'Resource': '/service/diskspace', 'Usage': '1.1446611881256', 'diskspace': {'available': '5119073291', 'quota': '5368709120'}}
    """
    # Create a Photoscene
    #
    """

    sceneName = str(sceneName)
    req = session.post(BASE_ENDPOINT + '/photoscene',
                       data={'scenename': sceneName,
                             'meshquality': '9',
                             'format': 'obj',
                             'metadata_name[0]': 'smartTex',
                             'metadata_value[0]': '1',
                             'metadata_name[1]': 'StitchingCreateInputFile',
                             'metadata_value[1]': '1',
                             'metadata_name[2]': 'StitchingQuality',
                             'metadata_value[2]': '2'}
                       )

    print(req.json())  # {'Photoscene': {'photosceneid': 'FGGBmaP9J3hA8yjSQwxaiIu8AbawlmtE37fnLHOa6Hc'}, 'Resource': '/photoscene', 'Usage': '0.49483108520508'}
    """

    # Get Photoscene Properties
    #
    req = session.get(BASE_ENDPOINT + '/photoscene/' + pid + '/properties')
    print(req.json())  # {'Usage': '0.58867907524109', 'Resource': '/photoscene/FGGBmaP9J3hA8yjSQwxaiIu8AbawlmtE37fnLHOa6Hc/properties', 'next_token': {}, 'Photoscenes': {'Photoscene': {'userAgent': 'PF_APIv3.2.4', 'clientID': 'AFG6xNhSh3AuAS9vYO3ePx1NRCE2JOxu', 'status': 'PROCESSING', 'userID': 'pqZLEg14sxnXZcU3xFkUYi0oVSLEffU3aKSaD8era5M=', 'convertStatus': 'CREATED', 'maxResolutionForImage': '100000000', 'StitchingQuality': '2', 'engineVersion': '3.0.0.1160', 'smartTex': '1', 'clientStatus': 'CREATED', 'StitchingCreateInputFile': '1', 'convertFormat': 'obj,ortho', 'meshQuality': '9', 'name': 'testme', 'creationDate': '2016-06-13T12:03:36', 'Files': {'0': '\n        '}, 'projectID': 'FGGBmaP9J3hA8yjSQwxaiIu8AbawlmtE37fnLHOa6Hc', 'photosceneid': 'FGGBmaP9J3hA8yjSQwxaiIu8AbawlmtE37fnLHOa6Hc', 'itemName': 'FGGBmaP9J3hA8yjSQwxaiIu8AbawlmtE37fnLHOa6Hc', 'userOutputFilename': {}, 'type': {}}}}

    # Add external links to images to Photoscene
    #

    urlArray = [
        "http://davidisrael.ca/sample_data/_MG_9026.jpg",
        "http://davidisrael.ca/sample_data/_MG_9027.jpg",
        "http://davidisrael.ca/sample_data/_MG_9028.jpg",
        "http://davidisrael.ca/sample_data/_MG_9029.jpg",
        "http://davidisrael.ca/sample_data/_MG_9030.jpg",
        "http://davidisrael.ca/sample_data/_MG_9031.jpg"
    ]

    req = session.post(BASE_ENDPOINT + '/file',
                       data={'photosceneid': pid,
                             'type': 'image',
                             'file[0]': urlArray[0],
                             'file[1]': urlArray[1],
                             'file[2]': urlArray[2],
                             'file[3]': urlArray[3],
                             'file[4]': urlArray[4],
                             'file[5]': urlArray[5]
                             }
                       )

    print(req.json())  # {'photosceneid': 'FGGBmaP9J3hA8yjSQwxaiIu8AbawlmtE37fnLHOa6Hc', 'Files': {'file': [{'filesize': '308394', 'msg': 'already on server', 'fileid': 'c0324804b00348a2a16755d57ed183b2', 'filename': '_MG_9029.jpg'}, {'filesize': '341288', 'msg': 'already on server', 'fileid': 'b8f82671068c4a19a83e8f430ddbc54b', 'filename': '_MG_9030.jpg'}, {'filesize': '332689', 'msg': 'already on server', 'fileid': 'f56bfa024f454109bf831f5d390fc239', 'filename': '_MG_9027.jpg'}, {'filesize': '364436', 'msg': 'already on server', 'fileid': '423e3ebe3bc443518a2061f63ffec6a0', 'filename': '_MG_9026.jpg'}, {'filesize': '354095', 'msg': 'already on server', 'fileid': '6e72755f0fc042c18c0497d94617512e', 'filename': '_MG_9031.jpg'}, {'filesize': '315268', 'msg': 'already on server', 'fileid': '10e8a6c91d474e66a35429d5e1d77284', 'filename': '_MG_9028.jpg'}]}, 'Resource': '/file', 'Usage': '12.713293075562'}
    """
    # Upload local images to Photoscene
    #
    localBuffer = str(directory)+str(name)
    localArray = os.listdir(localBuffer)
    for i in range(len(localArray)):
        localArray[i] = str(directory)+str(name)+str(localArray[i])

    multiple_files=[]
    
    for num in range(95):
        multiple_files.append(('file['+num+']',(os.path.basename(localArray[num]),open(localArray[num],'rb'),'image/jpeg'))
                              
#    multiple_files = [
 #       ('file[0]',(os.path.basename(localArray[0]), open(localArray[0], 'rb'), 'image/jpeg')),


    for file in range(len(multiple_files)):
        req = session.post(BASE_ENDPOINT + '/file',
                           data={'photosceneid': pid,
                                 'type': 'image'},
                           files = multiple_files[file]
                           )

        print(req.json()) #{'photosceneid': '9Qhty43WV1NvuHdkPOHYH1L1VBIPO4uXU3jj6vZ2ikU', 'Usage': '4.6607179641724', 'Resource': '/file', 'Files': {'file': [{'filesize': '364436', 'filename': '_MG_9026.jpg', 'fileid': '274bad0314b048fa99ca2a17689f3737', 'msg': 'already on server'}, {'filesize': '332689', 'filename': '_MG_9027.jpg', 'fileid': '41350bd9a4ff410b82545cac87e676b5', 'msg': 'already on server'}, {'filesize': '332689', 'filename': '_MG_9027.jpg', 'fileid': '41350bd9a4ff410b82545cac87e676b5', 'msg': 'already on server'}]}}

        # Process Photoscene
        #
        req = session.post(BASE_ENDPOINT + '/photoscene/' + pid)
        print(req.json())  # {'Photoscene': {'photosceneid': 'FGGBmaP9J3hA8yjSQwxaiIu8AbawlmtE37fnLHOa6Hc'}, 'Resource': '/photoscene/FGGBmaP9J3hA8yjSQwxaiIu8AbawlmtE37fnLHOa6Hc', 'msg': 'No error', 'Usage': '2.5454890727997'}
        

        # Get Photoscene output file
        #
    req = session.get(BASE_ENDPOINT + '/photoscene/' + pid,
                      data={'format': 'ortho'}
                      )

    print(req.json())   # {'Resource': '/photoscene/FGGBmaP9J3hA8yjSQwxaiIu8AbawlmtE37fnLHOa6Hc', 'Error': {'code': '22', 'msg': 'Data is not ready'}, 'Usage': '0.38405299186707'}
            # {'Resource': '/photoscene/FGGBmaP9J3hA8yjSQwxaiIu8AbawlmtE37fnLHOa6Hc', 'Usage': '0.70922684669495', 'Photoscene': {'progressmsg': 'DONE', 'photosceneid': 'FGGBmaP9J3hA8yjSQwxaiIu8AbawlmtE37fnLHOa6Hc', 'resultmsg': {}, 'scenelink': 'https://s3.amazonaws.com/com.autodesk.storage.production/V5C5QB5QPBHZ/my/a5c481bf7b124d6f89ca68718f888780/2ee1231976db45e6950772ff3f8a115b-c308bfe6c8d64bdba97f3a62ed5d1e90?AWSAccessKeyId=AKIAJ5BDHTMLFDQJDQTQ&Expires=1465822417&Signature=XG0vShIeFGFKq1KVhL8kj/K321w=', 'progress': '100', 'filesize': '8266'}}

#authenticate()
    
main()




 
