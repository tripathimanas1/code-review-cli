# Code Review CLI

AI-powered code reviewer in your terminal. Four modes: general, security, explain, refactor.

Built with Gemini 2.0 Flash — works on any codebase.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Add your Gemini API key to .env
```

## Usage

### Review a file
```bash
python main.py file path/to/your_file.py
python main.py file app.py --mode security
python main.py file main.py --mode refactor --context "This is a FastAPI route handler"
```

### Review your latest git diff
```bash
python main.py diff
python main.py diff --mode security
python main.py diff --staged          # only staged changes
python main.py diff --base main       # diff against main branch
```

### Paste code directly
```bash
python main.py paste
python main.py paste --mode explain
```

### Watch a file (auto-review on every save)
```bash
python main.py watch app.py
python main.py watch main.py --mode security
```

## Review Modes

| Mode | What it does |
|------|-------------|
| `general` | Bugs, quality, performance, quick wins |
| `security` | Injection, auth, input validation, secrets, data exposure |
| `explain` | Plain English walkthrough of what code does |
| `refactor` | Concrete refactoring suggestions with rewritten code |

## Codebase Graph

Generate an interactive dependency graph for any Python project — visualizes files, connections, and structure in your browser.

```bash
# Graph current folder
python main.py graph .

# Graph any project (different drive is fine)
python main.py graph C:\Users\Manas\projects\fashionfusion

# Save to a custom file
python main.py graph . --output mygraph.html

# Generate without auto-opening browser
python main.py graph . --no-open
```

### What you see

- Every Python file as a node, sized by lines of code
- Orange nodes = hub files with many dependencies
- Purple nodes = regular modules
- Click any node to see its classes, functions, and connections
- Search files in the sidebar
- Scroll to zoom, drag to pan

### Works across drives

```bash
# Tool on D:, project on C: — no problem
python D:\code-review-cli\main.py graph C:\projects\fashionfusion
```
