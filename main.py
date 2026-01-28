import threading

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from starlette.responses import JSONResponse

from modules import dc, tool

app = FastAPI()


class QueryRequest(BaseModel):
    handle: str


@app.post("/query")
def query_handle(req: QueryRequest):
    res = tool.query_handle(req.handle)
    if res is None:
        raise HTTPException(status_code=404, detail="使用者名稱不存在")
    return res


templates = Jinja2Templates(directory="templates")


@app.get("/query", response_class=HTMLResponse)
def get_query_page(request: Request):
    return templates.TemplateResponse("query.html", {"request": request})


@app.get("/health_check")
async def health_check():
    return JSONResponse(content={"status": "ok"})


if __name__ == '__main__':
    threading.Thread(target=dc.main, daemon=True).start()
    uvicorn.run(app, host='0.0.0.0', port=8070)
