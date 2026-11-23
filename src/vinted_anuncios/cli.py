from __future__ import annotations

from collections.abc import Callable
from typing import Annotated

import typer

from .adapters.selenium_driver import SeleniumDriverFactory
from .features.check_session.command import CheckSession, SessionError
from .features.check_session.handler import check_session
from .features.run_sweep.handler import run_publish, run_reply, run_sweep
from .scheduler import start
from .shared.config import ConfigError
from .shared.logging_conf import setup_logging
from .shared.models import Mode
from .shared.settings import SettingsError, load_settings

app = typer.Typer(help="Publicador local de anuncios de Vinted (modo simulación por defecto)")

PublishOption = Annotated[bool, typer.Option("--publish", help="Publica de verdad en Vinted")]
DryRunOption = Annotated[bool, typer.Option("--dry-run", help="Fuerza la simulación (por defecto)")]
ScheduleOption = Annotated[
    bool, typer.Option("--schedule", help="Queda vivo y ejecuta los dos jobs programados")
]


def _execute(action: Callable[..., None], *, publish: bool, dry_run: bool, schedule: bool) -> None:
    try:
        settings = load_settings()
        logger = setup_logging(settings.log_dir)
        mode = Mode.PUBLISH if publish and not dry_run else Mode.DRY_RUN
        if schedule:
            start(settings, mode, logger=logger)
        else:
            action(settings, mode, logger=logger)
    except (ConfigError, SettingsError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    publish: PublishOption = False,
    dry_run: DryRunOption = False,
    schedule: ScheduleOption = False,
) -> None:
    """Recorre Data y aplica el barrido completo por defecto."""
    if ctx.invoked_subcommand is not None:
        return
    _execute(run_sweep, publish=publish, dry_run=dry_run, schedule=schedule)


@app.command("publish")
def publish_command(publish: PublishOption = False, dry_run: DryRunOption = False) -> None:
    """Escanea Data y publica anuncios pendientes; no responde favoritos."""
    _execute(run_publish, publish=publish, dry_run=dry_run, schedule=False)


@app.command("reply")
def reply_command(publish: PublishOption = False, dry_run: DryRunOption = False) -> None:
    """Revisa favoritos de cada cuenta; no escanea ni publica anuncios."""
    _execute(run_reply, publish=publish, dry_run=dry_run, schedule=False)


@app.command("sweep")
def sweep_command(
    publish: PublishOption = False,
    dry_run: DryRunOption = False,
    schedule: ScheduleOption = False,
) -> None:
    """Publica anuncios y responde favoritos, igual que `vinted` sin subcomando."""
    _execute(run_sweep, publish=publish, dry_run=dry_run, schedule=schedule)


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
