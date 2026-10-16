# FastAPI Config Precedence Service

## Run locally
```bash
pip install -r requirements.txt
APP_PORT=8655 APP_WORKERS=8 APP_DEBUG=true APP_LOG_LEVEL=info APP_API_KEY=key-o75x27cfg6 uvicorn main:app --host 0.0.0.0 --port 8655
```

Test:
`http://localhost:8655/effective-config?set=port=9000&set=debug=false`

Configuration precedence:
defaults -> config.<APP_ENV>.yaml -> .env -> OS APP_* variables -> repeated `set` query parameters.

Deploy this folder to a Python hosting provider that supports FastAPI. The final endpoint URL must be the actual deployed URL; a URL cannot be created from source code alone.
