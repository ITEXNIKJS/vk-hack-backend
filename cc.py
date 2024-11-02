import requests
from typing import List


def get_repository_files(repo_url: str) -> List[str]:
    repo_parts = repo_url.strip().split('/')
    if len(repo_parts) < 5:
        raise ValueError("Неверный формат URL репозитория. Ожидается: https://github.com/USERNAME/REPOSITORY")

    username = repo_parts[-2]
    repository = repo_parts[-1]

    def get_contents(path: str = '') -> List[str]:
        contents_url = f"https://api.github.com/repos/{username}/{repository}/contents/{path}"
        response = requests.get(contents_url)

        if response.status_code != 200:
            raise Exception(f"Ошибка при получении содержимого: {response.json().get('message', 'Unknown error')}")

        contents = response.json()
        files = []

        for item in contents:
            if item['type'] == 'file':
                files.append(item['path'])
            elif item['type'] == 'dir':
                files.extend(get_contents(item['path']))

        return files

    return get_contents()


def get_user_modified_files(repo_url: str, username_to_find: str) -> List[str]:
    repo_parts = repo_url.strip().split('/')
    if len(repo_parts) < 5:
        raise ValueError("Неверный формат URL репозитория. Ожидается: https://github.com/USERNAME/REPOSITORY")

    username = repo_parts[-2]
    repository = repo_parts[-1]

    commits_url = f"https://api.github.com/repos/{username}/{repository}/commits"
    commits_response = requests.get(commits_url)

    if commits_response.status_code != 200:
        raise Exception(f"Ошибка при получении коммитов: {commits_response.json().get('message', 'Unknown error')}")

    commits = commits_response.json()
    modified_files = set()

    for commit in commits:
        if commit.get('author', {}).get('login') == username_to_find:
            commit_sha = commit['sha']
            commit_details_url = f"https://api.github.com/repos/{username}/{repository}/commits/{commit_sha}"
            commit_details_response = requests.get(commit_details_url)

            if commit_details_response.status_code != 200:
                raise Exception(
                    f"Ошибка при получении деталей коммита: {commit_details_response.json().get('message', 'Unknown error')}")

            commit_details = commit_details_response.json()
            for file in commit_details['files']:
                modified_files.add(file['filename'])

    return sorted(list(modified_files))


def get_file_changes(repo_url: str, username_to_find: str, file_path: str) -> List[str]:
    repo_parts = repo_url.strip().split('/')
    if len(repo_parts) < 5:
        raise ValueError("Неверный формат URL репозитория. Ожидается: https://github.com/USERNAME/REPOSITORY")

    username = repo_parts[-2]
    repository = repo_parts[-1]

    commits_url = f"https://api.github.com/repos/{username}/{repository}/commits?path={file_path}"
    commits_response = requests.get(commits_url)

    if commits_response.status_code != 200:
        raise Exception(f"Ошибка при получении коммитов: {commits_response.json().get('message', 'Unknown error')}")

    commits = commits_response.json()
    all_changes = []

    for commit in commits:
        if commit.get('author', {}).get('login') == username_to_find:
            commit_sha = commit['sha']
            commit_details_url = f"https://api.github.com/repos/{username}/{repository}/commits/{commit_sha}"
            commit_details_response = requests.get(commit_details_url)

            if commit_details_response.status_code != 200:
                raise Exception(
                    f"Ошибка при получении деталей коммита: {commit_details_response.json().get('message', 'Unknown error')}")

            commit_details = commit_details_response.json()
            for file in commit_details['files']:
                if file['filename'] == file_path:
                    patch = file.get('patch', '')
                    if patch:
                        changes = []
                        current_changes = []
                        for line in patch.split('\n'):
                            if line.startswith('@@') or line.startswith('+++') or line.startswith('---'):
                                if current_changes:
                                    changes.extend(current_changes)
                                    current_changes = []
                                continue

                            if line.startswith('+') or line.startswith('-'):
                                current_changes.append(line)

                        if current_changes:
                            changes.extend(current_changes)

                        all_changes.extend(changes)

    return all_changes


repo_url = "https://github.com/Gerbylev/Optics-Hackathon"
username = "kap40nka"
file_path = "DEAP_prod_1.py"

try:
    print("Список всех файлов в репозитории:")
    all_files = get_repository_files(repo_url)
    for file in all_files:
        print(file)

    print("\nСписок файлов, измененных пользователем:")
    modified_files = get_user_modified_files(repo_url, username)
    for file in modified_files:
        print(file)

    print("\nИзменения в конкретном файле:")
    changes = get_file_changes(repo_url, username, file_path)
    for change in changes:
        print(change)

except Exception as e:
    print(f"Ошибка: {e}")