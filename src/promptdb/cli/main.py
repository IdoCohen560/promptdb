"""PromptDB CLI — the flagship interface."""

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    help="PromptDB — ask your database in English.",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()


@app.command()
def ask(question: str) -> None:
    """Ask a natural-language question about the database."""
    from promptdb.agent.graph import build_graph

    with console.status("[dim]thinking…[/]"):
        result = build_graph().invoke({"question": question})

    if result.get("error"):
        console.print(f"[dim]SQL:[/] {result.get('sql', '?')}")
        console.print(f"[red]Query error:[/] {result['error']}")
        raise typer.Exit(1)

    console.print(f"[dim]SQL:[/] [cyan]{result['sql']}[/]")

    cols = result.get("columns", [])
    rows = result.get("rows", [])
    if cols:
        table = Table(show_header=True, header_style="bold")
        for c in cols:
            table.add_column(str(c))
        for r in rows[:20]:
            table.add_row(*[str(v) for v in r])
        console.print(table)

    console.print(f"\n[bold green]{result['answer']}[/]")


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
