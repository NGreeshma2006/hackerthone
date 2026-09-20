# StockStory AI

StockStory AI is a multilingual voice-first inventory assistant for small businesses in India. The prototype includes a FastAPI backend with SQLite persistence and a Vite + React frontend with a mobile-friendly interface.

## Features

- Multilingual UI and voice processing for English, Hindi, Telugu, Tamil, Kannada, Malayalam, Marathi, and Bengali
- Language-independent product IDs and cross-language aliases
- Voice + typed input through a shared NLP pipeline
- Inventory lifecycle tracking: purchase, sale, damage, return, credit, free sample, and adjustment
- StockStory explanations from real transaction history
- Reconciliation flow with confirmation before adjustment
- Alerts and insights generated from live inventory data
- Product-specific unit conversion support and shop vocabulary

## Local setup

### 1. Backend

```bash
cd c:\Users\DELL\Downloads\hackerthone
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Then open http://localhost:8000/docs

### 2. Frontend

```bash
cd c:\Users\DELL\Downloads\hackerthone
npm install
npm run dev
```

Then open the local Vite URL (usually http://localhost:5173)

## Demo flow

- Select Hindi and say: "आज 20 बोरी चावल आया।"
- Switch to English and say: "5 bags of rice were sold."
- Switch to Tamil and say a damaged stock phrase
- Ask: "Rice stock entha undi?"
- Ask: "Where did my rice stock go?"

## Default sample data

The app seeds products for Rice, Oil, Sugar, Dal, and Wheat with realistic transactions.

## Notes

- The backend stores data in SQLite at `backend/stockstory.db`
- The frontend persists language choice in localStorage
- Speech recognition uses the browser's Web Speech API when supported

## BoliStock interface

The frontend uses the layout and styling from `bolistock-inventory.zip` with live inventory data. Start the Python backend on port 8000 and run `npm run dev`; open the URL Vite prints. Both development and preview proxy `/api` to the backend. For other deployments, set `VITE_API_URL` to the backend URL before building.

Quick add records purchases, sales, damage and returns. Item catalog creates products. Product cards open their stock history. Reports and Share today's view download CSV inventory snapshots. Settings and voice-language preferences are saved in this browser. Voice entry requires a browser with speech recognition and microphone permission; typed entry remains available.

Verification:

```powershell
npm run build
.venv\Scripts\python.exe -m unittest discover -s tests -p test_inventory.py
npx playwright test tests/dashboard.spec.js --workers=1 --timeout=90000
```

The browser test uses headless Microsoft Edge and mocked inventory responses, so it does not alter shop data. Set `BOLI_TEST_URL` if the development server is not on port 5174. Backend tests use an isolated in-memory database.

### Voice commands and playback

Choose a language in the top bar, then tap the microphone. Voice prompts, inventory replies, and playback use that language. Tap the small speaker beside the response to replay it. The browser needs microphone permission and a speech-recognition service; playback uses a matching device voice when available and otherwise fetches online audio from `/voice/speak` using [edge-tts](https://github.com/rany2/edge-tts). Online playback supports all eight selectable languages without installing Windows voices and requires internet access from the backend. Response text is sent to Microsoft's online speech service for synthesis. A typed fallback is offered when recognition is unavailable.

Supported inventory commands include receiving stock, sales, customer returns, damage, credit, remaining stock, and reorder questions. Examples: `Add 3 kg of rice`, `तीन किलो चावल जोड़ो`, `మూడు కిలోల బియ్యం జోడించు`, `அரிசி எவ்வளவு உள்ளது?`. Say one movement at a time. An explicit receipt with a product name, quantity and unit can create a new catalog item automatically, for example `Add 10 packets of biscuits`. Repeating that name updates the same item. Missing units use that item's configured unit; bags and kilograms need a configured conversion. Unknown, ambiguous, negated, and incomplete requests do not change stock. This is a vocabulary-based inventory assistant, not a general-purpose conversational model.

Additional verification:

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -p 'test_*.py'
npx playwright test tests/voice.spec.js --workers=1 --timeout=90000
```

Browser tests simulate recognition and synthesis to verify language routing, final-result handling, cancellation, playback, permission errors, and typed fallback. Physical microphone capture still depends on the user's browser, microphone permission, and recognition service. Online playback removes the installed-voice requirement. Start both servers; inventory commands and online playback need the backend on port 8000.

### Accounts and personalized greetings

Choose **Sign up** on the login screen, enter your full name and email, and set and confirm a password of at least eight characters. Creating an account signs you in. Returning users sign in with the same email and password; the dashboard greeting and profile show the saved full name. **Sign out** lets another user sign in.

Accounts are stored in the backend SQLite database, with salted PBKDF2 password hashes. Browser sessions use expiring, revocable HttpOnly cookies and are checked with `/auth/me` on reload. The previous prototype localStorage profiles are discarded; create an account once to use the new flow. Run the frontend and backend together via the Vite `/api` proxy. Accounts currently access this installation's shared shop inventory; this change does not add separate inventories per account or authorization to the existing inventory endpoints.

Account verification: `.venv\Scripts\python.exe -m unittest discover -s tests -p test_auth.py` and `npx playwright test tests/auth.spec.js --workers=1`.
