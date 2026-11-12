# AGENTS.md

Guia operativa para agentes que trabajen en `economista`.

## Identidad del proyecto

`economista` es una biblioteca open source de Python para economia aplicada. Su
proposito es ser una capa economica sobre el ecosistema PyData, no reemplazarlo.
Integra `pandas`, `numpy`, `statsmodels`, `scipy`, `xarray`, `matplotlib`,
`plotly` y herramientas maduras cuando ya resuelven bien el problema.

La promesa tecnica es:

> Obtener, normalizar, analizar, modelar y visualizar datos economicos con
> metadatos reproducibles, bajo una API coherente, unificada y extensible.

Trata el repo como un paquete academico serio: claridad, trazabilidad,
reproducibilidad, pruebas y documentacion son parte del producto.

## Principios de trabajo

- Lee el codigo y el documento fundacional antes de proponer cambios grandes.
- Prefiere cambios pequenos, revisables y alineados con la arquitectura actual.
- No introduzcas scope creep. El paquete debe crecer por modulos bien terminados,
  no por listas largas de funciones incompletas.
- No reimplementes bibliotecas maduras salvo que exista una razon economica clara.
- Usa nombres explicitos y economicos. Los alias cortos pueden existir despues,
  pero la API principal debe comunicar intencion.
- Mantener compatibilidad PyData es obligatorio: los objetos centrales deben
  interoperar limpiamente con `pandas` y, cuando aplique, con el resto del stack.
- No rompas cambios no relacionados del usuario. Si el arbol esta sucio, entiende
  el estado antes de editar.

## Arquitectura actual

- `economista.core`: abstracciones base, metadata, schema, query, config, cache y
  errores. Debe ser pequeno, estable y cuidadoso.
- `economista.data`: API publica de datos, conectores, registry y normalizacion.
  No debe depender de `analysis`.
- `examples/`: notebooks ejecutables, pedagogicos y sin outputs guardados.
- `tests/`: pruebas unitarias y fixtures. Las pruebas contra APIs reales no deben
  correr por defecto en CI.

Objeto central:

- `EconDataset` envuelve un `pandas.DataFrame`.
- No heredar de `pandas.DataFrame`.
- La metadata no es decoracion; es parte estructural del resultado.
- `data.fetch(...)` debe devolver `EconDataset` por default.
- `to_pandas()` es la via principal para interoperar.

Formato canonico recomendado:

```text
geo | geo_name | time | value | indicator | indicator_name | unit | frequency | source | dataset
```

Columnas opcionales relevantes:

```text
sector | product | currency | seasonal_adjustment | price_base | notes | downloaded_at
```

## Conectores de datos

Todo conector debe seguir este flujo conceptual:

```text
Solicitud del usuario
-> DataQuery
-> ConnectorRegistry
-> BaseConnector concreto
-> Respuesta cruda
-> Normalizacion
-> Validacion de schema
-> EconDataset
-> Cache
-> Usuario
```

Reglas para conectores:

- Deben devolver esquema canonico o levantar errores explicitos.
- Deben preservar metadata: fuente, dataset, indicador, cobertura geografica,
  cobertura temporal, fecha de descarga y parametros de consulta.
- Deben usar errores personalizados de `economista.core.errors`.
- Deben ser robustos ante APIs externas inestables: timeouts, 429, 5xx, payloads
  inesperados y cambios de formato.
- No asumas que una API externa es estable. Usa fixtures para pruebas por defecto.
- Las pruebas online deben ser opcionales y marcadas como integracion.
- Si una fuente tiene endpoints fragiles, prefiere estrategias conservadoras
  aunque hagan mas requests.

Nota sobre World Bank/WDI:

- El conector evita `source=2` por default porque produjo 502/timeouts.
- El conector consulta pais por pais y combina resultados para evitar fragilidad
  del endpoint multi-pais.
- Conserva `User-Agent`, `follow_redirects`, pausa breve y reintentos para
  errores temporales.

## Testing y calidad

Antes de cerrar cambios de codigo, corre:

```bash
pytest -q
ruff check .
mypy
```

Para cambios de empaquetado, tambien corre:

```bash
python -m build
```

Expectativas:

- `mypy` esta en modo estricto.
- Ruff usa line length 88.
- No agregues dependencias sin justificar su lugar: base, `analysis`, `viz`,
  `docs` o `dev`.
- Tests de conectores deben usar fixtures o mocks por defecto.
- No dependas de internet para la suite normal.

## Notebooks y ejemplos

Los notebooks son parte de la experiencia publica del paquete.

- Deben ser pedagogicos, comentados entre celdas y faciles de ejecutar.
- No guardes outputs pesados ni resultados gigantes.
- Evita dependencias visuales no declaradas, por ejemplo `DataFrame.style` si
  requiere `jinja2`.
- Muestra unidades legibles: millions, billions, percent, indices, etc.
- Mantener ejemplos pequenos y estables es mejor que cubrir demasiados casos.

## Documentacion

La documentacion debe explicar tanto el uso como la razon economica.

- README: instalacion, primer uso y alcance actual.
- Notebooks: ejemplos interactivos.
- Futuro `docs/`: tutoriales, guias conceptuales y referencia API.

Regla de release:

> No documentation, no release.

## Versionado y releases

El proyecto usa SemVer con criterio pragmatico para `0.x`.

- Patch: correcciones internas o bugfixes pequenos.
- Minor: nueva capacidad publica, nuevo conector, nuevo modulo o ampliacion clara
  de API.
- Major: reservado para estabilizacion futura `1.0`.

Los tags deben usar formato:

```text
vX.Y.Z
```

La version de `pyproject.toml` debe coincidir con el tag.

## Prioridades de roadmap

Prioridad inmediata despues de `0.2.0`:

1. Robustecer `core` y `data`.
2. Carga local CSV/Excel.
3. Nuevos conectores con alto valor: FRED, IMF, INEGI.
4. Documentacion inicial mas completa.

No adelantes modulos analiticos grandes si no cumplen:

- API clara.
- Tests.
- Documentacion.
- Ejemplos.
- Integracion con `EconDataset` y `pandas.DataFrame`.
- Errores explicitos.
- Decision clara de construir o delegar.

## Estilo de colaboracion

El modo de trabajo ideal para este repo:

- Primero entender el contexto y el documento fundacional.
- Luego proponer un corte pequeno y util.
- Implementar con pruebas y ejemplos.
- Validar con comandos reales.
- Resumir decisiones, riesgos y siguientes pasos.

Este paquete debe sentirse como herramienta confiable para investigacion,
docencia, consultoria, sector publico y analisis profesional de datos
economicos.

## Gobernanza vigente desde 2026-11-11

Lee [GOVERNANCE.md](GOVERNANCE.md) antes de proponer una funcionalidad nueva.
Toda capacidad pública debe completar el ciclo: necesidad económica,
implementación revisada, release con SemVer, investigación reproducible y
divulgación. Tras un release funcional, no inicies otra capacidad hasta que
Daniel y Jesús aprueben los resultados publicados y queden registrados sus
enlaces. Se permiten correcciones, seguridad, documentación y mantenimiento.

El documento fundacional original es histórico; consulta su
[apéndice vigente](docs/development/foundational_addendum_2026-11-11.md).
