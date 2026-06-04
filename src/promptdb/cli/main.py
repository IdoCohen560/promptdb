"""PromptDB CLI — the flagship interface."""

import time
from pathlib import Path

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

    t0 = time.monotonic()
    with console.status("[dim]thinking…[/]"):
        result = build_graph().invoke({"question": question})
    elapsed = time.monotonic() - t0

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
    console.print(
        f"[dim]· {elapsed:.2f}s · ${result.get('cost_usd', 0.0):.5f} · "
        f"{result.get('attempts', 1)} attempt(s)[/]"
    )


@app.command()
def schema(output: str = typer.Option("", help="Write the Mermaid diagram to a file instead of stdout")) -> None:
    """Render an ER diagram (Mermaid) of the database schema."""
    from promptdb.data.schema_graph import mermaid_er

    diagram = mermaid_er()
    if output:
        Path(output).write_text(diagram)
        console.print(f"Wrote ER diagram to {output}")
    else:
        console.print(diagram)


@app.command()
def profile() -> None:
    """Profile the database: row counts, null rates, distinct counts (read-only)."""
    from promptdb.data.profile import profile_db

    data = profile_db()
    tbl = Table(title="Tables", show_header=True, header_style="bold")
    tbl.add_column("Table")
    tbl.add_column("Rows", justify="right")
    tbl.add_column("Cols", justify="right")
    for t in data:
        tbl.add_row(t["table"], f"{t['rows']:,}", str(len(t["columns"])))
    console.print(tbl)
    for t in data:
        nullish = [c for c in t["columns"] if c["null_pct"] > 0]
        if nullish:
            cols = ", ".join(f"{c['col']} {c['null_pct']:.0f}% null" for c in nullish)
            console.print(f"[dim]{t['table']}: {cols}[/]")


@app.command()
def doctor() -> None:
    """Report read-only data-quality issues (orphaned FKs, empty tables, high-null columns)."""
    from promptdb.data.quality import check_quality

    issues = check_quality()
    if not issues:
        console.print("[bold green]No data-quality issues found.[/]")
        return
    colors = {"high": "red", "medium": "yellow", "low": "dim"}
    for i in issues:
        c = colors.get(i["severity"], "white")
        console.print(f"[{c}]{i['severity'].upper():6s}[/] [bold]{i['table']}[/] — {i['issue']}")


if __name__ == "__main__":
    app()
