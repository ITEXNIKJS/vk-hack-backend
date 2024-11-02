import asyncio

from services.GItService import GitService
from services.LLMService import LLMService
from services.prompts import prompt_for_get_interesting_files


async def main():
    ser = LLMService()
    cc = GitService('fdsf')

    all_files = cc.get_project_files()
    changes_files = cc.get_changes_files_by_username("fsfds")

    print(all_files)
    print(changes_files)

    print("\n\n_______________________________________________________________________\n\n")

    bb = await ser.fetch_completion(prompt_for_get_interesting_files(all_files, changes_files), {"max_tokens": 300})

    print(bb)

asyncio.run(main())
