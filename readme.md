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

1. Push this repo to GitHub (public or private).
2. Go to share.streamlit.io → New app → pick the repo → set main file to `app.py` → Deploy.
3. No secrets/API keys needed for the default setup.

## No API keys, anywhere

- The **Grammar Checker** tab calls LanguageTool's free public endpoint (just needs internet, no signup/key). If that's unreachable it falls back to a local LanguageTool server, which needs Java but still no key.
- The **Grammar Q&A** tab is a self-contained rule-based knowledge base (keyword matching against curated grammar explanations) — fully offline, no external calls at all.
- The **Quiz** and **Learning Progress** tabs are pure Python/Streamlit logic.

## File structure

Just two files matter:
- `app.py` — everything (knowledge base, quiz bank, grammar checker, UI)
- `requirements.txt` — the three dependencies

## Extending it

If later on you *do* want more open-ended AI answers (not required for this
project to work), you could add an LLM call as a fallback inside the
`answer_question()` function when nothing in the knowledge base matches —
but that's entirely optional and this app works fully without it.
