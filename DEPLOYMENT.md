# Current deployment: Vercel frontend + Railway backend

The backend is `https://hackerthone-production.up.railway.app`.
The repository's `vercel.json` routes `/api/:path*` to that backend, preserving
same-origin browser requests and login cookies. The Vite development proxy only
runs locally; it cannot route requests on a deployed static site.

## Apply this fix

1. Commit and push `vercel.json` and `vite.config.js` to the branch Vercel deploys.
2. In Vercel, use the repository root as **Root Directory** (leave it blank),
   **Build Command** `npm run build`, and **Output Directory** `frontend/dist`.
3. Redeploy that branch and open the new deployment or the production domain.
   Previously generated deployment URLs still refer to their original builds.

Vercel builds force the frontend API base to `/api`, so a stale `VITE_API_URL`
setting cannot bypass the proxy. Other hosting providers still use `VITE_API_URL`.
All three clients (accounts, inventory, speech) use the same build-time setting.

## Verify

- Open `https://YOUR-VERCEL-DOMAIN/api/auth/me` before signing in. It should return
  JSON `{"detail":"Please sign in."}` with status 401, not HTML or a 404.
- Sign up or sign in, reload, and confirm the greeting still shows your name.
- Check inventory and selected-language speech playback.

A browser's red "Dangerous" warning is separate from API routing; review the
site's security classification with the browser provider if it remains.

## Account persistence on Railway

Accounts and sessions currently use SQLite at `backend/stockstory.db`. Keep that
file on persistent storage when deploying Railway; MongoDB inventory settings
do not move accounts into MongoDB. Do not replace an existing account database
with a new empty one when configuring persistence.

---

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
