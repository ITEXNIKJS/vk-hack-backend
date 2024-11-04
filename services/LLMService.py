import json

import aiohttp


class LLMService:

    async def fetch_completion(self, prompt: str, args=None) -> str:
        counter = 0
        print(prompt)
        while True:
            try:
                res = await self.__fetch_completion(prompt, (args or {}))
                return res
            except Exception as e:
                counter += 1
                if counter < 3:
                    print("Ошибка при обращение к llama")
                else:
                    raise e

    async def __fetch_completion(self, prompt: str, args) -> str:
            url = "https://vk-devinsight-case.olymp.innopolis.university/generate"

            data = {
                "prompt": [prompt],
                "apply_chat_template": False,
                "temperature": 0,
                **args
            }

            headers = {
                "Content-Type": "application/json"
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=json.dumps(data, ensure_ascii=False), headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        raise "LLM - error"
