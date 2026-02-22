from fastapi import FastAPI
from tracelm.integrations.fastapi import TraceLMMiddleware
from tracelm.decorator import node

app = FastAPI()
app.add_middleware(TraceLMMiddleware)


@node("compute")
def compute():
    return 42


@app.get("/")
async def root():
    compute()
    return {"message": "hello"}
