# Constitución del proyecto — VintedAnuncios

## 1. Propósito

Herramienta **local** y de uso personal que, desde un árbol de carpetas, publica anuncios en Vinted y responde una sola vez al primer mensaje del comprador cuando recibe una alerta de favorito.

No es un servicio multiusuario, no expone API y no se ejecuta en la nube.

## 2. Principios rectores

1. **Simulación por defecto.** Ninguna acción escribe en Vinted salvo que se pase explícitamente `--publish`.
2. **El sistema de archivos es la fuente de verdad.** Una carpeta de anuncio existe = anuncio pendiente. Se borra solo después de que Vinted confirme la publicación.
3. **Separación de capas.** `shared/` contiene datos y contratos; los handlers de
   `features/` contienen los casos de uso; Selenium y el filesystem viven aislados
   en `adapters/`. Los puertos de `shared/ports.py` definen la frontera.
4. **Sin estado local para las respuestas.** Vinted determina qué conversación fue respondida; solo se escriben logs de auditoría (sin datos personales).
5. **Seguridad por defecto.** Perfiles de navegador fuera de Git, Selenium escuchando solo en `127.0.0.1`, escaneo de secretos, logs sin mensajes de compradores.
6. **Sin evasión de controles de la plataforma.** El riesgo de las condiciones de servicio de Vinted fue revisado y aceptado por el propietario. No se implementan mecanismos anti-CAPTCHA ni de ocultación de automatización.
7. **Toda decisión importante se consulta.** Cada funcionalidad nueva se registra en `plans/` antes de implementarse.

## 3. Stack tecnológico

| Capa | Elección |
|---|---|
| Lenguaje | Python 3.12 |
| Entorno y dependencias | Poetry (`pyproject.toml`, `poetry.lock`) |
| Automatización | Selenium + Firefox (Docker, `docker-compose.yaml`) |
| Caption | Nombre del archivo de foto; solo `pathlib`, sin librerías de metadatos |
| Scheduler | APScheduler, cron `0 16 * * *`, `Europe/Madrid` configurable por `TIMEZONE` |
| CLI | Typer |
| Calidad | Ruff, mypy estricto, pytest, pre-commit (Ruff + mypy + detect-secrets), pip-audit manual |

## 4. Contrato de datos

### Caption (nombre del archivo de una de las fotos)

```
precio;medidas(ancho x largo);marca(opcional);modelo(opcional)
```

- `;` es siempre separador; no se escapa dentro de los valores.
- Se permite un `;` final y se interpreta como "sin modelo".
- `medidas` en centímetros con formato `50x60`.
- El nombre del archivo es la caption sin la extensión: `24.95;50x60;Nike;35A.HEIC`.
- Ejemplos: `25;40x30.HEIC`, `25;40x30;Levis.HEIC`, `25;40x30;Levis;Air Max 90.HEIC`.
- No se contempla el caso "modelo sin marca".

### Configuración

- Los tres archivos reales de `Data/` son obligatorios. Se crean copiando
  `config.json.example`, `description.example` y `reply_added_favorites.example`.
  Si falta alguno (o la plantilla de respuesta está vacía), la ejecución se
  detiene con un error y código de salida 1; no se escanea ni se publica.
- `Data/config.json`: una clave por categoría, con `default` y variantes opcionales por marca (`levis`).
- Selección del título: nombre de carpeta de categoría (coincidencia exacta; los puntos son literales) + `marca.lower()`. Si no hay variante, se usa `default` sin aviso.
- `Data/description.txt`: descripción común a todas las categorías; se usa tal cual. Si aparece el placeholder `{{TALLA}}`, se deja **literal** y se resolverá en una iteración futura.
- `Data/reply_added_favorites.txt`: plantilla global de respuesta. Si no existe, el módulo de respuestas se omite con un aviso.
- Las variables de entorno se leen y validan una sola vez en `shared/settings.py`;
  `config.py` queda reservado a la configuración de dominio de `Data/`. Los nombres
  de entorno van en inglés, igual que los identificadores de código.

### Árbol

```
Data/<Cuenta>/<Categoría>/<Anuncio>/  (solo fotos)
sessions/<Cuenta>/                    (perfil Firefox; contenido ignorado por Git)
```

## 5. Estándares

- Código y variables de entorno en inglés; documentación y logs en español.
- Ruff para formato y lint; mypy en modo estricto.
- Conventional Commits.
- `main` + ramas cortas para cambios grandes.
- Tests unitarios e integración; sin E2E automático contra Vinted.
- Cobertura objetivo: 80 % sobre la lógica pura (`config`, `metadata`, `models`, `scanner`).

## 6. Seguridad

- Selenium/VNC publicados solo en `127.0.0.1`.
- `Data/` excluido de Git; solo `Data/.gitkeep` y los tres `*.example` versionados.
- `sessions/` excluido de Git; solo `sessions/.gitkeep` versionado.
- Escaneo de secretos en pre-commit.
- Logs con identificadores y fechas, nunca texto de mensajes de compradores.
- Pausas configurables entre anuncios y entre cuentas por estabilidad.
- Revisión manual de dependencias con `pip-audit`.

## 7. Pendientes documentados

- Resolver `{{TALLA}}` en una iteración futura (plan 010).
- Confirmar la ubicación exacta de la alerta *"ha marcado como favorito tu artículo"*.
- Completar el spike de persistencia del perfil Firefox (plan 002).
- Definir el destino del campo `modelo` en el formulario de Vinted.

## 8. Proceso de cambio

Las decisiones estructurales (stack, contrato de datos, capas, seguridad) se consultan al propietario antes de aplicarse. Los cambios funcionales se registran como un plan en `plans/` y se marcan como completados al finalizar.
