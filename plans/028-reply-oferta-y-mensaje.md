# Plan 028 — Oferta y mensaje en favoritos no respondidos

**Estado:** completado.

**Objetivo:** completar `vinted reply`: al abrir cada notificación de favorito no
respondida, ofrecer 2 € menos que el precio anterior y enviar la plantilla
`Data/reply_added_favorites.txt`.

## Decisiones acordadas con el propietario

1. Solo `--publish` escribe en Vinted. `--dry-run` no abre navegador;
   `--simulate-send` y `--check-submit` solo inspeccionan y registran lo que
   harían, sin pulsar botones ni enviar mensajes.
2. La oferta y el mensaje se ejecutan **en el momento de abrir** cada
   conversación, dentro del bucle secuencial de notificaciones.
3. Se mantiene `offer-current-price-label` como marcador de «respondida». Al
   detectarla no se actúa y se detiene el barrido de esa cuenta.
4. El precio del placeholder (`XX,XX €`) se escribe como `XX,XX` (coma decimal,
   dos decimales, sin `€`) tras restar `2,00`, usando `Decimal`.
5. La plantilla se exige en todos los modos reales; `--dry-run` sigue sin
   exigirla.
6. Errores por notificación (precio ilegible o ≤ 2 €, selector ausente, fallo
   al enviar) se registran y se continúa con la siguiente. Si la oferta se
   aceptó pero falló el mensaje, no se reintenta.
7. Pausas entre acciones con el `ActionPacer` existente; sin variables nuevas.

## Cambios por fase

### Fase 1 — Contrato y lógica pura
- `shared/offers.py`: parseo del placeholder y cálculo del precio de oferta con
  `Decimal`, sin Selenium.
- `FavoriteNotification` gana `previous_price`, `offered_price` y
  `message_sent` (opcionales).
- `ScanFavoriteNotifications` lleva la plantilla; `FavoriteReplier.scan_favorites`
  la recibe y `reply()` desaparece.

### Fase 2 — Adapter
- Nuevos selectores `offer-price-field--input`, `offer-submit-button` y
  `composer--input`.
- `VintedFavoriteReplier` recibe `send: bool` y ejecuta por pestaña: detectar
  respondida → leer placeholder → calcular precio → (si `send`) rellenar,
  pulsar oferta, rellenar mensaje y pulsar Enter → cerrar pestaña.
- Con `send=False` solo se registran el precio propuesto y la plantilla que se
  enviaría.

### Fase 3 — Orquestación
- `run_reply` lee la plantilla en modos reales y no en `dry-run`.
- `SeleniumRuntime` activa la escritura solo en `Mode.PUBLISH`.
- `scheduler.py` sin cambios: hereda el nuevo comportamiento vía `run_reply`.

### Fase 4 — Tests y documentación
- Tests unitarios del cálculo de precio, del orden de acciones del adapter, del
  paso de la plantilla y de la validación por modo.
- Actualizar `CONSTITUTION.md`, `README.md`, `docs/architecture.md`,
  `docs/checklist.md` y los planes 007 y 027.
- Verificación: `ruff check .`, `ruff format --check`, `mypy src tests`,
  `pytest`. Sin `--publish`, sin E2E y sin tocar `sessions/`.

## Criterios de aceptación

- `24,95 €` produce una oferta de `22,95`; un precio ≤ 2 € o ilegible se omite.
- Solo `--publish` pulsa la oferta y envía el mensaje con Enter.
- La primera conversación respondida detiene el barrido de esa cuenta.
- Los errores por notificación se registran y no abortan las siguientes.
- `ruff`, `mypy` y `pytest` en verde.

## Resultado

- `ruff check .`, `ruff format --check .`, `mypy src tests` y `pytest` en verde:
  180 tests, 97 % de cobertura sobre la lógica pura medida.
- Comprobado en `--dry-run`: `vinted --dry-run` y `vinted reply --dry-run`
  terminan con código 0 sin abrir navegador ni exigir plantilla.
- Sin cambios en `sessions/`, sin `--publish` y sin prueba E2E contra Vinted.
  La verificación de la modal queda pendiente en `docs/checklist.md`.
- Mantenimiento posterior (`bc2af65`, `573b78e`, `a19f100`): se espera la modal de
  oferta antes de comprobar el estado, se amplía el timeout de la comprobación y
  se considera respondida la conversación con mensajes existentes
  (`conversation-message`), además del marcador original. Los tests y la
  documentación se adaptaron a esa decisión vigente.
