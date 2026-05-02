# LOL Team Builder Monorepo

This repository now contains both the client app and the FastAPI server.

## Structure

- `main.py`
  Client app entrypoint
- `server/main.py`
  Server app entrypoint
- `tools/riot_loader.py`
  Operator tool for loading Riot match data

## Run

### Client

```bash
python main.py
```

### Client operator tool

```bash
python -m tools.riot_loader
```

### Server

```bash
python -m uvicorn server.main:app --reload
```
