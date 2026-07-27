# Conectores de datos

`economista.data` ofrece una interfaz común para descubrir catálogos y descargar
series económicas. Cada consulta devuelve un `EconDataset` con datos en formato
canónico, metadata de procedencia e historial de consulta.

| Fuente | `source` | Cobertura actual |
| --- | --- | --- |
| [World Bank/WDI](world_bank.md) | `"world_bank"` | Indicadores de desarrollo, geografías y temas WDI. |
| [IMF DataMapper API v2](imf_datamapper.md) | `"imf"` | Indicadores anuales publicados por DataMapper, incluidos WEO y Fiscal Monitor. |

## Explorar antes de descargar

Usa `data.search` para encontrar códigos de indicadores y geografías. La forma
más eficiente es restringir la fuente y el tipo de catálogo:

```python
from economista import data

data.search(
    source="imf",
    dataset="WEO",
    query="real GDP growth",
    kind="indicators",
)
```

Si omites `source`, la búsqueda recorre todos los conectores registrados. Es el
modo apropiado para exploración amplia, aunque la primera consulta puede tardar
más mientras se descargan y guardan en caché los catálogos de cada fuente.

Los conectores se documentan con su alcance, semántica y limitaciones propias;
una fuente pública no implica que todas sus series sean directamente
comparables con las de otra fuente.
