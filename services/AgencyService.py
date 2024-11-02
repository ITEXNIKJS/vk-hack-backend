import asyncio
from lib2to3.fixes.fix_input import context

from attr import dataclass

from services.GItService import GitService
from services.LLMService import LLMService
from services.prompts import prompt_for_get_interesting_files, prompt_for_analysis_file, prompt_summarization_files
from utils.get_repositories_url import get_repositories_url
from utils.parser import parse_files_from_llm_response


@dataclass
class AgencyConfig:
    max_iteration: int
    check_softskill: bool
    check_hardskill: bool
    check_code_style: bool


@dataclass
class AgencyParams:
    account_url: str
    top_k_repositories: str


class AgencyService:

    def __init__(self, config: AgencyConfig, params: AgencyParams):
        self.config = config
        self.account_url = params.account_url
        self.top_k_repositories = params.top_k_repositories
        self.repositories = []
        self.git_service = GitService()
        self.llm_service = LLMService()


    async def profile_analysis(self):
        general_information = self.analysis_account()
        self.repositories = get_repositories_url(self.account_url, self.top_k_repositories)
        tasks = []

        for repository in self.repositories:
            tasks.append(self.repository_analysis(repository))

        results = await asyncio.gather(*tasks)
        response = await self.llm_service.fetch_completion(prompt_for_analysis_file(results),
                                                          {"max_tokens": 500})

        return response


    async def repository_analysis(self, repository_url):
        files = self.git_service.get_project_files(repository_url)
        changes_file = self.git_service.get_changes_files_by_username(repository_url, self.account_url)
        response = await self.llm_service.fetch_completion(prompt_for_get_interesting_files(files, changes_file), {"max_tokens": 400})
        file_path_for_analysis = parse_files_from_llm_response(response)
        if not len(file_path_for_analysis) > 0:
            raise Exception('Ошибка')
        tasks = []

        for file_path in file_path_for_analysis:
            tasks.append(self.file_analysis(file_path))

        results = await asyncio.gather(*tasks)
        response = await self.llm_service.fetch_completion(prompt_summarization_files(results),
                                                          {"max_tokens": 500})
        return repository_url, response


    async def file_analysis(self, file_path):
        file_context = self.git_service.get_project_files(file_path)
        response = await self.llm_service.fetch_completion(prompt_for_analysis_file(file_context),
                                                          {"max_tokens": 500})
        return response


    async def analysis_account(self):
        """Надо вернуть общую информацию, основные языки программирования, активность, опыт (с какого года на чём пишет)"""
        # Лучше вернуть dataclass а не вот это всё.
        return {"languages": ["JS", "Kotlin"], "active_status": "active", "experience": ["2 года", "5 месяцев"]}

