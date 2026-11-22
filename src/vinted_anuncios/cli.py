from __future__ import annotations

import typer

from .features.run_sweep.handler import run_sweep
from .scheduler import start
from .shared.config import ConfigError
from .shared.logging_conf import setup_logging
from .shared.models import Mode
from .shared.settings import SettingsError, load_settings

app = typer.Typer(help="Publicador local de anuncios de Vinted (modo simulación por defecto)")


@app.command()
def main(
    publish: bool = typer.Option(False, "--publish", help="Publica de verdad en Vinted"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Fuerza la simulación (por defecto)"),
    schedule: bool = typer.Option(False, "--schedule", help="Queda vivo y ejecuta a las 16:00"),
) -> None:
    """Recorre Data y aplica el barrido. Sin --publish no se escribe en Vinted."""
    try:
        settings = load_settings()
        logger = setup_logging(settings.log_dir)
        mode = Mode.PUBLISH if publish and not dry_run else Mode.DRY_RUN
        if schedule:
            start(settings, mode, logger=logger)
        else:
            run_sweep(settings, mode, logger=logger)
    except (ConfigError, SettingsError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc


if __name__ == "__main__":
    app()
