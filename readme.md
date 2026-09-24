# 📝 Smart English Writing Assistant (single-file version)

Grammar Error Correction · Grammar Q&A · Interactive Quiz Learning — all in
**one Python file** (`app.py`), no API keys required.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Push to GitHub

```bash
git init
git add .
git commit -m "Smart English Writing Assistant - single file"
git branch -M main
git remote add origin https://github.com/<your-username>/<repo-name>.git
git push -u origin main
```

## Deploy on Streamlit Community Cloud

1. Push this repo to GitHub (needs **`app.py`**, **`requirements.txt`**, and **`packages.txt`** — all three, in the repo root).
2. Go to share.streamlit.io → New app → pick the repo → set main file to `app.py` → Deploy.
3. No secrets/API keys needed. `packages.txt` tells Streamlit Cloud to `apt-get install` Java automatically during the build, so the grammar checker runs the local (unlimited, no-rate-limit) checker instead of relying on the free public API, which gets rate-limited quickly on shared cloud IPs.
4. The very first grammar check after deploying will take ~20-30 seconds (it downloads a small LanguageTool engine, ~200MB, one time). After that it's fast.
5. If you ever see a Java-related error on Cloud, go to your app's **Manage app → Reboot app**, which re-runs the `packages.txt` install step.

## No API keys, anywhere

- The **Grammar Checker** tab calls LanguageTool's free public endpoint (just needs internet, no signup/key). If that's unreachable it falls back to a local LanguageTool server, which needs Java but still no key.
- The **Grammar Q&A** tab is a self-contained rule-based knowledge base (keyword matching against curated grammar explanations) — fully offline, no external calls at all.
- The **Quiz** and **Learning Progress** tabs are pure Python/Streamlit logic.

## File structure

Three files matter:
- `app.py` — everything (knowledge base, quiz bank, grammar checker, UI)
- `requirements.txt` — the three Python dependencies
- `packages.txt` — tells Streamlit Cloud to install Java via apt (needed for the offline grammar checker; irrelevant if you only run this locally with Java already installed)

## Extending it

If later on you *do* want more open-ended AI answers (not required for this
project to work), you could add an LLM call as a fallback inside the
`answer_question()` function when nothing in the knowledge base matches —
but that's entirely optional and this app works fully without it.
