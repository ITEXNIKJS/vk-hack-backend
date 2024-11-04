import asyncio
import json
import os
from asyncio import gather
from itertools import count
from select import select
from typing import List
from unicodedata import category

import aiohttp
from attr import dataclass

from services.GItService import GitService
from services.LLMService import LLMService
from services.prompts import prompt_for_get_interesting_files, prompt_for_analysis_file, \
    prompt_summarization_fast_analysis, \
    generate_get_libs_prompt, generate_code_review_prompt, final_summarization, steck, generate_soft_skills
from utils.get_repositories_url import get_repositories_url
from utils.parser import parse_files_from_llm_response, parse_libs_name_from_llm_output, extract_info, parse_libraries, \
    check_text
from info import info


@dataclass
class AgencyConfig:
    max_iteration: int
    check_softskill: bool
    check_hardskill: bool
    check_code_style: bool
    chat_id: str


@dataclass
class AgencyParams:
    account_url: str
    top_k_repositories: int
    account_name: str
    reps_url: List[str]



class AgencyService:

    def __init__(self, config: AgencyConfig, params: AgencyParams):
        self.config = config
        self.account_url = params.account_url
        self.account_name = params.account_name
        self.top_k_repositories = params.top_k_repositories
        self.repositories = []
        self.git_service = GitService(params.account_url)
        self.llm_service = LLMService()
        self.repositories = params.reps_url
        self.session_id = config.chat_id
        self.count_iter = 0
        self.current_iter = 0


    async def profile_analysis(self):
        info[self.session_id] = {'chat_id': self.session_id}
        if not len(self.repositories) > 0:
            self.repositories = await self.git_service.get_top_repos(self.account_url, self.top_k_repositories)
        rep = [repos['url'] for repos in self.repositories]
        tasks = [self.fast_analysis(rep)]

        for repository in rep:
            tasks.append(self.repository_analysis(repository))

        results = await asyncio.gather(*tasks)
        code_analysis = []
        libs_dict = {}
        lang = []
        soft_skills = {}
        dev_class = []
        for res in results:
            if res:
                if res[0] == 'hard':
                    code_analysis.extend(res[1])
                    for key, value in res[3].items():
                        if key in soft_skills:
                            soft_skills[key] = (soft_skills[key] + value) / 2
                        else:
                            soft_skills[key] = value
                    for key, value in res[2].items():
                        if key not in libs_dict:
                            libs_dict[key] = value
                if res[0] == 'fast':
                    lang, dev_class, resp = res[1], res[2], res[3]


        grade = 'Junior'
        score = 0
        count = 0
        for code_resume in code_analysis:
            if 'Junior' in code_resume:
                score+=1
                count+=1
            elif 'Middel' in code_resume:
                score+=2
                count += 1
            elif 'Senior' in code_resume:
                score+=3
                count += 1

        if count == 0:
            score = score / 1
        else:
            score = score / count
        if score >= 2.1:
            grade = "Senior"
        elif score >= 1.7:
            grade = "Middel"

        json_for_front = {"grade": grade, "soft_skills": soft_skills}
        info[self.session_id].update(json_for_front)
        tasks = []
        tasks.append(self.test1(lang, dev_class, code_analysis, grade))
        tasks.append(self.test2(libs_dict))

        results = await asyncio.gather(*tasks)

        return results

    async def test1(self, lang, dev_class, code_analysis, grade):
        try:
            cc = await self.llm_service.fetch_completion(final_summarization(lang, dev_class, code_analysis, grade),
                                              {"max_tokens": 600, "frequency_penalty": 1})
            json_for_front = {"final": cc}
            info[self.session_id].update(json_for_front)
            return "result", await self.llm_service.fetch_completion(final_summarization(lang, dev_class, code_analysis, grade),
                                              {"max_tokens": 600, "frequency_penalty": 1})
        except:
            return self.test1(lang,dev_class,code_analysis,grade)

    async def test2(self, libs_dict):
        try:
            response = await self.llm_service.fetch_completion(steck(libs_dict),
                                              {"max_tokens": 300, "frequency_penalty": 1})
            cc = parse_libraries(response)
            json_for_front = {"skills": cc}
            info[self.session_id].update(json_for_front)
            return "skills", cc
        except:
            return self.test2(libs_dict)

    async def repository_analysis(self, repository_url):
        async def get_files(cc):
            try:
                response = await self.llm_service.fetch_completion(prompt_for_get_interesting_files(cc), {"max_tokens": 400})
                file_path_for_analysis = parse_files_from_llm_response(response)
                return file_path_for_analysis
            except:
                return []

        changes_file = await self.git_service.get_changes_files_by_username(repository_url, self.account_name)
        file_path_for_analysis = await get_files(changes_file)
        if not len(file_path_for_analysis) > 0:
            return
        self.count_iter += len(file_path_for_analysis)

        tasks = []

        for file_path in file_path_for_analysis:
            tasks.append(self.file_analysis(file_path, repository_url))

        results = await asyncio.gather(*tasks)
        code_analysis = []
        libs_dict = {}
        soft_skills = {}
        for res in results:
            if res:
                if res[0]:
                    if res[0][0] == 'steck':
                        for lib, description in res[0][1].items():
                            if lib not in libs_dict:
                                libs_dict[lib] = description
                if res[1]:
                    if res[1][0] == 'review':
                        code_analysis.append(res[1][1])
                if res[2]:
                    if res[2][0] == 'soft_skills':
                        for key, value in res[2][1].items():
                            if key in soft_skills:
                                soft_skills[key] = (soft_skills[key] + value) / 2
                            else:
                                soft_skills[key] = value

        return "hard", code_analysis, libs_dict, soft_skills

    async def fast_analysis(self, repository_urls):

        async def req(project_tree):
            try:
                response = await self.llm_service.fetch_completion(prompt_for_analysis_file(project_tree),
                                                                   {"max_tokens": 75})
                response = extract_info(response)
                return response
            except:
                return req(project_tree)

        project = [req(await self.git_service.get_changes_files_by_username(url, self.account_name)) for url in repository_urls]
        responses = await asyncio.gather(*project)
        lang = set()
        dev_class = set()
        occupation = set()
        for response in responses:
            if response:
                if response['Языки']:
                    lang.update(response['Языки'])
                if response['Класс']:
                    dev_class.add(response['Класс'])
                if response['Род занятий']:
                    occupation.add(response['Род занятий'])
        try:
            resp = await self.llm_service.fetch_completion(prompt_summarization_fast_analysis(lang, dev_class, occupation), {"max_tokens": 100})
            json_for_front = {"langs": list(lang), "dev_class": list(dev_class), "occupation": resp}
            info[self.session_id].update(json_for_front)
            return 'fast', lang, dev_class, resp
        except:
            info[self.session_id].update({"langs": list(lang), "dev_class": list(dev_class), "occupation": ""})
            return 'fast', lang, dev_class, ''



    async def file_analysis(self, file_path, repository_url):
        try:
            file_context = await self.git_service.get_user_diff_with_file_content(repository_url, self.account_name, file_path)
            file_name = os.path.basename(file_path)
            data_commits = await self.__get_commits_data(repository_url, self.account_name)
            tasks = []
            tasks.append(self.__analysis_steck(file_context)) # Анализируем стек технологий
            tasks.append(self.__analysis_code(file_name, file_context)) # Анализируем чистоту кода и оставленные комментарии
            tasks.append(self.__analysis_soft_skills(data_commits, file_context)) # Анализируем soft_skills по коммитам и комментариям к коду

            results = await asyncio.gather(*tasks)
            return results
        except:
            return

    async def __analysis_steck(self, context):
        try:
            response = await self.llm_service.fetch_completion(generate_get_libs_prompt(context),
                                                    {"max_tokens": 200})
            parser_data = parse_libraries(response)
            return "steck", parser_data
        except:
            return

    async def __analysis_code(self, file_name, context):
        try:
            response = await self.llm_service.fetch_completion(generate_code_review_prompt(context),
                                                    {"max_tokens": 100, "frequency_penalty": 1 })
            return "review", response
        except:
            return

    async def __analysis_soft_skills(self, data_commits, context):
        try:
            response = await self.llm_service.fetch_completion((generate_soft_skills(data_commits, context)),
                                                    {"max_tokens": 400})
            response = check_text(response)
            return "soft_skills", response
        except:
            return

    async def __get_commits_data(self, repository_url: str, username: str):
        repo_parts = repository_url.strip().split('/')
        if len(repo_parts) < 5:
            raise ValueError("Неверный формат URL репозитория. Ожидается: https://github.com/USERNAME/REPOSITORY")

        repo_owner = repo_parts[-2]
        repository = repo_parts[-1]

        headers = {
            'Accept': 'application/vnd.github+json',
            'Authorization': f"Bearer {os.getenv('GITHUB_TOKEN')}",
            'X-GitHub-Api-Version': '2022-11-28'
        }

        async with aiohttp.ClientSession(headers=headers) as session:
            commits_url = f"https://api.github.com/repos/{repo_owner}/{repository}/commits"
            params = {'author': username, 'per_page': 100}

            async with session.get(commits_url, params=params) as response:
                if response.status != 200:
                    response_json = await response.json()
                    return []

                commits = await response.json()

                # Извлекаем и возвращаем только текст сообщений коммитов
                commit_messages = [commit['commit']['message'] for commit in commits]
                return commit_messages

# async def main():
#     config = AgencyConfig(
#         max_iteration=23,
#         check_hardskill=True,
#         check_code_style=True,
#         check_softskill=True,
#     )
#     params =  AgencyParams(
#         account_url = "https://github.com/Gerbylev",
#         account_name="Gerbylev",
#         top_k_repositories = 10,
#         reps_url=[]
#     )
#     agency_service = AgencyService(config, params)
#     cc = await agency_service.profile_analysis("fds")
#
# if __name__ == "__main__":
#     asyncio.run(main())