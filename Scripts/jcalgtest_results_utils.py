import json
from urllib.parse import urlparse
import requests

JCALGTEST_GITHUB_RESULTS_URLS = [
    "https://github.com/crocs-muni/jcalgtest_results/tree/main/javacard/Profiles/aid",
    "https://github.com/crocs-muni/jcalgtest_results/tree/main/javacard/Profiles/performance",
    "https://github.com/crocs-muni/jcalgtest_results/tree/main/javacard/Profiles/performance/fixed",
    "https://github.com/crocs-muni/jcalgtest_results/tree/main/javacard/Profiles/performance/variable",
    "https://github.com/crocs-muni/jcalgtest_results/tree/main/javacard/Profiles/results",
    "https://github.com/crocs-muni/jcalgtest_results/tree/main/javacard/Profiles/results/NXP_JCOP3_J3H145g_P60",
    "https://github.com/crocs-muni/jcalgtest_results/tree/main/javacard/Profiles/results/only_cplc"]


def github_url_to_api(url: str) -> str:
    """
    Transform a public GitHub URL to an API URL.
    """
    parsed_url = urlparse(url)
    api_url = f"https://api.github.com/repos{parsed_url.path}"
    if parsed_url.query:
        api_url += f"?{parsed_url.query}"
    return api_url


def get_author_from_file_name(file_name: str) -> str:
    """Parses out providers name from JCAlgTest result file name

    Args:
        file_name (str): Name of metadata file to parse the name from

    Returns:
        str: Parsed out name of the provider
    """
    if not ("provided" in file_name and "by" in file_name):
        return ""
    name = file_name.split("provided_by_")[1].strip(").csv")
    name = " ".join(name.split("_"))
    return name


def get_jcalgtest_files_names() -> dict[str, str]:
    """ Returns names of files in configured jcalgtest URL repositories

    Returns:
        dict[str, str]: all files in the jcalgtest repositories as name: download_url
    """
    files: dict[str, str] = {}
    for url in JCALGTEST_GITHUB_RESULTS_URLS:
        print("Getting contents of " + url)
        repo_url, dir_path = url.split("/tree", maxsplit=1)
        dir_path = url.split("/main")[1]
        api_url = github_url_to_api(repo_url) + "/contents" + dir_path

        response = requests.get(api_url)
        data = {}
        if response.status_code == 200:
            try:
                data = response.json()
            except json.decoder.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
                print(f"Response content: {response.text.splitlines()[:5]}")
                return files
        else:
            print(
                f"Request failed with status code {response.status_code} - {response.reason}"
            )
        for file in data:
            if file["name"].endswith(".csv"):
                files[file["name"]] = file["download_url"]
    return files


def clear_and_tokenize_file_names() -> dict[str, tuple[list[str], str]]:
    """ Get filtered and cleared words in all jcalgtest results files names.

    Returns:
        dict[str, tuple[list[str], str]]: A dictionary in format file_name: tokens, url
    """
    data = get_jcalgtest_files_names()
    words_to_filter = [
        "open", "xx", "provided", "undisclosed", "abcdef"
        "notanonymousdatafixed", "Chris", "PetrSHenrikWatkinsOmackaThothrichardadam"
        "vault", 'PERFORMANCE', 'SYMMETRIC', 'ASYMMETRIC',
        'DATADEPEND', 'Expert', 'and', 'with', 'editionuniversal',
        'top', 'token', 'usb', 'crypto', 'java'
    ]
    result = {}
    for file, url in data.items():
        name = file.strip(".csv")
        tokens = name.split("_")
        tokens_map = map(lambda x: x.strip(")").strip(
            "(").strip("[").strip("]").strip(".csv").lower(), tokens)
        tokens_filter = filter(
            lambda x: len(x) > 2 and not x.isnumeric() and not all(
                c.isdigit() or c.isspace() for c in x), tokens_map)
        tokens_filter = filter(
            lambda x: True not in [
                x.lower() in word.lower() for word in words_to_filter],
            tokens_filter)
        tokens_filter = filter(lambda x: not any(y.strip('v').isnumeric()
                                                 for y in x.split('.')), tokens_filter)
        result[file] = list(tokens_filter), url

    return result
