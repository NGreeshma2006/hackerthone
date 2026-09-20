# Deploy StockStory AI on Render

This project is deployed as two Render services:

1. A FastAPI web service for the API.
2. A static site for the Vite/React frontend.

Do not commit `.env`. Add the MongoDB values only in Render's environment-variable screen.

## 1. Push the project to GitHub

Create a private GitHub repository and push this project. Confirm that `.env` is not included before pushing.

## 2. Deploy the backend

In Render, select **New > Web Service** and connect the GitHub repository.

| Setting | Value |
| --- | --- |
| Language | Python 3 |
| Root directory | Leave blank |
| Build command | `pip install -r requirements.txt` |
| Start command | `uvicorn backend.main:app --host 0.0.0.0 --port $PORT` |
| Health check path | `/docs` |

Under **Environment Variables**, add:

| Key | Value |
| --- | --- |
| `MONGO_URI` | Your complete MongoDB Atlas connection string |
| `MONGO_DB_NAME` | `stockstory` |

Deploy it and copy the API URL Render gives you, such as `https://stockstory-api.onrender.com`.

Open `https://YOUR-API-URL/db-status` after deployment. It must report `"database": "mongodb"` before continuing.

## 3. Deploy the frontend

In Render, select **New > Static Site** and connect the same repository.

| Setting | Value |
| --- | --- |
| Root directory | Leave blank |
| Build command | `npm ci && npm run build` |
| Publish directory | `frontend/dist` |

Add this build-time environment variable:

| Key | Value |
| --- | --- |
| `VITE_API_URL` | The API URL from step 2, without a trailing slash |

Deploy the static site. It will call the deployed API rather than the local `/api` proxy.

## 4. MongoDB Atlas network access

In Atlas, go to **Network Access** and allow Render to connect. For a demo, `0.0.0.0/0` permits access from all IP addresses; use a dedicated database user with a strong password and minimum required permissions. Rotate any password that has been shared outside Atlas.

## Verification

- Open the frontend URL and confirm inventory appears.
- Open `https://YOUR-API-URL/docs` to confirm the API is live.
- Open `https://YOUR-API-URL/db-status` and verify MongoDB is active.
