# IMF DataMapper API v2

El conector `source="imf"` integra la API pública **IMF DataMapper API v2** sin
credenciales. DataMapper es una superficie anual y curada de indicadores IMF;
no sustituye al API SDMX completo de IMF ni pretende exponer todos sus dataflows.

## Descargar observaciones

```python
from economista import data

growth = data.fetch(
    source="imf",
    dataset="WEO",
    indicator="NGDP_RPCH",
    geo=["MEX", "COL"],
    start=2020,
    end=2026,
)
```

`indicator` es obligatorio y acepta uno o varios códigos. `geo`, `start` y `end`
son opcionales; las observaciones están disponibles solo con frecuencia anual.
La columna `dataset` conserva el dataset que reporta DataMapper para cada
indicador, por ejemplo `WEO` o `FM`. Si se proporciona `dataset` al descargar,
se valida contra esa procedencia.

## Explorar indicadores y geografías

```python
data.search(
    source="imf",
    dataset="WEO",
    query="real GDP growth",
    kind="indicators",
)

data.search(
    source="imf",
    query="Mexico",
    kind="geos",
    geo_type="country",
)
```

El catálogo de indicadores expone unidad, descripción, dataset, fecha de
actualización y `projection_year` cuando IMF lo publica. Las geografías se
clasifican como `country`, `region` o `group`. DataMapper no expone un catálogo
equivalente de temas, por lo que `kind="topics"` devuelve una tabla vacía.

## Interpretación y límites

El año de proyección debe revisarse antes de interpretar períodos futuros como
observaciones realizadas. Las estimaciones y proyecciones de WEO pueden diferir
de estadísticas nacionales o de otras series IMF por metodología y revisiones.

Para resultados consistentes ante el comportamiento variable de los filtros
remotos de DataMapper, el conector filtra geografía y período localmente. La
caché local evita descargar de nuevo los catálogos y consultas idénticas.

Consulta [el ejemplo WEO](../../examples/data_imf_datamapper_weo.ipynb) para un
flujo completo de descubrimiento, descarga, comparación y metadata.
