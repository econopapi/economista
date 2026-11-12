# Borrador para revisión core: colas en localidades e ingresos

**Fecha de ejecución:** 11 de noviembre de 2026. **Estado:** resultados
preliminares; falta revisión de Daniel y Jesús, release y divulgación. Este
documento no establece que alguna variable siga una ley de potencias.

## Pregunta y método

Usamos el adaptador `economista.analysis.fit_power_law` sobre dos fuentes
oficiales de INEGI. El ajuste de ley de potencias y la distancia
Kolmogorov-Smirnov provienen de `powerlaw` 2.0.0. Fijamos umbrales previos para
cada ejercicio y exploramos su sensibilidad. No se realizó una prueba de
bondad de ajuste por bootstrap. Una razón de verosimilitud sólo compara los
modelos que sí pudieron ajustarse; no establece por sí sola que el modelo
preferido sea adecuado. Véase [Clauset, Shalizi y Newman
(2009)](https://arxiv.org/abs/0706.1062).

El entorno de cálculo fue Python 3.14, NumPy 2.5.4, pandas 3.0.3, SciPy
1.18.1 y `powerlaw` 2.0.0, con el código del PR de esta funcionalidad. Los
notebooks contienen todos los filtros y comandos. Los archivos CSV originales
no se redistribuyen aquí.

## Población por localidad, ITER 2020

Fuente: [ZIP nacional oficial de ITER
2020](https://www.inegi.org.mx/contenidos/programas/ccpv/2020/datosabiertos/iter/iter_00_cpv2020_csv.zip)
y [descriptor](https://www.inegi.org.mx/contenidos/programas/ccpv/2020/doc/fd_iter_cpv2020.pdf).
SHA-256 del CSV extraído:
`29e9bf43b7d22967d2bdc1ca0a3e47b0fd18802948f2ed42985ae1bc1e34151a`.

De 195 662 filas, el filtro retuvo 189 432 localidades identificables con
población positiva. El análisis principal usa 4 189 localidades con al menos
2 500 habitantes. Se excluyen totales y agregados de localidades de una o
dos viviendas. Las localidades censales no equivalen a ciudades ni zonas
metropolitanas.

| Población mínima (`xmin`) | Localidades en cola | `alpha` | Distancia KS |
| ---: | ---: | ---: | ---: |
| 2 500 | 4 189 | 1.954 | 0.0096 |
| 5 000 | 2 155 | 1.948 | 0.0147 |
| 10 000 | 1 102 | 1.927 | 0.0263 |

Con `xmin=2 500`, la comparación con exponencial devolvió razón de
log-verosimilitud 4 356.8 y valor p aproximado de 1.52 × 10⁻⁶⁷ a favor de
ley de potencias frente a esa alternativa. `powerlaw` advirtió que no
encontró un ajuste lognormal válido; se omite esa comparación. Estos números
no son una prueba de bondad absoluta ni autorizan una afirmación sobre la
distribución de todas las ciudades de México.

## Ingreso corriente de hogares, ENIGH 2024

Fuente: [ZIP oficial de
CONCENTRADOHOGAR](https://www.inegi.org.mx/contenidos/programas/enigh/nc/2024/microdatos/enigh2024_ns_concentradohogar_csv.zip)
y [descripción de la
base](https://www.inegi.org.mx/contenidos/programas/enigh/nc/2024/microdatos/889463924494.pdf).
SHA-256 del CSV extraído:
`e7a7396e92a64f994cd6c9df8dadb97855504122f9719da6676476a56c98d793`.

El archivo contiene 91 414 hogares; 91 408 tienen `ing_cor` y `factor`
positivos. El notebook muestra una curva descriptiva con el factor de
expansión, pero **el ajuste de `powerlaw` usa la muestra sin ponderar**.
Los umbrales son percentiles del ingreso observado, en pesos trimestrales.

| Percentil | `xmin` (MXN trimestrales) | Hogares en cola | `alpha` | Distancia KS |
| ---: | ---: | ---: | ---: | ---: |
| 90 | 135 675.90 | 9 141 | 3.763 | 0.0124 |
| 95 | 175 250.81 | 4 571 | 3.832 | 0.0090 |
| 99 | 309 778.02 | 915 | 3.853 | 0.0420 |

`powerlaw` advirtió que no encontró un ajuste lognormal válido; se omite
esa comparación. Tampoco se puede convertir `alpha` ni su error estándar en
una estimación nacional: el ajuste ignora estratos, conglomerados y factores
de expansión de la encuesta. La metodología oficial identifica `factor` como
ponderador y describe el [diseño muestral
complejo](https://www.inegi.org.mx/contenidos/programas/enigh/nc/2024/doc/889463924517.pdf).

## Revisión pendiente

Daniel y Jesús deben revisar la pregunta, los umbrales, las advertencias de
`powerlaw`, el alcance de las comparaciones y el texto divulgativo. Tras el
release, se publicará una versión aprobada de este análisis con enlaces al
tag y al artículo de divulgación. Un video será opcional.
