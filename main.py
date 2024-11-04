import uuid
from typing import List, Optional

from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from services.AgencyService import AgencyService, AgencyParams, AgencyConfig
from info import info
from services.ChatService import generate_answer

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sessions={}
agency = {}


class RepRequest(BaseModel):
    account_url: str
    account_name: str
    reps_url: list[str]

class AccountRequest(BaseModel):
    account_url: str
    account_name: str
    rep_analysis: int

class ResponseClass(BaseModel):
    chat_id : str

class Message(BaseModel):
    role: str
    content: str

class Messages(BaseModel):
    messages: list[Message]
    chat_id: str

class Response(BaseModel):
    grade: Optional[str]
    soft_skills: Optional[dict[str, float]]
    final: Optional[str]
    skills: Optional[dict[str, str]]

class ChatResponse(BaseModel):
    answer: str

@app.post("/rep")
async def rep(cc: RepRequest)-> Response:
    chat_id = str(uuid.uuid4())
    agency_config = AgencyConfig(
        max_iteration=23,
        check_hardskill=True,
        check_code_style=True,
        check_softskill=True,
        chat_id=chat_id
    )
    urls = [{'url': url} for url in cc.reps_url]
    agency_params = AgencyParams(
        account_url=cc.account_url,
        account_name=cc.account_name,
        top_k_repositories=len(cc.reps_url),
        reps_url = urls
    )
    
    agency = AgencyService(config=agency_config, params=agency_params)
    await agency.profile_analysis()
    nn = Response(**info[chat_id])
    return nn

@app.post("/account")
async def account(dd: AccountRequest) -> Response:
    chat_id = str(uuid.uuid4())
    agency_config = AgencyConfig(
        max_iteration=23,
        check_hardskill=True,
        check_code_style=True,
        check_softskill=True,
        chat_id=chat_id
    )
    agency_params = AgencyParams(
        account_url=dd.account_url,
        account_name=dd.account_name,
        top_k_repositories=dd.rep_analysis,
        reps_url=[]
    )
    agency = AgencyService(config=agency_config, params=agency_params)
    await agency.profile_analysis()
    nn = Response(**info[chat_id])
    return nn



@app.post("/chat")
async def chat(req: Messages)-> ChatResponse:
    if req.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session ID not found")
    response = await generate_answer(req.session_id, req.messages)
    return ChatResponse(answer=response)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
