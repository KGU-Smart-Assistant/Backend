# Backend
해당 프로젝트는 API키가 필요합니다.
보안을 위해 API키는 코드에 직접 작성하지 않고 환경변수인 .env로 관리합니다.
1.루트에 .env파일을 만듭니다.
2.별도의 API키를 받아서 해당 파일에 GOOGLE_API_KEY= 별도의 키 를 입력합니다.

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

```
.env 파일 만들고
```
```bash
uvicorn app.main:app --reload
```

## Docker Compose Full Stack

`Docker-compose.yml` now runs the backend, PostgreSQL, Chroma, and the Next.js frontend together.

1. Create `backend/.env` from `backend/.env.example`.
2. Fill required keys such as `GOOGLE_API_KEY`, `KAKAO_REST_API_KEY`, and `NEXT_PUBLIC_KAKAOMAP_KEY`.
3. Run from the `backend` directory:

```powershell
docker compose -f Docker-compose.yml up --build
```

Frontend: http://localhost:3000
Backend API: http://localhost:8000
