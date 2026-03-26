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

```bash
uvicorn app.main:app --reload
```
