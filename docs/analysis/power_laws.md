# Análisis de colas con `powerlaw`

`economista.analysis.fit_power_law` adapta la biblioteca externa
[`powerlaw`](https://github.com/powerlaw-devs/powerlaw) a datos económicos con
metadata. Instala el extra opcional:

```bash
pip install "economista[analysis]"
```

```python
from economista.analysis import fit_power_law

fit = fit_power_law(dataset)  # EconDataset con columna value
print(fit.alpha, fit.xmin, fit.ks_distance, fit.n_tail)
comparison = fit.compare_to("lognormal")
print(comparison.log_likelihood_ratio, comparison.p_value)
raw = fit.raw_fit  # API completa de powerlaw, incluidos sus gráficos
```

La función acepta `EconDataset`, `pandas.DataFrame`, `pandas.Series`, arreglos
de NumPy y secuencias de números. Para tablas, `column="value"` es el valor por
defecto; selecciona otra columna con `column="ing_cor"`. Usa `discrete=True`
para conteos enteros, como población por localidad. `xmin=None` delega la
elección del umbral a `powerlaw`; fija un umbral positivo con `xmin=...` si la
pregunta de investigación lo requiere. Los datos deben ser unidimensionales,
finitos y estrictamente positivos. Filtra valores ausentes o inválidos de
forma explícita antes de llamar a la función y registra cuántos excluiste.

`PowerLawFit` conserva una copia de la metadata de `EconDataset` y expone
`alpha`, `xmin`, distancia Kolmogorov-Smirnov (`ks_distance`), error estándar
`sigma`, `n_total`, `n_tail`, `discrete`, `column` y el objeto `raw_fit`.
`compare_to` devuelve la razón de log-verosimilitud y el valor p de
`powerlaw.distribution_compare("power_law", alternativa)`. Una razón positiva
favorece la ley de potencias frente a esa alternativa en la comparación; el
valor p no prueba bondad absoluta de ajuste.

El umbral estimado, el exponente y una recta aparente en escala logarítmica no
demuestran que el mecanismo económico sea una ley de potencias. Compara otras
distribuciones, informa el número de observaciones en la cola y documenta la
selección de datos. El método de [Clauset, Shalizi y Newman
(2009)](https://arxiv.org/abs/0706.1062) explica por qué los ajustes lineales
en gráficos log-log pueden resultar engañosos. Este adaptador no implementa una
prueba de bondad de ajuste por bootstrap ni inferencia para diseños muestrales
complejos; no atribuyas tales conclusiones a sus resultados.

## Estudios reproducibles

- `examples/analysis_power_law_iter_2020.ipynb`: población de localidades
  identificables del ITER 2020. Excluye filas de totales y agregados. Una
  localidad censal no equivale necesariamente a una ciudad o zona
  metropolitana.
- `examples/analysis_power_law_enigh_2024.ipynb`: ingreso corriente trimestral
  por hogar de la ENIGH 2024. Presenta por separado una distribución descriptiva
  con el factor de expansión y el ajuste exploratorio no ponderado. La
  biblioteca `powerlaw.Fit` no acepta pesos muestrales; ni el exponente ni su
  valor p representan inferencia nacional bajo el diseño de ENIGH.

Los notebooks indican las fuentes oficiales y usan archivos descargados por
quien los ejecuta. Los microdatos no se almacenan en el repositorio. Registra
la fecha de descarga, el nombre y hash del archivo, los filtros y las
versiones de `economista` y `powerlaw` al publicar resultados.
