Docker quickstart for Zeusonic backend

Build and run (from project root):

1) Build and start the service

   docker-compose up --build

   This will build the `backend` image and start the service on port 8000.

2) Visit Swagger UI:

   http://localhost:8000/docs

3) Persistence:

   - The SQLite DB is stored on the host at `./backend/storage/zeusonic.db` (mounted into the container).
   - Uploaded files are stored at `./backend/storage/audio_uploads` on the host.
   - Demo API key is stored in `./backend/.demo_api_key` (or the path configured by `API_KEY_PATH`).

5) Health checks / developer convenience:

   - Locally, run: `make health-local` (requires the app running locally on port 8000).
   - Against Docker, run: `make health-docker` (hits http://localhost:8000/api/v1/health).

6) Stopping and restarting

   docker-compose down
   docker-compose up --build

   The DB and uploaded files persist because of the volume mounts.

Notes

- For development you may want to inspect the demo API key in `./backend/.demo_api_key` after the first startup.
- The container runs uvicorn with: `uvicorn backend.main:app --host 0.0.0.0 --port 8000`.
