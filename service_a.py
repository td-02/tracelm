import requests
from fastapi import FastAPI
from tracelm.integrations.fastapi import TraceLMMiddleware
from tracelm.integrations.requests import patch_requests

patch_requests()

app = FastAPI()
app.add_middleware(TraceLMMiddleware)


@app.get("/")
async def root():
    requests.get("http://127.0.0.1:8002/")
    return {"ok": True}
