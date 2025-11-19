# Python Sandbox Execution API

A simple API that safely executes user-provided Python scripts using **Flask**, **nsjail**, and **Docker**.  
Users POST a script containing a `main()` function, and the API returns:

- the JSON value returned by `main()`
- any printed stdout output from the script

---

## Locally (Docker)

Build:
```bash
docker build -t python-sandbox-api .
```

Run
```bash
docker run --rm -p 8080:8080 python-sandbox-api
```

## Health check

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

## Cloud Run

Build:
```bash
gcloud builds submit --tag gcr.io/sandbox-stacksync/python-sandbox-api . 
```

Deploy:
```bash
gcloud run deploy python-sandbox-api \
  --image gcr.io/sandbox-stacksync/python-sandbox-api \
  --platform managed \
  --region europe-west1 \
  --allow-unauthenticated \
  --port 8080   
```

### Example Cloud
```bash
curl -X POST "https://python-sandbox-api-255832082464.europe-west1.run.app/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "script": "def main():\n    print(\"Hello\")\n    return {\"ok\": true}"
  }'
```

## Notes

- User code is executed inside nsjail with a CPU time limit and restricted filesystem.
- Due to Docker environment constraints, some advanced namespace isolation is limited.
- For stronger isolation, run the container with ```--read-only``` or ```--network=none```.
- On Cloud Run the kernel restricts some nsjail features. If nsjail fails with a specific PR_SET_SECUREBITS error, the service falls back to running the wrapper directly inside the container sandbox so the API still works.

## Time Spent

Approximatively 3 hours
