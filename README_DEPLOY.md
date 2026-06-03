# O'FAME Farm Feed Deployment Guide

## 1) Commit your code locally

From the project root in PowerShell:

```powershell
cd "c:\Users\user\Desktop\samue ade"
.\publish.ps1
```

This will:
- initialize Git if needed
- add all files
- create a commit with message `oca commigit remote remove origin
git remote add origin "https://github.com/stinger407/samue-ade.git"xt`

If the script fails because of PowerShell policy, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\publish.ps1
```

## 2) Push to GitHub

Create a new repository on GitHub and then run:

```powershell
.\publish.ps1 -RemoteUrl "https://github.com/<your-username>/<repo>.git"
```

Replace `<your-username>` and `<repo>` with your GitHub account and repository name.

If you prefer to use Git commands directly instead of the script:

```powershell
git init

git add -A

git commit -m "oca commit"

git remote add origin https://github.com/<your-username>/<repo>.git
git branch -M main
git push -u origin main
```

## 3) Deploy on Render (recommended)

- Create a free account on Render.com.
- Click **New** → **Web Service**.
- Connect your GitHub repo.
- Build command:
  ```bash
  pip install -r requirements.txt
  ```
- Start command:
  ```bash
  gunicorn app:app
  ```
- Confirm Python runtime from `runtime.txt`.
- Add environment variables in Render:
  - `SECRET_KEY`
  - any other production settings you need.

Render will build and publish your site with a public URL.

## 4) Run locally on Windows without Gunicorn

If you want to test locally on Windows, use the included Waitress runner:

```powershell
pip install -r requirements.txt
python run_server.py
# Open http://127.0.0.1:8000
```

## 5) Local test with Flask (optional)

```powershell
$env:FLASK_APP = "app.py"
$env:FLASK_ENV = "development"
flask run --host=127.0.0.1 --port=8000
```

## Notes

- Make sure `app.py` uses a strong `SECRET_KEY` in production, ideally from an environment variable.
- If you need help creating the GitHub repo or deploying to Render, I can walk you through each step.
