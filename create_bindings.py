import os
from os.path import exists
import hashlib
import pathlib
import json
from typing import Union
import urllib.request
import urllib
from datetime import datetime
from urllib.parse import urlparse, unquote
from pathlib import Path
import jwt

SECRET_KEY = ""

LOCAL_HEADER_PATH = (
    "C:\\Dokumenty\\Diplomovka\\seccerts-overlay\\Examples\\Headers\\example_header_1.json"
)
JCALGTEST_RESULTS_BINDINGS_PATH = (
    "C:\\Dokumenty\\Diplomovka\\seccerts-overlay\\jcAlgTestResultsBindings"
)
metadataFileHeadersObjs = [[{"measurementTool": "JCAlgtest",
                             "measurementAuthor": "CROCS",
                             "metadataURL": "https://raw.githubusercontent.com/crocs-muni/jcalgtest_results/main/javacard/Profiles/performance/fixed/Feitian_JavaCOS_3.0.4____PERFORMANCE_SYMMETRIC_ASYMMETRIC_DATAFIXED_1557852970194__3b_fc_18_00_00_81_31_80_45_90_67_46_4a_00_64_16_06_00_00_00_00_1e.csv",
                             }],
                           [{"measurementTool": "JCAlgtest",
                             "measurementAuthor": "CROCS",
                             "metadataURL": "https://raw.githubusercontent.com/crocs-muni/jcalgtest_results/main/javacard/Profiles/performance/fixed/Infineon_SECORA_ID_X_Batch_16072021_SALES____PERFORMANCE_SYMMETRIC_ASYMMETRIC_DATAFIXED_1627630268599__3b_88_80_01_00_00_00_11_77_81_c3_00_2d_(provided_by_Thoth).csv",
                             }],
                           ]
metadataBindingsObj = {
    "bindings": [
        {
            "certificateIDs": ["SERTIT-116"],
            "metadataHeaderURL": "https://raw.githubusercontent.com/crocs-muni/seccerts-overlay/main/Examples/Headers/example_header_0.json",
        },
        {
            "certificateIDs": [
                "NSCIB-CC-0031318-CR2",
                "NSCIB-CC-0031318-CR3"],
            "metadataHeaderURL": pathlib.Path(LOCAL_HEADER_PATH).as_uri(),
        },
    ],
    "author": "CROCS",
}


def is_local(url: str) -> bool:
    """ Function to check whether the given URL is local

    Args:
        url (str): URL to check

    Returns:
        bool: Whether the given URL is local
    """
    url_parsed = urlparse(url)
    if url_parsed.scheme in ("file", ""):
        return exists(url_parsed.path)
    return False


def get_file_path(url: str) -> str:
    """ Function to get local path from file located by url that can be remote as well.

    Args:
        url (str): URL to get the locate the file

    Returns:
        str: local path to the file
    """
    filepath = url
    if not is_local(url):
        filepath = "metadata.csv"
        parsed_url = urlparse(url)
        path = parsed_url.path
        nonpath_parts = (parsed_url.scheme, parsed_url.netloc, '', parsed_url.params, parsed_url.query, parsed_url.fragment)
        nonpath_url = urllib.parse.urlunparse(nonpath_parts) 
        url = nonpath_url + urllib.parse.quote(path)
        #print("Retrieving remote file: " + url)
        urllib.request.urlretrieve(url, filepath)
    else:
        filepath = unquote(urlparse(url).path)
    return filepath


def get_metadata_file_hash(url: str) -> bytes:
    """ Get Hash of file located by URL

    Args:
        url (str): Location of the file to retrieve

    Returns:
        str: Hash of the located file
    """
    metadata_file_path = get_file_path(url)
    sha256 = hashlib.sha256()
    buff_size = 65536
    with open(metadata_file_path, "rb") as f:
        data = f.read(buff_size)
        while data:
            sha256.update(data)
            data = f.read(buff_size)
    return sha256.digest()


def get_jwt(data: dict[str, Union[str, list]]) -> str:
    """ Encodes the given data into jwt

    Args:
        data (dict[str, Union[str, list]]): data to be encoded

    Returns:
        str: jwt token of the given data
    """
    return jwt.encode(data, key=SECRET_KEY, algorithm="HS256")


def verify_jwt(url: str) -> bool:
    """ Verifies the jwt of the header at the given url

    Args:
        url (str): Location of the header

    Returns:
        bool: Whether the jwt is valid
    """
    header_file_path = get_file_path(url)
    with open(Path(header_file_path), "r", encoding='utf-8') as f:
        header_obj = json.load(f)
        old = header_obj["JWT"]
        del header_obj["JWT"]
        new = get_jwt(header_obj)
        return new == old


def get_metadata_metadata(url: str) -> dict[str, str]:
    """ Get metadata of the given URL file

    Args:
        url (str): url of the file to get metadata for

    Returns:
        dict[str, str]: dictionary with hash and timestamp
    """
    return {
        "metadataSHA256": f"{get_metadata_file_hash(url)}",
        "timeStamp": str(datetime.now()),
    }


def create_metadata_headers_obj(
        metadata_headers: dict[str, Union[str, list]]) -> dict[str, Union[str, list]]:
    """ Creates metadata headers obj

    Args:
        metadataHeaders (dict[str, Union[str, list]]): Data to be in the result

    Returns:
        dict[str, Union[str, list]]: given data plus hash, timestamp and version
    """
    return {
        "data": list(
            map(lambda x: get_metadata_metadata(x["metadataURL"]) | x, metadata_headers)
        ),
        "version": "1.0",
    }


def create_metadata_headers_file(
        headers_data: dict[str, Union[str, list]], headers_path: str) -> None:
    """Create metadata headers file from the minimal headers data at the given path

    Args:
        headersData (dict[str, str]): minimal data required for header construction
        headersPath (str): Path to where the header should be created
    """
    headers = create_metadata_headers_obj(headers_data)
    with open(headers_path, "w", encoding='utf-8') as f:
        headers["JWT"] = get_jwt(headers)
        f.write(json.dumps(headers))


def get_binding_metadata() -> dict[str, str]:
    """ Provides metadata for the binding

    Returns:
        dict[str, str]: additional metadata object
    """
    return {
        "timeStamp": str(datetime.now()),
    }


def create_metadata_binding(
        metadata_binding_obj: dict[str, Union[str, list]]) -> dict[str, str]:
    """ Verifies JWT of the bound header and
        Creates metadata binding obj from the given data and addtional metadata about the file

    Args:
        metadataBindingObj (dict[str, Union[str, list]]): base binding data object

    Returns:
        dict[str, str]: Base binding data object enriched with metadata
    """
    if not verify_jwt(metadata_binding_obj["metadataHeaderURL"]):
        print(
            f'Header JWT verification failed for {metadata_binding_obj["metadataHeaderURL"]}')
    else:
        print("JWT verification passed")

    return get_binding_metadata() | metadata_binding_obj


def create_binding_file(
        bindings_data: dict[str, Union[str, list]], bindings_file_path: str) -> None:
    """ Creates a binding file at the given location from the given base data

    Args:
        bindingsData (dict[str, Union[str, list]]): base binding data
        bindingsFilePath (str): Where to create the binding file
    """
    bindings = {
        "data": list(map(create_metadata_binding, bindings_data["bindings"])),
        "author": bindings_data["author"],
        "version": "1.0",
    }
    with open(bindings_file_path, "w", encoding='utf-8') as f:
        bindings["JWT"] = get_jwt(bindings)
        f.write(json.dumps(bindings))


def match_certs_to_jcalgtest_files() -> dict[str, tuple[str, str]]:
    """Matches the certificates names to jcalgtest files names.

    Returns:
        dict[str, tuple[str, str]]: Matches dictionary in format cert_id: filename, fileurl
    """
    from jcalgtest_results_utils import clear_and_tokenize_file_names
    
    def get_cert_data() -> any:
        """Load cert_data from the json file where yhey are stored

        Returns:
            any: json cert data
        """    
        with open("cert_data.json", "w", encoding='utf-8') as f:
            return json.load(f)

    files = clear_and_tokenize_file_names()
    matches = {}
    for id, name in get_cert_data().items():
        for file, (tokens, url) in files.items():
            matched_tokens = []
            for token in tokens:
                if token in name.lower().split(" "):
                    matched_tokens.append(token)
            if len(matched_tokens) > 0:
                if id in matches:
                    matches[id].append((file, url))
                else:
                    matches[id] = [(file, url)]

    with open("matches.json", "w", encoding='utf-8') as f:
        f.write(json.dumps(matches))

    return matches


def create_headers_from_matches(matches: dict[str, tuple[str, str]]) -> None:
    """ Creates headers objects from matches of certs and data

    Args:
        matches (dict[str, tuple[str, str]]): Matches of certs to metadata file names
    """
    from jcalgtest_results_utils import get_author_from_file_name

    for match in matches:
        for file, url in matches[match]:
            path = os.path.join(
                JCALGTEST_RESULTS_BINDINGS_PATH,
                "Headers",
                f"jcalgtest_{file}.json")
            if exists(path):
                print(f"Header file for {file} already exists, skipping")
                continue
            header = {
                "measurementTool": "JCAlgtest",
                "measurementAuthor": get_author_from_file_name(file),
                "metadataURL": url,
            }
            create_metadata_headers_file([header], path)


def create_bindings_from_matches_and_headers(
        matches: dict[str, tuple[str, str]]) -> None:
    """ Creates bindings from the given matches and existing header files

    Args:
        matches (dict[str, tuple[str, str]]): Matches of certs to header file names
    """
    bindings = {}
    for match in matches:
        for file, _ in matches[match]:
            url = f"https://raw.githubusercontent.com/crocs-muni/seccerts-overlay/main/jcAlgTestResultsBindings/Headers/jcalgtest_{file}.json"
            if url not in bindings:
                bindings[url] = [match]
            else:
                bindings[url].append(match)

    bindings = [
        {
            "certificateIDs": ids,
            "metadataHeaderURL": url,
        }
        for url, ids in bindings.items()
    ]

    i = 0
    while len(bindings) >= 0:
        path = os.path.join(
            JCALGTEST_RESULTS_BINDINGS_PATH,
            "Bindings",
            f"jcalgtest_{i}_bindings.json")
        if len(bindings) >= 50:
            create_binding_file(
                {"bindings": bindings[:50], "author": "xmoravec"}, path)
            bindings = bindings[50:]
        else:
            create_binding_file(
                {"bindings": bindings, "author": "xmoravec"}, path)
            break
        i += 1


if __name__ == "__main__":
    if exists("matches.json"):
        with open("matches.json", "r", encoding='utf-8') as f:
            print("Loading matches from cached matches.json")
            matches = json.load(f)
    else:
        matches = match_certs_to_jcalgtest_files()
    create_headers_from_matches(matches)
    create_bindings_from_matches_and_headers(matches)
