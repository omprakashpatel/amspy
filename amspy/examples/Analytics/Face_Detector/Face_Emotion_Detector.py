"""
Copyright (c) 2016, John Deutscher
Description: Sample Python script for Face Detector processor
License: MIT (see LICENSE.txt file for details)
Documentation : https://azure.microsoft.com/en-us/documentation/articles/media-services-face-and-emotion-detection/ 
"""
import os
import json
import amspy
import time
import sys
#import pytz
import urllib
import logging
import datetime
from azure import *
from azure.storage.blob import BlockBlobService
from azure.storage.blob import ContentSettings

###########################################################################################
##### DISCLAIMER ##### ##### DISCLAIMER ##### ##### DISCLAIMER ##### ##### DISCLAIMER #####
###########################################################################################

# ALL CODE IN THIS DIRECTOY (INCLUDING THIS FILE) ARE EXAMPLE CODES THAT  WILL  ACT ON YOUR 
# AMS ACCOUNT.  IT ASSUMES THAT THE AMS ACCOUNT IS CLEAN (e.g.: BRAND NEW), WITH NO DATA OR 
# PRODUCTION CODE ON IT.  DO NOT, AGAIN: DO NOT RUN ANY EXAMPLE CODE AGAINST PRODUCTION AMS
# ACCOUNT!  IF YOU RUN ANY EXAMPLE CODE AGAINST YOUR PRODUCTION  AMS ACCOUNT,  YOU CAN LOSE 
# DATA, AND/OR PUT YOUR AMS SERVICES IN A DEGRADED OR UNAVAILABLE STATE. BE WARNED!

###########################################################################################
##### DISCLAIMER ##### ##### DISCLAIMER ##### ##### DISCLAIMER ##### ##### DISCLAIMER #####
###########################################################################################

# Load Azure app defaults
try:
	with open('../../config.json') as configFile:
		configData = json.load(configFile)
except FileNotFoundError:
	print("ERROR: Expecting config.json in examples folder")
	sys.exit()

account_name = configData['accountName']
account_key = configData['accountKey']
sto_account_name = configData['sto_accountName']
sto_accountKey = configData['sto_accountKey']
log_name = configData['logName']
log_level = configData['logLevel']
purge_log = configData['purgeLog']

#Initialization...
print ("\n-----------------------= AMS Py =----------------------")
print ("Azure Media Analytics - Face Detector v1 Sample")
print ("-------------------------------------------------------\n")

#Remove old log file if requested (default behavior)...
if (purge_log.lower() == "yes"):
        if (os.path.isfile(log_name)):
                os.remove(log_name)

#Basic Logging...
logging.basicConfig(format='%(asctime)s - %(levelname)s:%(message)s', level=log_level, filename=log_name)

# Get the access token...
response = amspy.get_access_token(account_name, account_key)
resjson = response.json()
access_token = resjson["access_token"]

#Some global vars...
NAME = "movie"
ENCRYPTION = "1" # 0=None, StorageEncrypted=1, CommonEncryptionProtected=2, EnvelopeEncryptionProtected=4
ENCRYPTION_SCHEME = "StorageEncryption" # StorageEncryption or CommonEncryption.
ISM_NAME = "movie.ism"
VIDEO_NAME = "movie.mp4"
VIDEO_PATH = "../../assets/movie.mp4"
ASSET_FINAL_NAME = "Python Sample-Face Detection"
PROCESSOR_NAME = "Azure Media Face Detector"
MODE = "Face" #or Emotion
FACE_DETECTION_CONFIG = "face_detection_config.json"
EMOTION_DETECTION_CONFIG = "emotion_detection_config.json"

### get ams redirected url
response = amspy.get_url(access_token)
if (response.status_code == 200):
        ams_redirected_rest_endpoint = str(response.url)
else:
        print("GET Status: " + str(response.status_code) + " - Getting Redirected URL ERROR." + str(response.content))
        exit(1)


######################### PHASE 1: UPLOAD and VALIDATE #########################
### create an asset
print ("\n001 >>> Creating a Media Asset")
response = amspy.create_media_asset(access_token, NAME)
if (response.status_code == 201):
	resjson = response.json()
	asset_id = str(resjson['d']['Id'])
	print("POST Status.............................: " + str(response.status_code))
	print("Media Asset Name........................: " + NAME)
	print("Media Asset Id..........................: " + asset_id)
else:
	print("POST Status.............................: " + str(response.status_code) + " - Media Asset: '" + NAME + "' Creation ERROR." + str(response.content))

### create an assetfile
print ("\n003 >>> Creating a Media Assetfile (for the video file)")
response = amspy.create_media_assetfile(access_token, asset_id, VIDEO_NAME, "false", "false")
if (response.status_code == 201):
	resjson = response.json()
	video_assetfile_id = str(resjson['d']['Id'])
	print("POST Status.............................: " + str(response.status_code))
	print("Media Assetfile Name....................: " + str(resjson['d']['Name']))
	print("Media Assetfile Id......................: " + video_assetfile_id)
	print("Media Assetfile IsPrimary...............: " + str(resjson['d']['IsPrimary']))
else:
	print("POST Status: " + str(response.status_code) + " - Media Assetfile: '" + VIDEO_NAME + "' Creation ERROR." + str(response.content))

### create an asset write access policy for uploading
print ("\n005 >>> Creating an Asset Write Access Policy")
duration = "440"
response = amspy.create_asset_accesspolicy(access_token, "NewUploadPolicy", duration, "2")
if (response.status_code == 201):
	resjson = response.json()
	write_accesspolicy_id = str(resjson['d']['Id'])
	print("POST Status.............................: " + str(response.status_code))
	print("Asset Access Policy Id..................: " + write_accesspolicy_id)
	print("Asset Access Policy Duration/min........: " + str(resjson['d']['DurationInMinutes']))
else:
	print("POST Status: " + str(response.status_code) + " - Asset Write Access Policy Creation ERROR." + str(response.content))

### create a sas locator
print ("\n007 >>> Creating a write SAS Locator")

## INFO: If you need to upload your files immediately, you should set your StartTime value to five minutes before the current time.
#This is because there may be clock skew between your client machine and Media Services.
#Also, your StartTime value must be in the following DateTime format: YYYY-MM-DDTHH:mm:ssZ (for example, "2014-05-23T17:53:50Z").
# EDITED: Not providing starttime is the best approach to be able to upload a file immediatly...
#starttime = datetime.datetime.now(pytz.timezone(time_zone)).strftime("%Y-%m-%dT%H:%M:%SZ")
#response = amspy.create_sas_locator(access_token, asset_id, write_accesspolicy_id, starttime)
response = amspy.create_sas_locator(access_token, asset_id, write_accesspolicy_id)
if (response.status_code == 201):
	resjson = response.json()
	saslocator_id = str(resjson['d']['Id'])
	saslocator_baseuri = str(resjson['d']['BaseUri'])
	sto_asset_name = os.path.basename(os.path.normpath(saslocator_baseuri))
	saslocator_cac = str(resjson['d']['ContentAccessComponent'])
	print("POST Status.............................: " + str(response.status_code))
	print("SAS URL Locator StartTime...............: " + str(resjson['d']['StartTime']))
	print("SAS URL Locator Id......................: " + saslocator_id)
	print("SAS URL Locator Base URI................: " + saslocator_baseuri)
	print("SAS URL Locator Content Access Component: " + saslocator_cac)
else:
	print("POST Status: " + str(response.status_code) + " - SAS URL Locator Creation ERROR." + str(response.content))

### Use the Azure Blob Blob Servic library from the Azure Storage SDK.
block_blob_service = BlockBlobService(account_name=sto_account_name, sas_token=saslocator_cac[1:])

### Define a callback method to show progress of large uploads
def uploadCallback(current, total):
	if (current != None):
		print('{0:2,f}/{1:2,.0f} MB'.format(current,total/1024/1024))

### Start upload the video file
print ("\n009 >>> Uploading the Video File")
with open(VIDEO_PATH, mode='rb') as file:
        video_content = file.read()
        video_content_length = len(video_content)

response = block_blob_service.create_blob_from_path(
		sto_asset_name,
		VIDEO_NAME,
		VIDEO_PATH,
		max_connections=5,
		content_settings=ContentSettings(content_type='video/mp4'),
		progress_callback=uploadCallback,
	)
if (response == None):
        print("PUT Status..............................: 201")
        print("Video File Uploaded.....................: OK")

### update the assetfile metadata after uploading
print ("\n011 >>> Updating the Video Assetfile")
response = amspy.update_media_assetfile(access_token, asset_id, video_assetfile_id, video_content_length, VIDEO_NAME)
if (response.status_code == 204):
	print("MERGE Status............................: " + str(response.status_code))
	print("Assetfile Content Length Updated........: " + str(video_content_length))
else:
	print("MERGE Status............................: " + str(response.status_code) + " - Assetfile: '" + VIDEO_NAME + "' Update ERROR." + str(response.content))

### delete the locator, so that it can't be used again
print ("\n013 >>> Deleting the Locator")
response = amspy.delete_sas_locator(access_token, saslocator_id)
if (response.status_code == 204):
	print("DELETE Status...........................: " + str(response.status_code))
	print("SAS URL Locator Deleted.................: " + saslocator_id)
else:
	print("DELETE Status...........................: " + str(response.status_code) + " - SAS URL Locator: '" + saslocator_id + "' Delete ERROR." + str(response.content))

### delete the asset access policy
print ("\n014 >>> Deleting the Acess Policy")
response = amspy.delete_asset_accesspolicy(access_token, write_accesspolicy_id)
if (response.status_code == 204):
	print("DELETE Status...........................: " + str(response.status_code))
	print("Asset Access Policy Deleted.............: " + write_accesspolicy_id)
else:
	print("DELETE Status...........................: " + str(response.status_code) + " - Asset Access Policy: '" + write_accesspolicy_id + "' Delete ERROR." + str(response.content))

### get the media processor for Face Detecion
print ("\n015 >>> Getting the Media Processor for Face Detection")
response = amspy.list_media_processor(access_token)
if (response.status_code == 200):
        resjson = response.json()
        print("GET Status..............................: " + str(response.status_code))
        for mp in resjson['d']['results']:
                if(str(mp['Name']) == PROCESSOR_NAME):
                        processor_id = str(mp['Id'])
                        print("MEDIA Processor Id......................: " + processor_id)
                        print("MEDIA Processor Name....................: " + PROCESSOR_NAME)
else:
        print("GET Status: " + str(response.status_code) + " - Media Processors Listing ERROR." + str(response.content))

## create a Face or Emotion Dection Job

if (MODE == "Face"):
	print ("\n016 >>> Creating a Face Detection Job to process the content")
	with open(FACE_DETECTION_CONFIG, mode='r') as file:
			configuration = file.read()
else if (MODE == "Emotion"):
	print ("\n016 >>> Creating an Emotion Detection Job to process the content")
	with open(EMOTION_DETECTION_CONFIG, mode='r') as file:
			configuration = file.read()

response = amspy.encode_mezzanine_asset(access_token, processor_id, asset_id, ASSET_FINAL_NAME, configuration)
if (response.status_code == 201):
	resjson = response.json()
	job_id = str(resjson['d']['Id'])
	print("POST Status.............................: " + str(response.status_code))
	print("Media Job Id............................: " + job_id)
else:
	print("POST Status.............................: " + str(response.status_code) + " - Media Job Creation ERROR." + str(response.content))

### list a media job
print ("\n017 >>> Getting the Media Job Status")
flag = 1
while (flag):
	response = amspy.list_media_job(access_token, job_id)
	if (response.status_code == 200):
		resjson = response.json()
		job_state = str(resjson['d']['State'])
		if (resjson['d']['EndTime'] != None):
			joboutputassets_uri = resjson['d']['OutputMediaAssets']['__deferred']['uri']
			flag = 0
		print("GET Status..............................: " + str(response.status_code))
		print("Media Job Status........................: " + amspy.translate_job_state(job_state))
	else:
		print("GET Status..............................: " + str(response.status_code) + " - Media Job: '" + asset_id + "' Listing ERROR." + str(response.content))
	time.sleep(5)

## getting the output Asset id
print ("\n019 >>> Getting the Indexed Media Asset Id")
response = amspy.get_url(access_token, joboutputassets_uri, False)
if (response.status_code == 200):
	resjson = response.json()
	face_asset_id = resjson['d']['results'][0]['Id']
	print("GET Status..............................: " + str(response.status_code))
	print("Indexed Media Asset Id..................: " + face_asset_id)
else:
	print("GET Status..............................: " + str(response.status_code) + " - Media Job Output Asset: '" + job_id + "' Getting ERROR." + str(response.content))


# Get Asset by using the list_media_asset method and the Asset ID
response = amspy.list_media_asset(access_token,face_asset_id)
if (response.status_code == 200):
    resjson = response.json()
    # Get the container name from the Uri
    outputAssetContainer = resjson['d']['Uri'].split('/')[3]
    print(outputAssetContainer)

### Use the Azure Blob Blob Service library from the Azure Storage SDK to download just the output JSON file
block_blob_service = BlockBlobService(account_name=sto_account_name,account_key=sto_accountKey)
generator = block_blob_service.list_blobs(outputAssetContainer)
for blob in generator:
    print(blob.name)
	if (blob.name.endswith(".json")):
		print("\n\n##### Output Results ######")
		blobText = block_blob_service.get_blob_to_text(outputAssetContainer, blob.name)
		print(blobText.content)
		block_blob_service.get_blob_to_path(outputAssetContainer, blob.name, "output/" + blob.name)
	else:
		block_blob_service.get_blob_to_path(outputAssetContainer, blob.name, "output/" + blob.name)
