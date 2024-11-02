import os
import re
from typing import List, Dict, Tuple


class GitService:
    # IGNORE_PATTERNS = re.compile(
    #     r'(\.git|\.yml|\.env|__pycache__|\.DS_Store|Thumbs.db|\.log|\.tmp|\.bak|\.swp|\.swo|\.class|\.o|\.obj|\.exe|\.dll|\.jar|\.war|\.7z|\.zip|\.tar|\.gz|\.rar|\.png|\.jpg|\.jpeg|\.gif|\.svg|\.pdf|\.docx?|\.xlsx?|\.pptx?)$')

    def __init__(self):
        # self.repository_url = repository_url
        self.IGNORE_PATTERNS = re.compile(r'\.git')

    async def get_project_files(self, url) -> List[str]:
        """Получает список папок проекта, игнорируя файлы и папки .git."""

        def create_tree_of_project(directory_name):
            path = f'data/{directory_name}'
            all_paths = []
            for root, dirs, files in os.walk(path):
                if '.git' in root:
                    continue
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    all_paths.append(file_path)

            return all_paths

        directory_path = 'AI-assistant'
        all_paths = create_tree_of_project(directory_path)
        self.gg = all_paths
        return all_paths

    async def get_file_content(self, file_name: str) -> Tuple[str, str]:
        """Получает код из указанного файла."""
        path = f'data/{file_name}'

        try:
            with open(path, 'r', encoding='utf-8') as file:
                content = file.read()
            return path, content
        except FileNotFoundError:
            raise f"Файл '{file_name}' не найден."
        except Exception as e:
            raise f"Произошла ошибка: {e}"

    async def get_changes_files_by_username(self, repository_url, username: str) -> List[str]:
        """Возвращает изменённые файлы, произведенные указанным пользователем."""
        import random
        random.seed(42)
        return random.sample(self.gg, 30)


    async def get_user_diff_with_file_content(self, username: str, file_path: str) -> str:
        """Возвращает код файла с указанием того, что поправил указанный пользователь."""
        pass


