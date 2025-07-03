from fastapi import FastAPI, Request
from subprocess import run
import os

app = FastAPI()

@app.post("/download")
async def download_etf(request: Request):
    data = await request.json()
    symbols = data.get("symbols", [])
    results = []

    for symbol in symbols:
        cmd = ["python3", "holdings_dl.py", "--symbol", symbol]
        result = run(cmd, capture_output=True, text=True)
        results.append({
            "symbol": symbol,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        })

    return {"results": results}
