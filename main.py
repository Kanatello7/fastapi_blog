from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import fastapi.responses
app = FastAPI()

posts: list[dict] = [
    {
        "id": 1,
        "name": "Kanat",
        "age": 20,
    },
    {
        "id": 2,
        "name": "Tom",
        "age": 29
    },
]

@app.get("/api/posts")
def get_dict() -> list[dict]:
    return posts

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
@app.get("/posts", response_class=HTMLResponse, include_in_schema=False)
def home() -> str:
    return f"<h1>{posts[0]["name"]}</h1>"