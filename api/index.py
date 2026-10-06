from fastapi import FastAPI, Request, Response
from pydantic import BaseModel

app = FastAPI()

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "*",
    "Access-Control-Max-Age": "86400",
}


@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    if request.method == "OPTIONS":
        return Response(status_code=200, headers=CORS_HEADERS)
    response = await call_next(request)
    for k, v in CORS_HEADERS.items():
        response.headers[k] = v
    return response


# ---- PASTE YOUR EXISTING DATA = [ ... ] LIST HERE ----
DATA = [
    # (apac, emea, amer rows exactly as before)
]


class RequestData(BaseModel):
    regions: list[str]
    threshold_ms: float


def percentile(values, p):
    values = sorted(values)
    if len(values) == 1:
        return values[0]
    position = (len(values) - 1) * p
    lower = int(position)
    upper = lower + 1
    if upper >= len(values):
        return values[lower]
    fraction = position - lower
    return values[lower] + (values[upper] - values[lower]) * fraction


@app.get("/")
@app.get("/api")
def health():
    return {"status": "ok"}


@app.post("/")
@app.post("/api")
def calculate_metrics(data: RequestData):
    results = {}
    for region in data.regions:
        rows = [row for row in DATA if row["region"] == region]

        if not rows:
            results[region] = {
                "avg_latency": None,
                "p95_latency": None,
                "avg_uptime": None,
                "breaches": 0,
            }
            continue

        latencies = [row["latency_ms"] for row in rows]
        uptimes = [row["uptime_pct"] for row in rows]

        results[region] = {
            "avg_latency": sum(latencies) / len(latencies),
            "p95_latency": percentile(latencies, 0.95),
            "avg_uptime": sum(uptimes) / len(uptimes),
            "breaches": sum(l > data.threshold_ms for l in latencies),
        }

    return results