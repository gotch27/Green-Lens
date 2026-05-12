Green Lens - ИКТ

Строго забрането push на главна(main) гранка.
Прво направете push  на сопствена гранка. 
Откако ќе се валидираат промените ќе се стави на 
главната(main) гранка

## Backend Docker setup

The React frontend, Django backend, PostgreSQL database, ML service, and database UI can run through Docker Compose.

### 1. Configure environment

Create or update `backend/.env`:

```env
DJANGO_SECRET_KEY=change-me-in-local-env
DJANGO_DEBUG=1
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
LOG_LEVEL=DEBUG
ROOT_LOG_LEVEL=INFO

POSTGRES_DB=greenlens
POSTGRES_USER=greenlens
POSTGRES_PASSWORD=greenlens
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

ML_SERVICE_URL=http://localhost:8001
JWT_SIGNING_KEY=change-me-to-a-different-long-random-jwt-secret
ML_SERVICE_TIMEOUT_SECONDS=60
OPENWEATHERMAP_API_KEY=your_openweathermap_key
WEATHER_TIMEOUT_SECONDS=4
MAX_IMAGE_UPLOAD_SIZE=5242880
```

When running in Docker, Compose overrides these two values automatically:

```env
POSTGRES_HOST=db
ML_SERVICE_URL=http://ml-service:8001
```

So local Python can use `localhost`, while containers use service names on the Docker network.

For the ML service, add these to `backend/.env` before running Compose:

```env
OPENAI_API_KEY=your_openai_key
TAVILY_API_KEY=your_tavily_key
```

### 2. Start everything

```bash
docker compose up --build
```

The backend runs migrations automatically, then starts Django at:

```text
http://127.0.0.1:8000
```

The frontend runs at:

```text
http://127.0.0.1:5173
```

Inside Docker, the Vite dev server proxies `/api/*` to `http://backend:8000`. When running the frontend outside Docker with `npm run dev`, it proxies to `http://localhost:8000`.

Health check:

```bash
curl http://127.0.0.1:8000/api/health/
```

### 3. Database access

PostgreSQL is available from your host at:

```text
host: localhost
port: 5432
database: greenlens
user: greenlens
password: greenlens
```

Adminer database UI:

```text
http://127.0.0.1:8080
```

Adminer login:

```text
System: PostgreSQL
Server: db
Username: greenlens
Password: greenlens
Database: greenlens
```

### 4. ML service container

The backend already calls the AI service at:

```text
http://ml-service:8001/ml/analyze/
```

Compose now starts a service named `ml-service` from `./ml-service`, exposed on:

```text
http://127.0.0.1:8001
```

Docker DNS lets Django reach it at `http://ml-service:8001`.

### 5. Apidog/Postman checks

Create environment variables:

```text
baseUrl = http://127.0.0.1:8000
scanId = 1
```

Requests:

```text
GET {{baseUrl}}/api/health/
GET {{baseUrl}}/api/weather/?city=Skopje
GET {{baseUrl}}/api/scans/
GET {{baseUrl}}/api/scans/{{scanId}}/
POST {{baseUrl}}/api/scans/{{scanId}}/retry/
GET {{baseUrl}}/api/scans/{{scanId}}/report/
DELETE {{baseUrl}}/api/scans/{{scanId}}/
```

Upload scan:

```text
POST {{baseUrl}}/api/scans/
Body: form-data
image = File
city = Skopje
```

If the AI container is not running yet, upload/retry will return:

```json
{"error":"ML service unavailable."}
```
