from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.api_server import router

app = FastAPI()


app.include_router(router)