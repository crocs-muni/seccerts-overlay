import json

def process_raw_data(raw_data: str) -> dict[str, str]:
    """Processes raw data printed out from mongoDB to a python dictionary

    Args:
        raw_data (str): raw data printed out from mongoDB

    Returns:
        dict[str, str]: Parsed out python dictionary of cert_id: cert_name
    """
    processed = {}
    for line in raw_data.splitlines():
        tokens = list(map(lambda x: x.strip(), line.split(':')))
        if len(tokens) == 2:
            processed[tokens[0]] = tokens[1]
    print(f"Process raw data returning {len(processed)} certs")
    return processed

def get_cert_data() -> any:
    """Load cert_data from the json file where yhey are stored

    Returns:
        any: json cert data
    """    
    with open("cert_data.json", "w", encoding='utf-8') as f:
        return json.load(f)


def clear_and_tokenize_file_names() -> list[list[str]]:
    """Return all cert names as a filtered list of tokens

    Returns:
        list[list[str]]: filtered list of lists of tokens in cert names
    """
    data = get_cert_data()   

    result = []
    for name in data:
        tokens = name.split(" ")
        tokens = [x.strip(")").strip("(").strip("[").strip("]").strip(".csv").lower() for x in tokens]
        tokens = filter(
            lambda x: len(x) > 2 and not x.isnumeric() and not (
                "provided" in x or "xx" in x or "undisclosed" in x) and not all(
                c.isdigit() or c.lower() in 'abcdef' or c.isspace() for c in x), tokens)
        result += [list(tokens)]

    return result
