# Setup

Linux/macOS: create a Python 3.11 virtual environment, install `pip install -e ".[test]"`, validate with `python scripts/validate_environment.py`, seed with `python scripts/seed_demo.py`, and run `uvicorn services.api.main:app --reload`. Build the reviewer client with `cd frontend && npm install && npm run build`; copy `frontend/dist` behind the API or use Vite proxy for development. Windows PowerShell uses `.venv\Scripts\Activate.ps1` and the same Python commands.
