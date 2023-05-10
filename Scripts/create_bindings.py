import os
from os.path import exists
import hashlib
import json
from typing import Union, Any
import urllib.request
import urllib
from datetime import datetime
from urllib.parse import urlparse, unquote
from pathlib import Path
import jwt

SECRET_KEY = ""

JCALGTEST_RESULTS_BINDINGS_PATH = "../jcAlgTestResultsBindings"
DEMO_BINDINGS_PATH = "../Demonstration Bindings"

metadata_file_headers_base = [[{"measurement_tool": "JCAlgtest",
                                "measurement_author": "Petr Svenda",
                                "metadata_url": "https://raw.githubusercontent.com/crocs-muni/jcalgtest_results/main/javacard/Profiles/results/NXP_J2E145G_ICFabDate_2013_025_ALGSUPPORT__3b_f9_13_00_00_81_31_fe_45_4a_43_4f_50_32_34_32_52_33_a2_(provided_by_PetrS_and_Lukas_Malina).csv",
                                "metadata_type": "JCAlgTest algorithm support",
                                "metadata_preview": "https://www.fi.muni.cz/~xsvenda/jcalgtest/pics/logo.png"},
                               {"measurement_tool": "JCAlgtest",
                                "measurement_author": "Matus Nemec",
                                "metadata_url": "https://owncloud.cesnet.cz/index.php/s/Ihhw3BKKzKTaxB9/download?path=%2FCard%2FNXP%20J2E145G%201024b&files=00250496.csv",
                                "metadata_type": "RSA key analysis",
                                "metadata_preview": "https://owncloud.cesnet.cz/index.php/s/Ihhw3BKKzKTaxB9/download?path=%2FCard%2FNXP%20J2E145G%201024b&files=nxpjcop3_j2e145g.PNG"},
                               {"measurement_tool": "JCAlgtest",
                                "measurement_author": "David Komarek",
                                "metadata_url": "https://is.muni.cz/th/fa6tq/thesis.pdf",
                                "metadata_type": "RSA powertrace",
                                "metadata_preview": "https://drive.google.com/uc?id=1pjFalwnhxWAE0EgYrZJ2v1fTHV6fnSUi"}],
                              ]

bindings_data = [{
    "bindings": [
        {
            "certificate_ids": ["NIST-2247", "NSCIB-CC-13-37760-CR2"],
            "metadata_header_url": "https://raw.githubusercontent.com/crocs-muni/seccerts-overlay/main/Demonstration%20Bindings/Headers/demonstration_data_header.json",
        }
    ],
    "author": "CROCS",
}]


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
        nonpath_parts = (
            parsed_url.scheme,
            parsed_url.netloc,
            '',
            parsed_url.params,
            parsed_url.query,
            parsed_url.fragment)
        nonpath_url = urllib.parse.urlunparse(nonpath_parts)
        url = nonpath_url + urllib.parse.quote(path)
        print("Retrieving remote file: " + url)
        try:
            urllib.request.urlretrieve(url, filepath)
        except:
            url = nonpath_url + path
            print(f"Error, Trying with {url}")
            urllib.request.urlretrieve(url, filepath)
    else:
        filepath = unquote(urlparse(url).path)
    return filepath


def get_metadata_file_hash(url: str) -> str:
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
    return sha256.digest().hex()


def get_jwt(data: dict[str, Union[str, list[Any]]]) -> str:
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
        "metadata_sha256": get_metadata_file_hash(url),
        "timestamp": str(datetime.now()),
    }


def create_metadata_headers_obj(
        metadata_headers: list[dict[str, Any]]) -> dict[str, Any]:
    """ Creates metadata headers obj

    Args:
        metadataHeaders (dict[str, Union[str, list]]): Data to be in the result

    Returns:
        dict[str, Union[str, list]]: given data plus hash, timestamp and version
    """
    result = {
        "data": list(
            map(lambda x: get_metadata_metadata(
                x["metadata_url"]) | x, metadata_headers)
        ),
        "version": "1.0",
    }

    for header in result["data"]:
        if not header["measurement_author"]:
            header["measurement_author"] = "Unknown author"

    return result


def create_metadata_headers_file(
        headers_data: list[dict[str, Any]], headers_path: str) -> None:
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
        "timestamp": str(datetime.now()),
    }


def create_metadata_binding(
        metadata_binding_obj: dict[str, Any]) -> dict[str, str]:
    """ Verifies JWT of the bound header and
        Creates metadata binding obj from the given data and addtional metadata about the file

    Args:
        metadataBindingObj (dict[str, Union[str, list]]): base binding data object

    Returns:
        dict[str, str]: Base binding data object enriched with metadata
    """
    if not verify_jwt(metadata_binding_obj["metadata_header_url"]):
        print(
            f'Header JWT verification failed for {metadata_binding_obj["metadata_header_url"]}')
    else:
        print("JWT verification passed")

    return get_binding_metadata() | metadata_binding_obj


def create_binding_file(
        binding_data: dict[str, Any], bindings_file_path: str) -> None:
    """ Creates a binding file at the given location from the given base data

    Args:
        bindingsData (dict[str, Union[str, list]]): base binding data
        bindingsFilePath (str): Where to create the binding file
    """
    bindings = {
        "data": list(map(create_metadata_binding, binding_data["bindings"])),
        "author": binding_data["author"],
        "version": "1.0",
    }
    with open(bindings_file_path, "w", encoding='utf-8') as f:
        bindings["JWT"] = get_jwt(bindings)
        f.write(json.dumps(bindings))


def match_certs_to_jcalgtest_files() -> dict[str, list[tuple[str, str]]]:
    """Matches the certificates names to jcalgtest files names.

    Returns:
        dict[str, tuple[str, str]]: Matches dictionary in format cert_id: filename, fileurl
    """
    from jcalgtest_results_utils import clear_and_tokenize_file_names

    def get_cert_data() -> dict[str, Any]:
        """Load cert_data from the json file where yhey are stored

        Returns:
            any: json cert data
        """
        with open("cert_data.json", "r", encoding='utf-8') as f:
            return json.load(f)

    files = clear_and_tokenize_file_names()
    matches: dict[str, list[tuple[str, str]]] = {}
    for cert_id, name in get_cert_data().items():
        for file, (tokens, url) in files.items():
            matched_tokens = []
            for token in tokens:
                if token in name.lower().split(" "):
                    matched_tokens.append(token)
            if len(matched_tokens) > 0:
                if cert_id in matches:
                    matches[cert_id].append((file, urllib.parse.unquote(url)))
                else:
                    matches[cert_id] = [(file, urllib.parse.unquote(url))]

    with open("matches.json", "w", encoding='utf-8') as f:
        f.write(json.dumps(matches))

    return matches


def create_headers_from_matches(
        matches: dict[str, list[tuple[str, str]]]) -> None:
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
                "measurement_tool": "JCAlgtest",
                "measurement_author": get_author_from_file_name(file),
                "metadata_url": url,
            }
            create_metadata_headers_file([header], path)


def create_bindings_from_matches_and_headers(
        matches: dict[str, list[tuple[str, str]]], bindings_file_path: str) -> None:
    """ Creates bindings from the given matches and existing header files

    Args:
        matches (dict[str, tuple[str, str]]): Matches of certs to header file names
    """
    os.makedirs(bindings_file_path, exist_ok=True)
    bindings = {}
    for match in matches:
        for file, _ in matches[match]:
            url = f"https://raw.githubusercontent.com/crocs-muni/seccerts-overlay/main/jcAlgTestResultsBindings/Headers/jcalgtest_{file}.json"
            if url not in bindings:
                bindings[url] = [match]
            else:
                bindings[url].append(match)

    processed_bindings = [
        {
            "certificate_ids": list(map(lambda x: "NIST-" + x if "CC" not in x and "NIST" not in x else x, ids)),
            "metadata_header_url": url,
        }
        for url, ids in bindings.items()
    ]

    i = 0
    while len(processed_bindings) >= 0:
        path = os.path.join(
            bindings_file_path,
            "Bindings",
            f"jcalgtest_{i}_bindings.json")
        if len(processed_bindings) >= 50:
            create_binding_file(
                {"bindings": processed_bindings[:50], "author": "xmoravec"}, path)
            processed_bindings = processed_bindings[50:]
        else:
            create_binding_file(
                {"bindings": processed_bindings, "author": "xmoravec"}, path)
            break
        i += 1


def create_demonstration_bindings_and_headers(
        target_directory: str, header_data: list[list[dict[str, str]]], binding_data: list[dict[str, Any]]) -> None:
    """ Creates binding files from minimal header and bindings data

    Args:
        target_directory (str): _description_
    """
    os.makedirs(target_directory, exist_ok=True)
    header_path = os.path.join(
        target_directory, "Headers", "demonstration_data_header.json")
    binding_path = os.path.join(
        target_directory, "Bindings", "demonstration_binding.json")

    for header in header_data:
        create_metadata_headers_file(header, header_path)
    for binding in binding_data:
        create_binding_file(binding, binding_path)


if __name__ == "__main__":
    '''
    # This is how you can create bindings for jcalgest result files
    if exists("matches.json"):
        with open("matches.json", "r", encoding='utf-8') as f:
            print("Loading matches from cached matches.json")
            matches = json.load(f)
    else:
        matches = match_certs_to_jcalgtest_files()
    create_headers_from_matches(matches)
    create_bindings_from_matches_and_headers(
        matches, JCALGTEST_RESULTS_BINDINGS_PATH)
    '''

    create_demonstration_bindings_and_headers(
        DEMO_BINDINGS_PATH, metadata_file_headers_base, bindings_data)
