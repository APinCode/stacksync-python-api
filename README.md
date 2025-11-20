# Python Sandbox Execution API

A simple API that safely executes user-provided Python scripts using **Flask**, **nsjail**, and **Docker**.  
Users POST a script containing a `main()` function, and the API returns:

- the JSON value returned by `main()`
- any printed stdout output from the script

---

## Local Usage (Docker)

### Build
```bash
docker build -t python-sandbox-api .
```

### Run
```bash
docker run --rm -p 8080:8080 python-sandbox-api
```

### Health check

```bash
curl http://localhost:8080/status
```

## Examples 

### Request

```bash
curl -X POST "http://localhost:8080/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "script": "def main():\n    print(\"Hello\")\n    return {\"ok\": true}"
  }'
```
### Response

```json
{
  "result": {"ok": true},
  "stdout": "Hello"
}
```

## Deployment on Google Cloud Run

### Build
```bash
gcloud builds submit --tag gcr.io/sandbox-stacksync/python-sandbox-api . 
```

### Deploy
```bash
gcloud run deploy python-sandbox-api \
  --image gcr.io/sandbox-stacksync/python-sandbox-api \
  --platform managed \
  --region europe-west1 \
  --allow-unauthenticated \
  --port 8080   
```

### Example (Cloud Run)
```bash
curl -X POST "https://python-sandbox-api-255832082464.europe-west1.run.app/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "script": "def main():\n    print(\"Hello\")\n    return {\"ok\": true}"
  }'
```

## Notes

- Scripts run inside nsjail using a dedicated wrapper (executor.py).
- The jail enforces:
  - Isolated working directory (/sandbox)
  - 5-second CPU time limit
  - Clean environment
- To support nsjail on Google Cloud Run we use:
  - Non-root execution (USER appuser)
  - No new namespaces (Due Cloud Run blocking them)
  - rlimits disabled via disable_rl: true (Cloud Run restricts RLIMIT_RTPRIO, so nsjail needs to inherit the parent's limits)

## Time Spent

Approximately 3 hours
