import hashlib
import pathlib
import json
from typing import List
import jwt, json
import urllib.request
import urllib
import requests
from datetime import datetime
from urllib.parse import urlparse, unquote
import os
from os.path import exists
from pathlib import Path


SECRET_KEY = "SOME_PROPER_KEY_HERE"

LOCAL_HEADER_PATH = (
    "C:\Dokumenty\Diplomovka\seccerts-overlay\Examples\Headers\example_header_1.json"
)

JCALGTEST_RESULTS_BINDINGS_PATH = (
    "C:\Dokumenty\Diplomovka\seccerts-overlay\jcAlgTestResultsBindings"
)


class DataIntegrityError(Exception):
    pass


def is_local(url):
    url_parsed = urlparse(url)
    if url_parsed.scheme in ("file", ""):
        return exists(url_parsed.path)
    return False


metadataFileHeadersObjs = [
    [
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
    ],
]

metadataBindingsObj = {
    "bindings": [
        {
            "certificateIDs": ["SERTIT-116"],
            "metadataHeaderURL": "https://raw.githubusercontent.com/crocs-muni/seccerts-overlay/main/Examples/Headers/example_header_0.json",
        },
        {
            "certificateIDs": ["NSCIB-CC-0031318-CR2", "NSCIB-CC-0031318-CR3"],
            "metadataHeaderURL": pathlib.Path(LOCAL_HEADER_PATH).as_uri(),
        },
    ],
    "author": "CROCS",
}

JCALGTEST_TO_FIPS_MATCHES = ""


def getMetadataFileHash(url):
    metadataFilePath = url
    if not is_local(url):
        metadataFilePath = "metadata.csv"
        urllib.request.urlretrieve(url, metadataFilePath)
    else:
        metadataFilePath = unquote(urlparse(url).path)

    sha256 = hashlib.sha256()
    BUFF_SIZE = 65536
    with open(metadataFilePath, "rb") as f:
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


def createMetadataHeadersObj(metadataHeaders):
    return {
        "data": list(
            map(lambda x: getMetadataMetadata(x["metadataURL"]) | x, metadataHeaders)
        ),
        "version": "1.0",
    }


def createMetadataHeadersFile(headersData, headersPath):
    headers = createMetadataHeadersObj(headersData)
    with open(headersPath, "w") as f:
        token = jwt.encode(headers, key=SECRET_KEY, algorithm="HS256")
        headers["JWT"] = token
        f.write(json.dumps(headers))


def verify_header_jwt(url):
    # print(f"verifying jwt of: {url}")
    headerFilePath = url
    if not is_local(url):
        headerFilePath = "header.json"
        urllib.request.urlretrieve(url, headerFilePath)
    else:
        headerFilePath = unquote(urlparse(url).path)

    with open(Path(headerFilePath), "r") as f:
        header_obj = json.load(f)
        header, signature = {
            "data": header_obj["data"],
            "version": header_obj["version"],
        }, header_obj["JWT"]
        decoded = jwt.decode(signature, key=SECRET_KEY, algorithms="HS256")
        if decoded != header:
            raise DataIntegrityError(
                "The data are different than the decoded JWT included with them"
            )
    return True


def getBindingMetadata(url):
    verify_header_jwt(url)
    return {
        "timeStamp": datetime.now().__str__(),
    }


def createMetadataBinding(metadataBindingObj):
    return (
        getBindingMetadata(metadataBindingObj["metadataHeaderURL"]) | metadataBindingObj
    )


def createBindingFile(bindingsData, bindingsFilePath):
    bindings = {
        "data": list(map(createMetadataBinding, bindingsData["bindings"])),
        "author": bindingsData["author"],
        "version": "1.0",
    }
    with open(bindingsFilePath, "w") as f:
        token = jwt.encode(bindings, key=SECRET_KEY, algorithm="HS256")
        bindings["JWT"] = token
        f.write(json.dumps(bindings))


def match_certs_to_jcalgtest_files() -> dict[str, tuple[str, str]]:
    from fips_certificates import certs_data as certs
    from jcalgtest_results_utils import clear_and_tokenize_file_names

    files = clear_and_tokenize_file_names()
    matches = {}
    for id, name in certs.items():
        for file, (tokens, url) in files.items():
            matched_tokens = []
            for token in tokens:
                if token in name.lower().split(" "):
                    matched_tokens.append(token)
            if len(matched_tokens) > 0:
                # print(f"matched {len(matched_tokens)} tokens: {matched_tokens} of cert: {id, name} to {file}")
                if id in matches:
                    matches[id].append((file, url))
                else:
                    matches[id] = [(file, url)]

    with open("matches.json", "w") as f:
        f.write(json.dumps(matches))

    return matches


def create_headers_from_matches(matches):
    for match in matches:
        for file, url in matches[match]:
            path = os.path.join(
                JCALGTEST_RESULTS_BINDINGS_PATH, "Headers", f"jcalgtest_{file}.json"
            )
            if exists(path):
                continue
            header = {
                "measurementTool": "JCAlgtest",
                "measurementAuthor": "",
                "metadataURL": url,
            }
            createMetadataHeadersFile([header], path)


def create_bindings_from_matches_and_headers(matches) -> None:
    bindings = {}
    i = 0
    for match in matches:
        for file, _ in matches[match]:
            header_path = os.path.join(
                JCALGTEST_RESULTS_BINDINGS_PATH, "Headers", f"jcalgtest_{file}.json"
            )
            url = urllib.parse.urljoin(
                "file:", urllib.request.pathname2url(header_path)
            )
            if url not in bindings:
                bindings[url] = [match]
            else:
                bindings[url].append(match)

    merged_bindings = [
        {
            "certificateIDs": ids,
            "metadataHeaderURL": url,
        }
        for url, ids in bindings.items()
    ]
    while len(merged_bindings) >= 0:
        path = os.path.join(
            JCALGTEST_RESULTS_BINDINGS_PATH, "Bindings", f"jcalgtest_{i}_bindings.json"
        )
        if len(merged_bindings) >= 50:
            createBindingFile({"bindings": merged_bindings[:50], "author": ""}, path)
            merged_bindings = merged_bindings[50:]
        else:
            createBindingFile({"bindings": merged_bindings, "author": ""}, path)
            break
        i += 1


# path = os.path.join(JCALGTEST_RESULTS_BINDINGS_PATH, "Headers", f"jcalgtest_fips_bindings_{i // 50}.json")

if __name__ == "__main__":
    with open("matches.json", "r") as f:
        matches = json.load(f)
    # matches = match_certs_to_jcalgtest_files()
    # create_headers_from_matches(matches)
    create_bindings_from_matches_and_headers(matches)
