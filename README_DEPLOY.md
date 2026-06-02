winget install --id Git.Git -e --source wingetwinget install --id Git.Git -e --source wingetchoco install git -y# commit + push (replace with your repo URL)
.\publish.ps1 -RemoteUrl "https://github.com/<your-username>/<repo>.git"

# or just commit locally
.\publish.ps1.\publish.ps1Quick deployment guide

1) Prepare local git repo and commit:

```bash
cd "c:\Users\user\Desktop\samue ade"
git init
git add .
git commit -m "Initial site for O'FAME Farm Feed"
```

2) Push to GitHub:

- Create a new repository on GitHub (web UI).
- Follow the instructions to add remote and push:

```bash
git remote add origin https://github.com/<your-username>/<repo>.git
git branch -M main
git push -u origin main
```

3) Deploy on Render (recommended):

- Create a free account on Render.com.
- Click "New" → "Web Service" → connect your GitHub repo.
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app`
- Choose the Python runtime matching `runtime.txt`.

Render will build and provide a public URL.

Alternative hosts: Railway, Fly.io, DigitalOcean App Platform, PythonAnywhere.

4) Local test using Gunicorn:

```bash
pip install -r requirements.txt
gunicorn --bind 127.0.0.1:8000 app:app
# Visit http://127.0.0.1:8000
```

Notes and security:
- Replace `app.secret_key` in `app.py` with a strong secret or use environment variable.
- Configure environment variables for production (db path, admin password, keys) in the host's dashboard.
- Consider adding HTTPS and a proper database for production.

Windows local publish and Render guidance

If you're on Windows you can use the included PowerShell helper to create a local commit and push to GitHub (requires Git installed). Save and run the script from the project root.

Usage (PowerShell):

```powershell
# create commit and push (provide your GitHub repo URL)
.\publish.ps1 -RemoteUrl "https://github.com/<your-username>/<repo>.git"

# or just create the local commit without pushing
.\publish.ps1
```

If Git is not installed, download it from https://git-scm.com/downloads and re-run the script.

Deploying on Render after pushing

- On Render, create a new Web Service and connect your GitHub repo.
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app`
- Add environment variables in Render's dashboard: `SECRET_KEY` (replace the default), and any DB credentials if used.
- Render will detect `runtime.txt` for Python version; confirm or override if needed.

Windows local run (no Gunicorn)

To run the app locally on Windows without Gunicorn, use the Waitress runner included in `run_server.py`:

```powershell
pip install -r requirements.txt
python run_server.py
# open http://127.0.0.1:8000
```

If you want me to perform the Git push and Render deploy for you, grant repository access or run the `publish.ps1` script locally and tell me when it's pushed.