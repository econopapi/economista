# World Bank / World Development Indicators

El conector `source="world_bank"` accede a World Development Indicators (WDI)
mediante la API pública del Banco Mundial. No requiere credenciales.

## Descargar observaciones

```python
from economista import data

gdp = data.fetch(
    source="world_bank",
    dataset="wdi",
    indicator="NY.GDP.MKTP.CD",
    geo=["MEX", "COL"],
    start=2000,
    end=2024,
)
```

`indicator` y `geo` son obligatorios. Ambos aceptan un código o una lista de
códigos. El resultado conserva el valor original de WDI y los campos canónicos
`source="world_bank"` y `dataset="wdi"`; convierte unidades para presentación
solo después de llamar a `to_pandas()`.

## Catálogos disponibles

```python
data.search(source="world_bank", query="GDP", kind="indicators")
data.search(source="world_bank", query="Mexico", kind="geos")
data.search(source="world_bank", query="debt", kind="topics")
```

Las geografías aceptan los filtros `region`, `income_level` e
`include_aggregates=False`. La búsqueda es lexical sobre metadatos oficiales;
no confirma por sí sola que un indicador tenga cobertura para cada país o año.

## Operación y trazabilidad

El conector consulta observaciones país por país, usa pausas, reintentos para
errores transitorios y caché local. Es una decisión de resiliencia frente a la
fragilidad de consultas multi-país de WDI. Cada `EconDataset` registra fuente,
consulta, cobertura observada y fecha de descarga.

Consulta [el ejemplo de panel WDI](../../examples/data_world_bank_wdi.ipynb) para
una comparación integrada de PIB, población, crecimiento e inflación.
