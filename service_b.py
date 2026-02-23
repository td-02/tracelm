from fastapi import FastAPI
from tracelm.integrations.fastapi import TraceLMMiddleware

app = FastAPI()
app.add_middleware(TraceLMMiddleware)


@app.get("/")
async def root():
    return {"service": "B"}
