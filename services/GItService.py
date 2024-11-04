import asyncio
import re
import aiohttp
from typing import List, Tuple, Dict
import os

from dotenv import load_dotenv

load_dotenv()

class GitService:
    def __init__(self, auth_token: str = None):
        self.IGNORE_PATTERNS = re.compile(r'\.git')

        self.gg = []  # Store file paths for other methods to use
        self.auth_token = os.getenv('GITHUB_TOKEN')
        if not self.auth_token:
            raise ValueError(
                "GitHub token is required. Provide it either through constructor or GITHUB_TOKEN environment variable.")

        # Обновленные заголовки в соответствии с форматом curl
        self.headers = {
            'Accept': 'application/vnd.github+json',
            'Authorization': f'Bearer {self.auth_token}',
            'X-GitHub-Api-Version': '2022-11-28'
        }

    async def get_project_files(self, url: str) -> List[str]:
        """Получает список файлов проекта, игнорируя файлы и папки по шаблону."""
        repo_parts = url.strip().split('/')
        if len(repo_parts) < 5:
            raise ValueError("Неверный формат URL репозитория. Ожидается: https://github.com/USERNAME/REPOSITORY")

        username = repo_parts[-2]
        repository = repo_parts[-1]

        async with aiohttp.ClientSession(headers=self.headers) as session:
            async def get_contents(path: str = '') -> List[str]:
                contents_url = f"https://api.github.com/repos/{username}/{repository}/contents/{path}"
                async with session.get(contents_url) as response:
                    if response.status != 200:
                        response_json = await response.json()
                        raise Exception(
                            f"Ошибка при получении содержимого: {response_json.get('message', 'Unknown error')}")

                    contents = await response.json()
                    files = []

                    for item in contents:
                        if self.IGNORE_PATTERNS.search(item['path']):
                            continue
                        if item['type'] == 'file':
                            files.append(item['path'])
                        elif item['type'] == 'dir':
                            files.extend(await get_contents(item['path']))

                    return files

            self.gg = await get_contents()
            return self.gg

    async def get_file_content(self,url, file_path: str) -> Tuple[str, str]:
        """Получает содержимое указанного файла из GitHub."""
        repo_parts = url.strip().split('/')
        if len(repo_parts) < 5:
            raise ValueError("Неверный формат URL репозитория. Ожидается: https://github.com/USERNAME/REPOSITORY")

        username = repo_parts[-2]
        repository = repo_parts[-1]

        async with aiohttp.ClientSession(headers=self.headers) as session:
            url = f"https://api.github.com/repos/{username}/{repository}/contents/{file_path}"
            async with session.get(url) as response:
                if response.status != 200:
                    response_json = await response.json()
                    raise Exception(f"Ошибка при получении файла: {response_json.get('message', 'Unknown error')}")

                content = await response.json()
                import base64
                decoded_content = base64.b64decode(content['content']).decode('utf-8')
                return file_path, decoded_content

    async def get_changes_files_by_username(self, repository_url: str, username: str) -> List[str]:
        """Возвращает список файлов, измененных указанным пользователем."""
        repo_parts = repository_url.strip().split('/')
        if len(repo_parts) < 5:
            raise ValueError("Неверный формат URL репозитория. Ожидается: https://github.com/USERNAME/REPOSITORY")

        repo_owner = repo_parts[-2]
        repository = repo_parts[-1]

        async with aiohttp.ClientSession(headers=self.headers) as session:
            commits_url = f"https://api.github.com/repos/{repo_owner}/{repository}/commits"
            params = {'author': username}

            async with session.get(commits_url, params=params) as response:
                if response.status != 200:
                    response_json = await response.json()
                    return []

                commits = await response.json()
                modified_files = set()

                for commit in commits:
                    commit_sha = commit['sha']
                    commit_url = f"https://api.github.com/repos/{repo_owner}/{repository}/commits/{commit_sha}"

                    async with session.get(commit_url) as commit_response:
                        if commit_response.status != 200:
                            continue

                        commit_data = await commit_response.json()
                        for file in commit_data['files']:
                            if not self.IGNORE_PATTERNS.search(file['filename']):
                                modified_files.add(file['filename'])

                return sorted(list(modified_files))

    async def get_user_diff_with_file_content(self, repository_url: str, username:str, file_path: str) -> str:
        """Возвращает изменения, сделанные пользователем в указанном файле."""
        repo_parts = repository_url.split('/')
        if len(repo_parts) < 3:
            raise ValueError("Неверный формат пути к файлу")

        repo_owner = repo_parts[-2]
        repository = repo_parts[-1]
        file_path_in_repo = '/'.join(repo_parts[2:])

        async with aiohttp.ClientSession(headers=self.headers) as session:
            commits_url = f"https://api.github.com/repos/{repo_owner}/{repository}/commits"
            params = {'path': file_path, 'author': username}

            async with session.get(commits_url, params=params) as response:
                if response.status != 200:
                    response_json = await response.json()
                    raise Exception(f"Ошибка при получении коммитов: {response_json.get('message', 'Unknown error')}")

                commits = await response.json()
                changes = []

                for commit in commits:
                    commit_sha = commit['sha']
                    commit_url = f"https://api.github.com/repos/{repo_owner}/{repository}/commits/{commit_sha}"

                    async with session.get(commit_url) as commit_response:
                        if commit_response.status != 200:
                            continue

                        commit_data = await commit_response.json()
                        for file in commit_data['files']:
                            if file['filename'] == file_path:
                                patch = file.get('patch', '')
                                if patch:
                                    changes.extend(
                                        line for line in patch.split('\n')
                                        if line.startswith('+') or line.startswith('-')
                                    )

                return '\n'.join(changes)

    async def get_top_repos(self, github_url: str, limit: int = 5) -> List[Dict]:
        username = github_url.split('/')[-1]
        # headers = {'Accept': 'application/vnd.github.v3+json'}

        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(f"https://api.github.com/users/{username}/repos") as response:
                if response.status != 200:
                    return []
                repos = await response.json()

            non_fork_repos = [repo for repo in repos if not repo['fork']]
            tasks = [self.fetch_repo_commits(session, username, repo['name']) for repo in non_fork_repos]
            commit_counts = await asyncio.gather(*tasks)

            repo_info = [{
                'name': repo['name'],
                'description': repo['description'] or 'Нет описания',
                'url': repo['html_url'],
                'last_commit_date': repo['pushed_at'],
                'commit_count': count,
                'stars': repo['stargazers_count']
            } for repo, count in zip(non_fork_repos, commit_counts)]

            return sorted(
                repo_info,
                key=lambda x: x['commit_count'],
                reverse=True
            )[:limit]

    async def fetch_repo_commits(self, session: aiohttp.ClientSession, username: str, repo_name: str) -> int:
        url = f"https://api.github.com/repos/{username}/{repo_name}/commits"
        async with session.get(url, params={'author': username, 'per_page': 1}) as response:
            return self.extract_commit_count(response.headers.get('Link', ''))

    def extract_commit_count(self, link_header: str) -> int:
        if not link_header:
            return 1
        match = re.search(r'page=(\d+)>; rel="last"', link_header)
        return int(match.group(1)) if match else 1