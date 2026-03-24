# Backend

## FastAPI Structure

```text
app/
  api/
    v1/
      endpoints/
      router.py
    deps.py
  core/
    config.py
  db/
    base.py
  models/
  schemas/
  services/
  utils/
  main.py
tests/
  test_health.py
```

## Run

```bash
uvicorn app.main:app --reload
```
