from fastapi import APIRouter
from fastapi.responses import StreamingResponse, Response


from dotenv import load_dotenv
import os
import openai

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import time

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
router = APIRouter()


@router.get("/health")
async def health_check():
    return {"message": "I am healthy"}


def stream_from_openai(llm, query: str):
    llm = ChatOpenAI(model="gpt-4o-mini", streaming=True)
    response = llm.stream(query)
    for chunk in response:
        yield chunk.content


@router.get("/stream_answer")
async def stream_answer(query: str):
    streaming = True
    llm = ChatOpenAI(model="gpt-4o-mini", streaming=streaming)

    start_time = time.time()

    if streaming:
        response = StreamingResponse(
            stream_from_openai(llm, query), media_type="text/plain"
        )
    else:
        response = Response(llm.invoke(query).content, media_type="text/plain")

    end_time = time.time()
    duration = end_time - start_time
    print(f"Response time: {duration} seconds")

    return response
