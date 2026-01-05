# focus-tools
This tool was designed for people who want to avoid distractions (like myself). You post the tasks and reminders on it, forcing yourself to complete them, and you see a green marker indicating completion, which translates into a sense of accomplishment.

## Introduction
`focus-tools` is a lightweight tool for tracking tasks and reminders to help you stay focused. The core idea is simple:

- **Post tasks/reminders**
- **Force yourself to complete them**
- **Get a clear completion indicator (green marker)**

## How to Run (Server)
Below is a simple workflow for running it on a Linux server.

### 1) Activate your virtual environment
If you already have a `venv` created:

```bash
source venv/bin/activate
```

### 2) Use `tmux` to keep it running
Create a new session:

```bash
tmux new -s api
```

### 3) Start the Python service
Run your API/service inside the `tmux` session. Common examples:

```bash
# Example A: plain Python
python app.py

# Example B: FastAPI (uvicorn)
uvicorn main:app --host 0.0.0.0 --port 8000
```

Replace the command above with the actual entrypoint of this project.

Attach to the session (e.g. after reconnecting SSH):

```bash
tmux attach -t api
```

Kill the session:

```bash
tmux kill-session -t api
```
