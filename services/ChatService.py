from info import info
from services.LLMService import LLMService
from services.prompts import generate_prompt_use_history


async def generate_answer(session_id, messages):
    llm_service = LLMService()
    prompt = generate_prompt_use_history(info[session_id], messages)

    return await llm_service.fetch_completion(prompt, {"max_tokens": 700, "frequency_penalty": 1})