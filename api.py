from fastapi import FastAPI
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import matplotlib.pyplot as plt
import io

from logger import Logger

logger = Logger("logs.jsonl")
app = FastAPI(title="Signal Service API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/log")
def log_interaction(data: dict):
    logger.write(**data)
    return {"status": "ok", "logged": data}

@app.get("/logs/{agent_id}/{user_id}")
def get_logs(agent_id: str, user_id: str):
    return logger.read_recent(agent_id, user_id)

@app.get("/summary/{agent_id}/{user_id}")
def get_summary(agent_id: str, user_id: str):
    return logger.summarize_signals(agent_id, user_id)

@app.get("/visualize/{agent_id}/{user_id}")
def visualize(agent_id: str, user_id: str):
    summary = logger.summarize_signals(agent_id, user_id)
    if not summary:
        return JSONResponse({"error": "No data to visualize"})

    fig, ax = plt.subplots()
    ax.bar(summary.keys(), summary.values(), color='skyblue')
    ax.set_title(f"Signal Summary for {agent_id}/{user_id}")
    ax.set_ylabel("Frequency")

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)

    return FileResponse(buf, media_type="image/png")
