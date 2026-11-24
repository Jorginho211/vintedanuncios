# Plan 024 — Docker Compose completo: Selenium, scheduler y CLI

**Estado:** completado.

## Objetivo

Poder instalar el proyecto en otra máquina con Docker únicamente: un compose que
levante el grid de Selenium y el scheduler, y que permita ejecutar los comandos
de la CLI contra ese mismo entorno compartiendo `Data/`, `sessions/` y `logs/`
con el host.

## Decisiones consultadas al propietario

- El scheduler del contenedor arranca con `--publish --schedule` (autorización
  explícita del propietario). La regla de no publicar sin `--publish` se mantiene
  para el resto de ejecuciones; este plan no ejecuta publicaciones reales.
- Los comandos sueltos se lanzan con `docker compose run --rm vinted ...`, sin
  servicios adicionales ni `docker compose exec`.
- El usuario de los contenedores de la app se toma de `UID`/`GID` del host con
  valor por defecto 1000:1000. Selenium mantiene su usuario actual del compose.
- Las rutas compartidas son fijas y relativas al compose: `./Data`, `./sessions`
  y `./logs`. No se añaden variables `HOST_*`.

## Implementación

1. `Dockerfile`: `python:3.12-slim` + `tzdata`, instalar solo dependencias de
   producción con `pip install .`, `WORKDIR /app`, `ENTRYPOINT ["vinted"]` y
   `CMD ["--dry-run"]`. Sin dependencias de desarrollo.
2. `.dockerignore`: excluir Git, datos, perfiles, logs, `.env*`, cachés y tests
   para no meter secretos ni contenido personal en el contexto de build.
3. `docker-compose.yaml`: conservar `selenium` y añadir healthcheck con
   `curl /status`; servicio `vinted` con `command: ["--publish", "--schedule"]`,
   `restart: unless-stopped`, `depends_on` healthcheck, `env_file` opcional y
   variables forzadas `SELENIUM_URL=http://selenium:4444`, `DATA_DIR=/Data`,
   `PROFILES_DIR=/sessions`, `SELENIUM_DATA_DIR=/Data`,
   `SELENIUM_PROFILES_DIR=/sessions`. Volúmenes: `./Data:/Data:rw`,
   `./sessions:/sessions:rw`, `./logs:/app/logs:rw`.
4. Documentación: README, `docs/architecture.md`, `docs/security.md`,
   `CONSTITUTION.md` y `.env.example`.

## Verificación

- `docker compose config`
- `docker compose build`
- `docker compose run --rm vinted --dry-run`
- `docker compose up -d selenium` y comprobación de salud del grid
- `ruff`, `mypy` y `pytest` en verde
- No se ejecuta `--publish` ni `--simulate-send` durante la verificación.
