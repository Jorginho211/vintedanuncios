from __future__ import annotations

import typer

from .adapters.selenium_driver import SeleniumDriverFactory
from .features.check_session.command import CheckSession, SessionError
from .features.check_session.handler import check_session
from .features.run_sweep.handler import run_sweep
from .scheduler import start
from .shared.config import ConfigError
from .shared.logging_conf import setup_logging
from .shared.models import Mode
from .shared.settings import SettingsError, load_settings

app = typer.Typer(help="Publicador local de anuncios de Vinted (modo simulación por defecto)")


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    publish: bool = typer.Option(False, "--publish", help="Publica de verdad en Vinted"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Fuerza la simulación (por defecto)"),
    schedule: bool = typer.Option(False, "--schedule", help="Queda vivo y ejecuta a las 16:00"),
) -> None:
    """Recorre Data y aplica el barrido. Sin --publish no se escribe en Vinted."""
    if ctx.invoked_subcommand is not None:
        return
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


def _wait_for_enter() -> None:
    typer.echo("Abre http://127.0.0.1:7900 en tu navegador para ver el Firefox remoto.")
    input("Pulsa Enter para cerrar el navegador...")


@app.command("check-session")
def check_session_command(
    session: str = typer.Argument(..., help="Nombre de la carpeta en sessions/"),
) -> None:
    """Abre Vinted con el perfil de SESSION para verificar la sesión manualmente."""
    try:
        settings = load_settings()
        check_session(
            CheckSession(session=session),
            settings,
            SeleniumDriverFactory(settings),
            confirm=_wait_for_enter,
        )
    except (SessionError, SettingsError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc


if __name__ == "__main__":
    app()
