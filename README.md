# AI-Powered Travel Guide — Full Vercel Deployment

This version is configured to deploy the frontend and Flask backend in **one Vercel project**. You do not need Render.

## Project structure

```text
AI_Travel_Guide_Vercel/
├── app.py                 # Flask API + local homepage route
├── requirements.txt       # Python dependencies installed by Vercel
├── vercel.json            # Function duration configuration
├── .python-version        # Python runtime version
├── .env.example           # Example only; never put real keys here in Git
└── public/
    ├── index.html         # Frontend
    └── index.js           # Frontend JavaScript; API uses same-domain path
```

## Deploy everything to Vercel

1. Extract this ZIP and put the contents in the root of a GitHub repository. `app.py`, `requirements.txt`, `vercel.json`, and `public/` must be at the repository root (not inside another nested project folder).
2. Make sure you do **not** commit a real `.env` file or API keys.
3. Open https://vercel.com/new and import the GitHub repository.
4. Keep the Root Directory at `.` (repository root). Vercel should detect the Python/Flask app. Do not set a separate frontend project or a Render service.
5. In Vercel → Project → Settings → Environment Variables, add:
   - `GEMINI_API_KEY` — your Google AI Studio API key
   - `MURF_API_KEY` — your Murf API key
   - `GEMINI_MODEL` — `gemini-3.8-flash` (if this model is enabled for your API account; otherwise use a model ID supported by your account)
6. Add the variables to Production (and Preview/Development if needed), save, then redeploy so the deployment receives them.
7. Open the Vercel deployment URL. Check `/health` first; it should return `{"status":"ok"}`. Then generate an audio guide from the homepage.

## Local testing on Windows

1. Create a local `.env` from `.env.example` and fill in your real keys. Keep `.env` private.
2. In PowerShell, from this project root:

   ```powershell
   py -3.12 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   python app.py
   ```

3. Open http://127.0.0.1:5000. The frontend calls `/generate-audio-guide` on the same host, so no URL edit is needed between local and deployed environments.

## Important notes

- Both the frontend and backend use the same Vercel domain. The JavaScript calls `/generate-audio-guide`, not `localhost`.
- API keys belong only in Vercel Environment Variables or your ignored local `.env`, never in `public/index.js`.
- The backend makes two external requests (Gemini then Murf). Vercel function duration is configured to 300 seconds, but the account plan and current Vercel limits still apply. If audio generation exceeds the available duration, reduce latency or use a hosting setup designed for longer-running jobs.
- `GEMINI_MODEL=gemini-3.8-flash` reflects the model ID mentioned in the prior error response. Confirm the ID is available to your Google AI API account; model availability can differ.
- The configured Murf voice IDs must be valid for your Murf account and the selected language. If Murf rejects one, replace it with a supported voice ID.
- The Flask development server is for local testing only. Vercel runs the Flask app as a serverless function.
