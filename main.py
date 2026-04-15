import subprocess
import sys
import webbrowser
import typer
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich import print as rprint

from reviewer import review, review_diff, MODES
from grapher import build_graph
from visualizer import generate_html

app = typer.Typer(help="AI Code Reviewer — powered by Gemini")
console = Console()


def get_mode_choice() -> str:
    console.print("\n[bold]Review mode:[/bold]")
    for key, val in MODES.items():
        console.print(f"  [cyan]{key}[/cyan] — {val['label']}")
    choice = Prompt.ask("\nPick mode", choices=list(MODES.keys()), default="general")
    return choice


def display_review(result: str, mode: str):
    label = MODES[mode]["label"]
    console.print(Panel(Markdown(result), title=f"[bold green]{label}[/bold green]", border_style="green"))


@app.command("file")
def review_file(
    path: str = typer.Argument(..., help="Path to the file to review"),
    mode: str = typer.Option(None, "--mode", "-m", help="Review mode: general, security, explain, refactor"),
    context: str = typer.Option("", "--context", "-c", help="Extra context about this code"),
):
    """Review a specific file."""
    file_path = Path(path)
    if not file_path.exists():
        console.print(f"[red]File not found:[/red] {path}")
        raise typer.Exit(1)

    code = file_path.read_text(encoding="utf-8")

    if not mode:
        mode = get_mode_choice()

    console.print(f"\n[yellow]Reviewing {file_path.name} in [bold]{mode}[/bold] mode...[/yellow]")
    result = review(code, mode=mode, context=context)
    display_review(result, mode)


@app.command("diff")
def review_git_diff(
    base: str = typer.Option("HEAD", "--base", "-b", help="Base branch/commit to diff against"),
    mode: str = typer.Option("security", "--mode", "-m", help="Review mode"),
    staged: bool = typer.Option(False, "--staged", help="Review only staged changes"),
):
    """Review your latest git diff."""
    try:
        if staged:
            cmd = ["git", "diff", "--cached"]
        else:
            cmd = ["git", "diff", base]

        diff = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode("utf-8")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Git error:[/red] {e.output.decode()}")
        raise typer.Exit(1)

    if not diff.strip():
        console.print("[yellow]No changes detected in diff.[/yellow]")
        raise typer.Exit()

    lines = diff.count("\n")
    console.print(f"\n[yellow]Reviewing git diff ({lines} lines) in [bold]{mode}[/bold] mode...[/yellow]")

    result = review_diff(diff[:6000], mode=mode)
    display_review(result, mode)


@app.command("paste")
def review_paste(
    mode: str = typer.Option(None, "--mode", "-m", help="Review mode"),
    context: str = typer.Option("", "--context", "-c", help="Extra context about this code"),
):
    """Paste code directly into the terminal for review."""
    console.print("[yellow]Paste your code below. Press [bold]Ctrl+D[/bold] (Linux/Mac) or [bold]Ctrl+Z[/bold] (Windows) when done:[/yellow]\n")

    try:
        code = sys.stdin.read()
    except KeyboardInterrupt:
        raise typer.Exit()

    if not code.strip():
        console.print("[red]No code provided.[/red]")
        raise typer.Exit(1)

    if not mode:
        mode = get_mode_choice()

    console.print(f"\n[yellow]Reviewing pasted code in [bold]{mode}[/bold] mode...[/yellow]")
    result = review(code, mode=mode, context=context)
    display_review(result, mode)


@app.command("watch")
def watch_file(
    path: str = typer.Argument(..., help="File to watch and auto-review on save"),
    mode: str = typer.Option("general", "--mode", "-m", help="Review mode"),
):
    """Watch a file and auto-review every time it changes."""
    import time
    import hashlib

    file_path = Path(path)
    if not file_path.exists():
        console.print(f"[red]File not found:[/red] {path}")
        raise typer.Exit(1)

    console.print(f"[cyan]Watching [bold]{path}[/bold] for changes. Press Ctrl+C to stop.[/cyan]")

    def file_hash(p: Path) -> str:
        return hashlib.md5(p.read_bytes()).hexdigest()

    last_hash = file_hash(file_path)

    try:
        while True:
            time.sleep(2)
            current_hash = file_hash(file_path)
            if current_hash != last_hash:
                last_hash = current_hash
                console.print(f"\n[yellow]Change detected — reviewing...[/yellow]")
                code = file_path.read_text(encoding="utf-8")
                result = review(code, mode=mode)
                display_review(result, mode)
    except KeyboardInterrupt:
        console.print("\n[cyan]Stopped watching.[/cyan]")


@app.command("graph")
def graph_codebase(
    path: str = typer.Argument(".", help="Root directory of your codebase"),
    output: str = typer.Option("codebase_graph.html", "--output", "-o", help="Output HTML file path"),
    no_open: bool = typer.Option(False, "--no-open", help="Don't auto-open in browser"),
):
    """Generate an interactive dependency graph for a Python codebase."""
    root = Path(path).resolve()
    if not root.exists():
        console.print(f"[red]Path not found:[/red] {path}")
        raise typer.Exit(1)

    console.print(f"\n[yellow]Scanning codebase at [bold]{root}[/bold]...[/yellow]")

    graph_data = build_graph(str(root))

    if graph_data["total_files"] == 0:
        console.print("[red]No Python files found.[/red]")
        raise typer.Exit(1)

    console.print(f"[green]Found {graph_data['total_files']} files, {len(graph_data['edges'])} internal dependencies[/green]")
    console.print(f"[yellow]Generating graph...[/yellow]")

    out_path = generate_html(graph_data, output)

    console.print(Panel(
        f"[bold green]Graph saved to:[/bold green] {out_path}\n\n"
        f"[cyan]Files:[/cyan] {graph_data['total_files']}   "
        f"[cyan]Lines:[/cyan] {graph_data['total_loc']:,}   "
        f"[cyan]Edges:[/cyan] {len(graph_data['edges'])}",
        title="Codebase Graph"
    ))

    if not no_open:
        console.print("[yellow]Opening in browser...[/yellow]")
        webbrowser.open(f"file://{Path(out_path).resolve()}")


if __name__ == "__main__":
    app()
