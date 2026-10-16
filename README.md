# Chemo Companion — Starter Prototype

A beginner-friendly Python + Streamlit prototype for the Team Chemo Shield hackathon.

## Features included
- Symptom entry (date, symptom, severity, impact, optional notes)
- Persistent local SQLite storage
- Symptom history and basic severity chart
- Filter history by symptom
- Delete an entry
- Downloadable CSV and readable appointment summary
- Safety information and explicit prototype disclaimer

## Important limitations
- This is a hackathon demonstration, not a medical device or clinical service.
- Use fictional data only for demos.
- The database is local to the computer running the app.
- There is no login, cloud backup, secure multi-user storage, clinical alert validation, or hospital integration.
- Do not use the displayed severity scale to decide whether a symptom is safe or dangerous.
- The app is not continuously monitored and does not provide emergency alerts.

## Run on Windows
1. Install Python 3.10 or newer and Visual Studio Code.
2. Extract this ZIP to a folder.
3. Open the extracted folder in VS Code.
4. In VS Code, choose Terminal -> New Terminal.
5. Run:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

If `py` is not recognized, try `python` instead.

6. Open the local URL shown in the terminal (usually http://localhost:8501).

## Data storage
The app creates `chemo_companion.db` in the working directory the first time it runs. Keep this file private and do not upload real patient information to public repositories.
