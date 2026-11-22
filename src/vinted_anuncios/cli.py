from __future__ import annotations

import os
from pathlib import Path

import typer

from . import scheduler
from .config import ConfigError, validate_data_dir
from .runner import run_once

app = typer.Typer(help="Publicador local de anuncios de Vinted (modo simulación por defecto)")


@app.command()
def main(
    publish: bool = typer.Option(False, "--publish", help="Publica de verdad en Vinted"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Fuerza la simulación (por defecto)"),
    schedule: bool = typer.Option(False, "--schedule", help="Queda vivo y ejecuta a las 16:00"),
) -> None:
    """Recorre Data y aplica el barrido. Sin --publish no se escribe en Vinted."""
    try:
        validate_data_dir(Path(os.getenv("DATA_DIR", "Data")))
        do_publish = publish and not dry_run
        if schedule:
            scheduler.start(publish=do_publish)
        else:
            run_once(publish=do_publish)
    except ConfigError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc


if __name__ == "__main__":
    app()
