# economista.py

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

La instalación base incluye el primer conector de datos, por lo que no necesitas
extras para empezar a trabajar con World Bank/WDI.

## Primer uso

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

Puedes buscar en todos los conectores registrados omitiendo `source`, limitar
resultados con `limit=25` o traer todo con `limit=None`:

```python
resultados = data.search(query="external debt", kind="all")
```

La búsqueda actual es lexical sobre catálogos oficiales. No usa embeddings,
modelos de lenguaje ni verifica todavía cobertura completa indicador-país.

## Alcance actual

El primer MVP funcional incluye World Bank/WDI, esquema canónico, metadata,
exportación CSV/JSON/Parquet, caché local mínima y exploración tabular de
catálogos World Bank. FRED, IMF, INEGI y carga local CSV/Excel serán los
siguientes cortes.

Ejemplos interactivos:

- `examples/world_bank_gdp.ipynb`
- `examples/world_bank_population.ipynb`
- `examples/world_bank_gdp_growth.ipynb`
- `examples/world_bank_inflation.ipynb`

## Desarrollo

La guia para instalar, probar y trabajar localmente en el paquete esta en
`docs/development/handbook.md`.
