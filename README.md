# NTInet LNP Portal

Initial FastAPI Bandwidth LNP portal.

## Windows setup

```powershell
cd C:\Users\chair\Documents
Expand-Archive .\lnp-portal.zip -DestinationPath .\lnp-portal
cd .\lnp-portal
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000

Included: dashboard, sub-accounts, locations, number inventory, available-number search, CSR list/create, port list/create/detail/cancel.
