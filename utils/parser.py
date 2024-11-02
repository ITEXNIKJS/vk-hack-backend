import re


def parse_files_from_llm_response(response):
    matches = re.search(r'<end_file>(.*?)<end_file>', response, re.DOTALL)
    if matches:
        content = matches.group(1)
        paths = [line.strip() for line in content.splitlines() if re.search(r'/', line)]
        return paths

    solitary_matches = re.findall(r'<end_file>(.*?)$', response, re.DOTALL)
    if solitary_matches:
        content = solitary_matches[0]
        paths = [line.strip() for line in content.splitlines() if re.search(r'/', line)]
        return paths
    return []
