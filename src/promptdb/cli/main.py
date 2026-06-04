"""PromptDB CLI — the flagship interface. Subcommands are stubs until their phase lands."""

import typer
from rich.console import Console

app = typer.Typer(
    help="PromptDB — ask your database in English.",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()


@app.command()
def ask(question: str) -> None:
    """Ask a natural-language question about the database (P1)."""
    console.print(f"[yellow]Not implemented yet (P1).[/] You asked: {question!r}")


@app.command()
def schema() -> None:
    """Render an ER diagram of the database schema (P4.5)."""
    console.print("[yellow]Not implemented yet (P4.5 — schema graph).[/]")


@app.command()
def profile() -> None:
    """Profile the database: row counts, null rates, distributions (P4.5)."""
    console.print("[yellow]Not implemented yet (P4.5 — profiling).[/]")


@app.command()
def doctor() -> None:
    """Report read-only data-quality issues (P4.5)."""
    console.print("[yellow]Not implemented yet (P4.5 — data-quality).[/]")


if __name__ == "__main__":
    app()
