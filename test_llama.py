import asyncio
import aiohttp
from typing import List, Dict
import re







async def main():
    github_url = "https://github.com/karpathy"
    repos = await get_top_repos(github_url, 2)

    for i, repo in enumerate(repos, 1):
        print(f"\n{i}. {repo['name']}")
        print(f"Описание: {repo['description']}")
        print(f"URL: {repo['url']}")
        print(f"Последний коммит: {repo['last_commit_date']}")
        print(f"Количество коммитов: {repo['commit_count']}")
        print(f"Звёзд: {repo['stars']}")


if __name__ == "__main__":
    asyncio.run(main())