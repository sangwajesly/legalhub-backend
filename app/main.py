from fastapi import FastAPI
from app.api.routes import chat

app = FastAPI()

app.include_router(chat.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to LegalHub Backend"}