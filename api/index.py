from fastapi import FastAPI

from pydantic import BaseModel



from fastapi import FastAPI, Request, Response

app = FastAPI()

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "*",
    "Access-Control-Max-Age": "86400",
}

@app.get("/")
@app.get("/api")
def health():
    return {"status": "ok"}


@app.post("/")
@app.post("/api")
def calculate_metrics(data: RequestData):
    ...  # your existing body unchanged

@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    if request.method == "OPTIONS":
        return Response(status_code=200, headers=CORS_HEADERS)
    response = await call_next(request)
    for k, v in CORS_HEADERS.items():
        response.headers[k] = v
    return response

# Telemetry data from q-vercel-latency.json
DATA = [
    # APAC
    {"region": "apac", "latency_ms": 142.59, "uptime_pct": 98.934},
    {"region": "apac", "latency_ms": 179.8, "uptime_pct": 97.893},
    {"region": "apac", "latency_ms": 215.91, "uptime_pct": 98.397},
    {"region": "apac", "latency_ms": 178.63, "uptime_pct": 97.461},
    {"region": "apac", "latency_ms": 186.08, "uptime_pct": 99.115},
    {"region": "apac", "latency_ms": 114.68, "uptime_pct": 97.719},
    {"region": "apac", "latency_ms": 149.14, "uptime_pct": 97.863},
    {"region": "apac", "latency_ms": 223.36, "uptime_pct": 99.413},
    {"region": "apac", "latency_ms": 187.98, "uptime_pct": 99.426},
    {"region": "apac", "latency_ms": 151.99, "uptime_pct": 97.375},
    {"region": "apac", "latency_ms": 146.62, "uptime_pct": 98.366},
    {"region": "apac", "latency_ms": 137.77, "uptime_pct": 97.49},

    # EMEA
    {"region": "emea", "latency_ms": 177.32, "uptime_pct": 98.696},
    {"region": "emea", "latency_ms": 142.29, "uptime_pct": 99.399},
    {"region": "emea", "latency_ms": 235.55, "uptime_pct": 97.494},
    {"region": "emea", "latency_ms": 190.78, "uptime_pct": 98.012},
    {"region": "emea", "latency_ms": 132.73, "uptime_pct": 98.522},
    {"region": "emea", "latency_ms": 135.03, "uptime_pct": 99.213},
    {"region": "emea", "latency_ms": 178.03, "uptime_pct": 98.607},
    {"region": "emea", "latency_ms": 149.1, "uptime_pct": 98.283},
    {"region": "emea", "latency_ms": 177.06, "uptime_pct": 97.273},
    {"region": "emea", "latency_ms": 177.71, "uptime_pct": 97.61},
    {"region": "emea", "latency_ms": 227.23, "uptime_pct": 97.471},
    {"region": "emea", "latency_ms": 202.31, "uptime_pct": 97.362},

    # AMER
    {"region": "amer", "latency_ms": 166.87, "uptime_pct": 99.01},
    {"region": "amer", "latency_ms": 169.75, "uptime_pct": 99.161},
    {"region": "amer", "latency_ms": 194.33, "uptime_pct": 98.437},
    {"region": "amer", "latency_ms": 220.06, "uptime_pct": 98.786},
    {"region": "amer", "latency_ms": 166.01, "uptime_pct": 97.652},
    {"region": "amer", "latency_ms": 134.92, "uptime_pct": 98.653},
    {"region": "amer", "latency_ms": 141.25, "uptime_pct": 98.013},
    {"region": "amer", "latency_ms": 129.35, "uptime_pct": 97.808},
    {"region": "amer", "latency_ms": 218.22, "uptime_pct": 97.447},
    {"region": "amer", "latency_ms": 228.51, "uptime_pct": 97.855},
    {"region": "amer", "latency_ms": 153.25, "uptime_pct": 99.485},
    {"region": "amer", "latency_ms": 206.54, "uptime_pct": 99.034},
]


class RequestData(BaseModel):
    regions: list[str]
    threshold_ms: float


def percentile(values, percentile):
    """
    Calculate percentile using linear interpolation.
    Equivalent to NumPy's default percentile method.
    """

    values = sorted(values)

    if len(values) == 1:
        return values[0]

    position = (len(values) - 1) * percentile

    lower = int(position)
    upper = lower + 1

    if upper >= len(values):
        return values[lower]

    fraction = position - lower

    return (
        values[lower]
        + (values[upper] - values[lower]) * fraction
    )


@app.post("/")
def calculate_metrics(data: RequestData):

    results = {}

    for region in data.regions:

        rows = [
            row
            for row in DATA
            if row["region"] == region
        ]

        # If the requested region doesn't exist
        if not rows:
            results[region] = {
                "avg_latency": None,
                "p95_latency": None,
                "avg_uptime": None,
                "breaches": 0,
            }
            continue

        latencies = [
            row["latency_ms"]
            for row in rows
        ]

        uptimes = [
            row["uptime_pct"]
            for row in rows
        ]

        avg_latency = sum(latencies) / len(latencies)

        p95_latency = percentile(
            latencies,
            0.95
        )

        avg_uptime = sum(uptimes) / len(uptimes)

        breaches = sum(
            latency > data.threshold_ms
            for latency in latencies
        )

        results[region] = {
            "avg_latency": avg_latency,
            "p95_latency": p95_latency,
            "avg_uptime": avg_uptime,
            "breaches": breaches,
        }

    return results