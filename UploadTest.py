from __future__ import print_function

import os
import urllib.parse

import boto3
import simplejson as json
from rauth.service import OAuth2Service
from rauth.service import OAuth2Session

# TODO: fill in these details - note: access token can be substituted later (when known)
# Run authenticate(), follow the instructions, substitute access token.
# Then re-run without invoking authenticate() - invoke reuseSession() instead
#
# This is all autodesk stuff.
BASE_ENDPOINT = "https://developer.api.autodesk.com/photo-to-3d/v1"
clientID = 'u1d6QTrR3ryafCSybAqo7WyYB73dZzMf'
clientSecret = 'XqT068pvGEtlZiGD'
# The AccessToken line is where you will copy in the access token after veryfying.
accessToken = 'qF2YSBrmEJ7DpQGvOJeMFXhtqtuh'
# accessToken = 'ZtzbEzraT6WOlfGuXRyb1sHS7HLp'
redirectUrl = 'http://localhost.autodesk.com/callback'
scope = 'data:read data:write'
# PHOTOdir is the linux based base directory to the temp drive that will hold all images for day.
PHOTO_DIR = '/Volumes/NIKON 1/Master'
# this is andrew's personal s3 account so a transfer will occur or I will be reimbursed.
S3Bucket = 'veronicaautodeskbuffer'
# Name = 'PAULA'
# This is autodesk stuff and also seems to be wrong.
# pid = 'Kc4gD4ToXMRo3xZQ5k6YFIo2J1zN1Ndep8gO4XRSN1I'
# 'guqSomFaEwWpfhUwm6aH5VjaByaN'
pid = 'Kc4gD4ToXMRo3xZQ5k6YFIo2J1zN1Ndep8gO4XRSN1I'


def authenticate():
    photoTo3D = OAuth2Service(
        client_id=clientID,
        client_secret=clientSecret,
        name='Photo to 3D',
        authorize_url='https://developer.api.autodesk.com/authentication/v1/authorize',
        access_token_url='https://developer.api.autodesk.com/authentication/v1/gettoken',
        base_url='https://developer.api.autodesk.com/')

    print("Go to This URL: " + str(photoTo3D.get_authorize_url()) + '&redirect_uri=' + str(
        redirectUrl) + '&response_type=code' + '&scope=' + str(urllib.parse.quote(scope)))

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


def sessionCreate():
    session = OAuth2Session(client_id=clientID, client_secret=clientSecret, access_token=accessToken)
    return session


def initBoto3():
    s3 = boto3.resource('s3')
    return s3


def Upload(s3Instance, data, key, bucket):
    s3Instance.Bucket(bucket).put_object(Key=key, Body=data)


# Note: method assumes an access_token - calls Photo to 3D endpoints
#
def reuseSession(directory, name, uploadFlag=True):
    sceneName = name

    session = sessionCreate()

    # Get Date
    #
    req = session.get(BASE_ENDPOINT + '/service/date',
                      params={'format': 'json'})

    print(req.json())  # {'date': '2016-06-13T11:54:48', 'Usage': '0.41884088516235', 'Resource': '/service/date'}

    # Get A360 Diskspace
    #
    req = session.get(BASE_ENDPOINT + '/service/diskspace',
                      params={'format': 'json'})

    print(
        req.json())  # {'Resource': '/service/diskspace', 'Usage': '1.1446611881256', 'diskspace': {'available': '5119073291', 'quota': '5368709120'}}
    """
    # Create a Photoscene
    #
    """

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

    print(
        req.json())  # {'Photoscene': {'photosceneid': 'FGGBmaP9J3hA8yjSQwxaiIu8AbawlmtE37fnLHOa6Hc'}, 'Resource': '/photoscene', 'Usage': '0.49483108520508'}

    # Get Photoscene Properties

    req = session.get(BASE_ENDPOINT + '/photoscene/' + pid + '/properties')
    print(
        req.json())  # {'Usage': '0.58867907524109', 'Resource': '/photoscene/FGGBmaP9J3hA8yjSQwxaiIu8AbawlmtE37fnLHOa6Hc/properties', 'next_token': {}, 'Photoscenes': {'Photoscene': {'userAgent': 'PF_APIv3.2.4', 'clientID': 'AFG6xNhSh3AuAS9vYO3ePx1NRCE2JOxu', 'status': 'PROCESSING', 'userID': 'pqZLEg14sxnXZcU3xFkUYi0oVSLEffU3aKSaD8era5M=', 'convertStatus': 'CREATED', 'maxResolutionForImage': '100000000', 'StitchingQuality': '2', 'engineVersion': '3.0.0.1160', 'smartTex': '1', 'clientStatus': 'CREATED', 'StitchingCreateInputFile': '1', 'convertFormat': 'obj,ortho', 'meshQuality': '9', 'name': 'testme', 'creationDate': '2016-06-13T12:03:36', 'Files': {'0': '\n        '}, 'projectID': 'FGGBmaP9J3hA8yjSQwxaiIu8AbawlmtE37fnLHOa6Hc', 'photosceneid': 'FGGBmaP9J3hA8yjSQwxaiIu8AbawlmtE37fnLHOa6Hc', 'itemName': 'FGGBmaP9J3hA8yjSQwxaiIu8AbawlmtE37fnLHOa6Hc', 'userOutputFilename': {}, 'type': {}}}}

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

    req = session.post(BASE_ENDPOINT + '/file',
                       data={'photosceneid': pid,
                             'type': 'image',
                             'file[0]': urlArray[0],
                             'file[1]': urlArray[1],
                             'file[2]': urlArray[2],
                             'file[3]': urlArray[3],
                             'file[4]': urlArray[4],
                             'file[5]': urlArray[5],
                             'file[6]': urlArray[6],
                             'file[7]': urlArray[7],
                             'file[8]': urlArray[8],
                             'file[9]': urlArray[9],
                             'file[10]': urlArray[10],
                             'file[11]': urlArray[11],
                             'file[12]': urlArray[12],
                             'file[13]': urlArray[13],
                             'file[14]': urlArray[14],
                             'file[15]': urlArray[15],
                             'file[16]': urlArray[16],
                             'file[17]': urlArray[17],
                             'file[18]': urlArray[18],
                             'file[19]': urlArray[19],
                             'file[20]': urlArray[20],
                             'file[21]': urlArray[21],
                             'file[22]': urlArray[22],
                             'file[23]': urlArray[23],
                             'file[24]': urlArray[24],
                             'file[25]': urlArray[25],
                             'file[26]': urlArray[26],
                             'file[27]': urlArray[27],
                             'file[28]': urlArray[28],
                             'file[29]': urlArray[29],
                             'file[30]': urlArray[30],
                             'file[31]': urlArray[31],
                             'file[32]': urlArray[32],
                             'file[33]': urlArray[33],
                             'file[34]': urlArray[34],
                             'file[35]': urlArray[35],
                             'file[36]': urlArray[36],
                             'file[37]': urlArray[37],
                             'file[38]': urlArray[38],
                             'file[39]': urlArray[39],
                             'file[40]': urlArray[40],
                             'file[41]': urlArray[41],
                             'file[42]': urlArray[42],
                             'file[43]': urlArray[43],
                             'file[44]': urlArray[44],
                             'file[45]': urlArray[45],
                             'file[46]': urlArray[46],
                             'file[47]': urlArray[47],
                             'file[48]': urlArray[48],
                             'file[49]': urlArray[49],
                             'file[50]': urlArray[50],
                             'file[51]': urlArray[51],
                             'file[52]': urlArray[52],
                             'file[53]': urlArray[53],
                             'file[54]': urlArray[54],
                             'file[55]': urlArray[55],
                             'file[56]': urlArray[56],
                             'file[57]': urlArray[57],
                             'file[58]': urlArray[58],
                             'file[59]': urlArray[59],
                             'file[60]': urlArray[60],
                             'file[61]': urlArray[61],
                             'file[62]': urlArray[62],
                             'file[63]': urlArray[63],
                             'file[64]': urlArray[64],
                             'file[65]': urlArray[65],
                             'file[66]': urlArray[66],
                             'file[67]': urlArray[67],
                             'file[68]': urlArray[68],
                             'file[69]': urlArray[69],
                             'file[70]': urlArray[70],
                             'file[71]': urlArray[71],
                             'file[72]': urlArray[72],
                             'file[73]': urlArray[73],
                             'file[74]': urlArray[74],
                             'file[75]': urlArray[75],
                             'file[76]': urlArray[76],
                             'file[77]': urlArray[77],
                             'file[78]': urlArray[78],
                             'file[79]': urlArray[79],
                             'file[80]': urlArray[80],
                             'file[81]': urlArray[81],
                             'file[82]': urlArray[82],
                             'file[83]': urlArray[83],
                             'file[84]': urlArray[84],
                             'file[85]': urlArray[85],
                             'file[86]': urlArray[86],
                             'file[87]': urlArray[87],
                             'file[88]': urlArray[88],
                             'file[89]': urlArray[89],
                             'file[90]': urlArray[90],
                             'file[91]': urlArray[91],
                             'file[92]': urlArray[92],
                             'file[93]': urlArray[93],
                             'file[94]': urlArray[94]
                             }
                       )

    print(str(
        req.json()) + " Files Uploaded?")  # {'photosceneid': 'FGGBmaP9J3hA8yjSQwxaiIu8AbawlmtE37fnLHOa6Hc', 'Files': {'file': [{'filesize': '308394', 'msg': 'already on server', 'fileid': 'c0324804b00348a2a16755d57ed183b2', 'filename': '_MG_9029.jpg'}, {'filesize': '341288', 'msg': 'already on server', 'fileid': 'b8f82671068c4a19a83e8f430ddbc54b', 'filename': '_MG_9030.jpg'}, {'filesize': '332689', 'msg': 'already on server', 'fileid': 'f56bfa024f454109bf831f5d390fc239', 'filename': '_MG_9027.jpg'}, {'filesize': '364436', 'msg': 'already on server', 'fileid': '423e3ebe3bc443518a2061f63ffec6a0', 'filename': '_MG_9026.jpg'}, {'filesize': '354095', 'msg': 'already on server', 'fileid': '6e72755f0fc042c18c0497d94617512e', 'filename': '_MG_9031.jpg'}, {'filesize': '315268', 'msg': 'already on server', 'fileid': '10e8a6c91d474e66a35429d5e1d77284', 'filename': '_MG_9028.jpg'}]}, 'Resource': '/file', 'Usage': '12.713293075562'}

    # Process Photoscene
    #
    req = session.post(BASE_ENDPOINT + '/photoscene/' + pid)
    print(
        req.json())  # {'Photoscene': {'photosceneid': 'FGGBmaP9J3hA8yjSQwxaiIu8AbawlmtE37fnLHOa6Hc'}, 'Resource': '/photoscene/FGGBmaP9J3hA8yjSQwxaiIu8AbawlmtE37fnLHOa6Hc', 'msg': 'No error', 'Usage': '2.5454890727997'}

    # Get Photoscene output file
    #
    req = session.get(BASE_ENDPOINT + '/photoscene/' + pid, data={'format': 'ortho'})

    print(
        req.json())  # {'Resource': '/photoscene/FGGBmaP9J3hA8yjSQwxaiIu8AbawlmtE37fnLHOa6Hc', 'Error': {'code': '22', 'msg': 'Data is not ready'}, 'Usage': '0.38405299186707'}
    # {'Resource': '/photoscene/FGGBmaP9J3hA8yjSQwxaiIu8AbawlmtE37fnLHOa6Hc', 'Usage': '0.70922684669495', 'Photoscene': {'progressmsg': 'DONE', 'photosceneid': 'FGGBmaP9J3hA8yjSQwxaiIu8AbawlmtE37fnLHOa6Hc', 'resultmsg': {}, 'scenelink': 'https://s3.amazonaws.com/com.autodesk.storage.production/V5C5QB5QPBHZ/my/a5c481bf7b124d6f89ca68718f888780/2ee1231976db45e6950772ff3f8a115b-c308bfe6c8d64bdba97f3a62ed5d1e90?AWSAccessKeyId=AKIAJ5BDHTMLFDQJDQTQ&Expires=1465822417&Signature=XG0vShIeFGFKq1KVhL8kj/K321w=', 'progress': '100', 'filesize': '8266'}}


# Unfortunately Authentication is manual Please Put in main flag
# authenticate()

# reuseSession(PHOTO_DIR, Name)

def runProgram(authenFlag=False):
    if authenFlag == False:
        Name = input("Please input Name of Person used to Upload Photos: ")
        reuseSession(PHOTO_DIR, Name, False)
    elif authenFlag == True:
        print("Prepare to Authenticate: ")
        authenticate()


runProgram()
