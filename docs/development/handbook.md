# Handbook de desarrollo

Guia practica para trabajar localmente en `economista`.

## 1. Clonar el repositorio

```bash
git clone https://github.com/econopapi/economista.git
cd economista
```

Para trabajo cotidiano, parte de `development` y crea una rama para cada cambio:

```bash
git switch development
git pull --ff-only origin development
git switch -c feat/<tema>
```

El flujo recomendado de ramas es:

```text
feat/<tema> -- PR --> development -- release PR --> main -- tag --> GitHub Release --> PyPI
```

Usa ramas `feature/` o `feat/` para cambios concretos, integra primero en
`development` y reserva `main` casi exclusivamente para releases formales con
SemVer.

La separación de responsabilidades es intencional:

- `feat/<tema> → development`: implementa capacidad, pruebas, ejemplos y
  documentación; **no** modifica la versión en `pyproject.toml` ni cierra el
  bloque `Unreleased`.
- `development → main`: es el PR de release; actualiza `pyproject.toml`, mueve
  `Unreleased` a la versión y fecha de publicación, y prepara el tag.

### Trabajar en una feature branch

Usa un nombre que describa la capacidad, por ejemplo:

```bash
git switch -c feat/data-imf-datamapper-connector
```

Antes de cada commit, revisa exactamente lo que va a entrar:

```bash
git status --short
git diff --check
git diff
git add <rutas>
git diff --cached
git commit -m "feat(data): descripcion breve"
```

Después publica la rama y abre un PR hacia `development`:

```bash
git push -u origin feat/data-imf-datamapper-connector
gh pr create \
  --base development \
  --head feat/data-imf-datamapper-connector \
  --title "feat(data): add IMF DataMapper v2 connector" \
  --fill
```

No inicies trabajo nuevo directamente sobre `main`. Si ya tienes cambios sin
commit en `main`, no hace falta perderlos ni usar `stash`: crea inmediatamente
la feature branch desde ese estado y los cambios seguirán en el árbol de trabajo.

```bash
git switch -c feat/<tema>
git branch --show-current
git status --short
```

## 2. Crear un entorno virtual

Recomendado con `venv`:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

En Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

## 3. Instalar el paquete localmente

Para usar el paquete desde el checkout local:

```bash
python -m pip install -e .
```

La bandera `-e` significa "editable": los cambios en `src/economista/` se ven
sin reinstalar el paquete.

Para desarrollar, instala tambien las dependencias de calidad y pruebas:

```bash
python -m pip install -e ".[dev]"
```

En shells que tratan los corchetes de forma especial, conserva las comillas.

## 4. Verificar la instalacion

```bash
python -c "import economista; print(economista.__version__)"
```

Prueba rapida de la API publica:

```bash
python -c "from economista import data; print(data.search(source='world_bank', query='GDP current US dollars', limit=3))"
```

Esa segunda prueba usa internet y depende de World Bank. No debe formar parte de
la suite normal de CI.

## 5. Ejecutar pruebas y calidad

Antes de cerrar un cambio de codigo:

```bash
pytest -q
ruff check .
mypy
```

Que significan:

- `pytest -q`: corre la suite de pruebas.
- `ruff check .`: revisa estilo, imports y errores simples.
- `mypy`: valida tipos. El proyecto usa modo estricto.

Si modificaste empaquetado o metadata de distribucion:

```bash
python -m build
```

## 6. Estructura actual del paquete

```text
src/economista/
├── core/
│   ├── dataset.py
│   ├── metadata.py
│   ├── query.py
│   ├── schema.py
│   ├── config.py
│   ├── cache.py
│   └── errors.py
└── data/
    ├── api.py
    ├── base.py
    ├── registry.py
    └── sources/
        ├── imf.py
        └── world_bank.py
```

Reglas de arquitectura:

- `core` debe permanecer pequeno, estable y con pocas dependencias.
- `data` puede depender de `core`.
- `data` no debe depender de futuros modulos `analysis`.
- `EconDataset` envuelve un `pandas.DataFrame`; no debe heredar de el.
- `data.fetch(...)` debe devolver `EconDataset` por default.

## 7. Desarrollo de conectores

Todo conector debe seguir el flujo:

```text
DataQuery -> ConnectorRegistry -> BaseConnector -> respuesta cruda
-> normalizacion -> validacion -> EconDataset
```

Checklist minimo para un conector:

- Implementa `fetch`.
- Implementa `search` si la fuente lo permite.
- Implementa `available_geos`, `available_indicators` y `available_topics`
  cuando la fuente exponga catalogos equivalentes.
- Devuelve columnas canonicas.
- Llena `EconMetadata`.
- Usa errores personalizados de `economista.core.errors`.
- Tiene tests con fixtures o mocks.
- No depende de internet en la suite normal.

Contrato minimo de busqueda:

```text
source | dataset | kind | id | name
```

`data.search` es exploracion lexical sobre catalogos oficiales. No debe prometer
busqueda semantica, IA ni cobertura completa indicador-pais salvo que el
conector lo implemente y lo documente explicitamente.

Columnas canonicas:

```text
geo | geo_name | time | value | indicator | indicator_name | unit | frequency | source | dataset
```

## 8. Notebooks de ejemplo

Los notebooks viven en `examples/`.

Reglas:

- Deben ser pedagogicos y comentados entre celdas.
- No deben guardar outputs pesados.
- Deben mostrar unidades legibles: billions, millions, percent, indices.
- Evita `DataFrame.style` salvo que la dependencia requerida este declarada.
- Si usan APIs externas, deben ser pequenos y resilientes.

Notebooks actuales:

```text
examples/data_search_exploration.ipynb
examples/data_world_bank_wdi.ipynb
examples/data_imf_datamapper_weo.ipynb
```

Para abrirlos:

```bash
python -m pip install jupyterlab
jupyter lab
```

`jupyterlab` no esta en las dependencias base del paquete.

## 9. Cache local

Los conectores pueden usar cache local via `platformdirs`. La cache existe para:

- reducir llamadas repetidas,
- proteger contra APIs inestables,
- mejorar tiempos de respuesta,
- apoyar reproducibilidad.

Si estas depurando una llamada real a una API, considera instanciar el conector
con `cache=False`.

Ejemplo:

```python
from economista.data.sources.world_bank import WorldBankConnector

wb = WorldBankConnector(cache=False)
```

## 10. Versionado y releases

El proyecto usa SemVer de forma pragmatica:

- Patch: bugfix o correccion pequena.
- Minor: nuevo conector, nueva API publica o capacidad funcional clara.
- Major: reservado para `1.0`.

Antes de release:

```bash
pytest -q
ruff check .
mypy
python -m build
```

### Preparar la release

Una capacidad pública nueva, como un conector, requiere un incremento minor en
la serie `0.x`. Las feature branches dejan esos cambios bajo `Unreleased`; la
preparación de release ocurre exclusivamente en un PR de `development` hacia
`main`:

1. Actualiza la versión en `pyproject.toml`.
2. Cambia el bloque `Unreleased` de `CHANGELOG.md` por la versión y fecha de
   release.
3. Ejecuta el checklist anterior, incluyendo `mypy` y `python -m build`.
4. Abre, revisa y fusiona el PR de release hacia `main`.

La versión de `pyproject.toml` debe coincidir con el tag:

```text
version = "0.4.0"
tag = v0.4.0
```

Tras el merge, etiqueta el commit de `main` y crea el GitHub Release:

```bash
git switch main
git pull --ff-only origin main
git tag -a v0.4.0 -m "release: economista 0.4.0"
git push origin v0.4.0

gh release create v0.4.0 \
  --title "economista 0.4.0" \
  --generate-notes \
  --verify-tag
```

El workflow `Publish to PyPI` se ejecuta al publicar el GitHub Release; no
publiques manualmente el mismo artefacto desde otra máquina. Verifica en GitHub
que el entorno `pypi` y el workflow de publicación terminaron correctamente.

## 11. Errores comunes

### `pytest`, `ruff` o `mypy` no existen

Instala dependencias de desarrollo:

```bash
python -m pip install -e ".[dev]"
```

### Cambios locales no se reflejan al importar

Confirma que instalaste en modo editable:

```bash
python -m pip install -e .
```

### World Bank devuelve 502, 503 o timeout

Las APIs externas fallan. El conector WDI incluye reintentos, `User-Agent`,
`follow_redirects` y pausas breves. Para pruebas automatizadas, usa fixtures o
mocks; no dependas de internet en CI.

### Un notebook se ve raro por salidas viejas

Limpia outputs antes de commitear. En JupyterLab: `Kernel -> Restart Kernel and
Clear Outputs`.

## 12. Forma esperada de contribuir

1. Entiende el problema y el contexto economico.
2. Haz un corte pequeno y verificable.
3. Agrega tests.
4. Agrega o actualiza documentacion.
5. Corre checks.
6. Resume decisiones y riesgos.

El objetivo no es crecer rapido; es crecer con credibilidad tecnica y academica.
