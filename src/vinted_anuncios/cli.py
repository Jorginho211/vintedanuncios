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
SimulateSendOption = Annotated[
    bool,
    typer.Option(
        "--simulate-send",
        help="Rellena el formulario real sin pulsar Subir; borra las carpetas de anuncio",
    ),
]
CheckSubmitOption = Annotated[
    bool,
    typer.Option(
        "--check-submit",
        help="Diagnostica el estado del formulario antes de pulsar Subir, sin publicar",
    ),
]
ScheduleOption = Annotated[
    bool,
    typer.Option(
        "--schedule",
        help="Queda vivo y ejecuta los jobs programados de publicación y favoritos",
    ),
]


def _resolve_mode(*, publish: bool, dry_run: bool, simulate_send: bool, check_submit: bool) -> Mode:
    flags = [
        (name, value)
        for name, value in (
            ("--publish", publish),
            ("--dry-run", dry_run),
            ("--simulate-send", simulate_send),
            ("--check-submit", check_submit),
        )
        if value
    ]
    if len(flags) > 1:
        names = ", ".join(name for name, _ in flags)
        raise ConfigError(f"Los modos son mutuamente exclusivos: {names}")
    if dry_run:
        return Mode.DRY_RUN
    if simulate_send:
        return Mode.SIMULATE_SEND
    if check_submit:
        return Mode.CHECK_SUBMIT
    if publish:
        return Mode.PUBLISH
    return Mode.DRY_RUN


def _execute(
    action: Callable[..., None],
    *,
    publish: bool,
    dry_run: bool,
    simulate_send: bool,
    check_submit: bool,
    schedule: bool,
) -> None:
    try:
        mode = _resolve_mode(
            publish=publish,
            dry_run=dry_run,
            simulate_send=simulate_send,
            check_submit=check_submit,
        )
        settings = load_settings()
        logger = setup_logging(settings.log_dir)
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
    simulate_send: SimulateSendOption = False,
    check_submit: CheckSubmitOption = False,
    schedule: ScheduleOption = False,
) -> None:
    """Recorre Data y publica los anuncios pendientes por defecto."""
    if ctx.invoked_subcommand is not None:
        return
    _execute(
        run_sweep,
        publish=publish,
        dry_run=dry_run,
        simulate_send=simulate_send,
        check_submit=check_submit,
        schedule=schedule,
    )


@app.command("publish")
def publish_command(
    publish: PublishOption = False,
    dry_run: DryRunOption = False,
    simulate_send: SimulateSendOption = False,
    check_submit: CheckSubmitOption = False,
) -> None:
    """Escanea Data y publica anuncios; no responde favoritos."""
    _execute(
        run_publish,
        publish=publish,
        dry_run=dry_run,
        simulate_send=simulate_send,
        check_submit=check_submit,
        schedule=False,
    )


@app.command("reply")
def reply_command(
    publish: PublishOption = False,
    dry_run: DryRunOption = False,
    simulate_send: SimulateSendOption = False,
    check_submit: CheckSubmitOption = False,
) -> None:
    """Inspecciona notificaciones de favoritos por cuenta; no envía respuestas."""
    _execute(
        run_reply,
        publish=publish,
        dry_run=dry_run,
        simulate_send=simulate_send,
        check_submit=check_submit,
        schedule=False,
    )


@app.command("sweep")
def sweep_command(
    publish: PublishOption = False,
    dry_run: DryRunOption = False,
    simulate_send: SimulateSendOption = False,
    check_submit: CheckSubmitOption = False,
    schedule: ScheduleOption = False,
) -> None:
    """Publica anuncios pendientes, igual que `vinted` sin subcomando."""
    _execute(
        run_sweep,
        publish=publish,
        dry_run=dry_run,
        simulate_send=simulate_send,
        check_submit=check_submit,
        schedule=schedule,
    )


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
