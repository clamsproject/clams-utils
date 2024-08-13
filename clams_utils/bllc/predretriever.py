import json
import os
import requests
import hashlib


def download_preds(storage_url, pipeline_json: json, folder_name: os.path = None):
    import tempfile
    # code adapted from Keigh's goldretriever, which is adapted from Angela Lam
    if folder_name is None:
        folder_name = tempfile.TemporaryDirectory().name
    # Make new directory
    # Check if the directory is empty
    if not (len(os.listdir(folder_name)) == 0):
        raise Exception("The folder '" + folder_name + "' already exists and is not empty")
    # send a POST request to the storage api
    response = requests.post(storage_url, pipeline_json, headers={"Content-Type": "application/json"})
    # read the response as json. keys are guids and values are serialized mmif files
    mmifs = json.loads(response.text)
    # iterate through json and save each mmif as its own file
    for mmif in mmifs:
        filename = str(mmif) + ".mmif"
        path = os.path.join(folder_name, filename)
        json.dump(mmifs[mmif], open(path, "w"))
    # return the folder where they are saved
    return folder_name



