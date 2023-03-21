import hashlib
import pathlib
import json
import jwt
import urllib.request
from datetime import datetime
from urllib.parse import urlparse, unquote
from os.path import exists
from pathlib import Path

SECRET_KEY = "SOME_PROPER_KEY_HERE"


class DataIntegrityError(Exception):
    pass


def is_local(url):
    url_parsed = urlparse(url)
    if url_parsed.scheme in ('file', ''):
        print(f"The URL: {url} Identified as local")
        return exists(url_parsed.path)
    print(f"The URL: {url} Identified as NOT local")
    return False


metadataFileHeadersObjs = [[
    {
        "measurementTool": "JCAlgtest",
        "measurementAuthor": "CROCS",
        "metadataURL": "https://raw.githubusercontent.com/crocs-muni/jcalgtest_results/main/javacard/Profiles/performance/fixed/Feitian_JavaCOS_3.0.4____PERFORMANCE_SYMMETRIC_ASYMMETRIC_DATAFIXED_1557852970194__3b_fc_18_00_00_81_31_80_45_90_67_46_4a_00_64_16_06_00_00_00_00_1e.csv",
    }
],
    [
    {
        "measurementTool": "JCAlgtest",
        "measurementAuthor": "CROCS",
        "metadataURL": "https://raw.githubusercontent.com/crocs-muni/jcalgtest_results/main/javacard/Profiles/performance/fixed/Infineon_SECORA_ID_X_Batch_16072021_SALES____PERFORMANCE_SYMMETRIC_ASYMMETRIC_DATAFIXED_1627630268599__3b_88_80_01_00_00_00_11_77_81_c3_00_2d_(provided_by_Thoth).csv",
    }
]
]

metadataBindingsObj = {
    "bindings": [
        {
            "certificateIDs": ["SERTIT-116"],
            "metadataHeaderURL": "https://raw.githubusercontent.com/crocs-muni/seccerts-overlay/main/Examples/Headers/example_header_0.json",
        },
        {
            "certificateIDs": ["NSCIB-CC-0031318-CR2", "NSCIB-CC-0031318-CR3"],
            "metadataHeaderURL": pathlib.Path("/home/xmoravec/Dipl/security-analytics-pipeline/metadataBindings/metadataHeaders/example_header_1.json").as_uri(),
        }
    ],
    "author": "CROCS"
}


def getMetadataFileHash(url):
    metadataFilePath = url
    if not is_local(url):
        metadataFilePath = "metadata.csv"
        urllib.request.urlretrieve(url, metadataFilePath)
    else:
        metadataFilePath = unquote(urlparse(url).path)

    sha256 = hashlib.sha256()
    BUFF_SIZE = 65536
    with open(metadataFilePath, 'rb') as f:
        data = f.read(BUFF_SIZE)
        while data:
            sha256.update(data)
            data = f.read(BUFF_SIZE)
    return sha256.digest()


def getMetadataMetadata(url):
    return {
        "metadataSHA256": "{0}".format(getMetadataFileHash(url)),
        "timeStamp": datetime.now().__str__(),
    }


def createMetadataHeader(metadataHeaders):
    return {"data": list(map(lambda x: getMetadataMetadata(x["metadataURL"]) | x, metadataHeaders))}


def createMetadataHeadersFile(headersData, headersPath):
    headers = list(map(createMetadataHeader, headersData))
    pathTokens = headersPath.split(".")
    for i, elem in enumerate(headers):
        headersPath = Path(
            "".join(pathTokens[:1] + [f"_{i}."] + pathTokens[1:]))
        with open(headersPath, 'w') as f:
            token = jwt.encode(elem, key=SECRET_KEY, algorithm="HS256")
            elem["JWT"] = token
            f.write(json.dumps(elem))


def verify_jwt(url):
    print(f"verifying jwt of: {url}")
    headerFilePath = url
    if not is_local(url):
        headerFilePath = "header.json"
        urllib.request.urlretrieve(url, headerFilePath)
    else:
        headerFilePath = unquote(urlparse(url).path)

    with open(Path(headerFilePath), 'r') as f:
        header_obj = json.load(f)
        header, signature = {"data": header_obj['data']}, header_obj['JWT']
        decoded = jwt.decode(signature, key=SECRET_KEY, algorithms="HS256")
        if decoded != header:
            raise DataIntegrityError(
                "The data are different than the decoded JWT included with them")
    return True


def getBindingMetadata(url):
    verify_jwt(url)
    return {
        "timeStamp": datetime.now().__str__(),
    }


def createMetadataBinding(metadataBindingObj):
    return getBindingMetadata(metadataBindingObj["metadataHeaderURL"]) | metadataBindingObj


def createBindingFile(bindingsData, bindingsFilePath):
    bindings = {
        "data": list(map(createMetadataBinding, bindingsData["bindings"])),
        "author": bindingsData["author"]
    }
    with open(bindingsFilePath, 'w') as f:
        token = jwt.encode(bindings, key=SECRET_KEY, algorithm="HS256")
        bindings["JWT"] = token
        f.write(json.dumps(bindings))


if __name__ == "__main__":
    createMetadataHeadersFile(metadataFileHeadersObjs,
                              "metadataHeaders/example_header.json")
    createBindingFile(metadataBindingsObj, "bindings/example_bindings.json")
