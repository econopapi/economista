# economista.py  

Documentación extensa: https://econopapi.com/proyecto/economista/

---

`economista` es la biblioteca definitiva para datos, análisis e investigación económica aplicada en Python.

El objetivo es ofrecer una capa económica sobre el ecosistema científico de Python para obtener, normalizar, analizar, modelar y visualizar datos económicos con metadatos reproducibles.

`economista.py` no busca reemplazar a `pandas`, `numpy`, `scipy`, `statsmodels`, `scikit-learn`, `linearmodels`, `xarray`, `matplotlib` o `plotly`. Busca integrarlos, organizarlos y especializarlos para resolver problemas reales de economía aplicada.

> Una capa económica para el ecosistema científico de Python.

## Estado

Proyecto en fase fundacional. La API pública todavía no es estable.

## Instalación

```bash
pip install economista
```

La instalación base incluye los conectores de datos, por lo que no necesitas
extras para empezar a trabajar con World Bank/WDI e IMF DataMapper API v2.

## World Bank/WDI

```python
from economista import data

ds = data.fetch(
    source="world_bank",
    dataset="wdi",
    indicator="NY.GDP.MKTP.CD",
    geo=["MEX", "COL"],
    start=2000,
    end=2024,
)

df = ds.to_pandas()
metadata = ds.metadata.to_dict()
```

`data.fetch` devuelve un `EconDataset`: un `DataFrame` de pandas acompañado de
metadata económica, esquema e historial mínimo de consulta.

También puedes explorar catálogos de datos. `data.search` devuelve un
`DataFrame` por default para que sea cómodo en notebooks:

```python
indicadores = data.search(
    source="world_bank",
    query="GDP current US dollars",
    kind="indicators",
)
```

También sirve para encontrar códigos de países sin conocer ISO2 o ISO3:

```python
paises = data.search(
    source="world_bank",
    query="Mexico",
    kind="geos",
)
```

## IMF DataMapper API v2

`economista` incluye un conector para la API pública **IMF DataMapper API v2**.
Es una superficie anual y curada de indicadores IMF —incluidos WEO, Fiscal
Monitor y otros datasets publicados en DataMapper—, no un reemplazo del API
SDMX completo de IMF.

```python
crecimiento = data.fetch(
    source="imf",
    indicator="NGDP_RPCH",
    geo=["MEX", "COL"],
    start=2020,
    end=2025,
)

indicadores_imf = data.search(
    source="imf",
    query="real GDP growth",
    kind="indicators",
    dataset="WEO",
)
```

Cada observación conserva el dataset de procedencia que reporta IMF en la columna
`dataset` y sus unidades. El catálogo de indicadores expone también el año de
proyección cuando IMF lo publica; consúltalo antes de tratar una serie como datos
observados.

Puedes buscar en todos los conectores registrados omitiendo `source`, limitar
resultados con `limit=25` o traer todo con `limit=None`:

```python
resultados = data.search(query="external debt", kind="all")
```

La búsqueda actual es lexical sobre catálogos oficiales. No usa embeddings,
modelos de lenguaje ni verifica todavía cobertura completa indicador-país.

## Alcance actual

El MVP incluye World Bank/WDI e IMF DataMapper API v2, esquema canónico,
metadata, exportación CSV/JSON/Parquet, caché local mínima y exploración tabular
de catálogos. FRED, INEGI y carga local CSV/Excel serán los siguientes cortes.

Ejemplos interactivos:

- `examples/data_search_exploration.ipynb`
- `examples/data_world_bank_wdi.ipynb`
- `examples/data_imf_datamapper_weo.ipynb`

La documentación por conector está en `docs/data/`.

## Desarrollo

La guia para instalar, probar y trabajar localmente en el paquete esta en
`docs/development/handbook.md`.
