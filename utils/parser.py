import re


def parse_libs_name_from_llm_output(full_text):
    library_list = re.findall(r'\d+\.\s+[^\n]*', full_text)
    output = "\n".join(library_list)
    return output

def parse_files_from_llm_response(response):
    matches = re.search(r'<end_file>(.*?)<end_file>', response, re.DOTALL)
    if matches:
        content = matches.group(1)
        paths = [line.strip() for line in content.splitlines() if re.search(r'.', line)]
        return paths

    solitary_matches = re.findall(r'<end_file>(.*?)$', response, re.DOTALL)
    if solitary_matches:
        content = solitary_matches[0]
        paths = [line.strip() for line in content.splitlines() if re.search(r'/', line)]
        return paths
    return []

def extract_info(text):
    languages_pattern = r'^(?:Языки:\s*(.*))$'
    class_pattern = r'^(?:Класс:\s*(.*))$'
    occupation_pattern = r'^(?:Род занятий:\s*(.*))$'

    result = {}

    languages_match = re.search(languages_pattern, text, re.MULTILINE)
    class_match = re.search(class_pattern, text, re.MULTILINE)
    occupation_match = re.search(occupation_pattern, text, re.MULTILINE)

    if languages_match:
        text =  languages_match.group(1).strip()  # Убираем лишние пробелы
        result["Языки"] = [language.strip() for language in text.split(',')]
    else:
        result["Языки"] = None

    if class_match:
        result["Класс"] = class_match.group(1).strip()  # Убираем лишние пробелы
    else:
        result["Класс"] = None

    if occupation_match:
        result["Род занятий"] = occupation_match.group(1).strip()  # Убираем лишние пробелы
    else:
        result["Род занятий"] = None

    return result


def parse_libraries(text):
    lines = text.strip().split('\n')

    libraries = {}

    for line in lines:
        line = line.strip()
        if '->' in line:
            try:
                name, description = line.split('->', 1)
                libraries[name.strip()] = description.strip()
            except ValueError:
                print(f"Ошибка в строке: {line}")

    return libraries


keywords = ["Ясность общения", "Самоорганизация", "Командное взаимодействие", "Ответственность", "Адаптивность", "Инициативность"]


def check_text(input_text):
    lines = input_text.splitlines()
    results = {keyword: 5 for keyword in keywords}

    for line in lines:
        for keyword in keywords:
            if keyword in line:
                numbers = re.findall(r'\d+', line)
                results[keyword] = int(numbers[0]) if numbers else 5

    return results
