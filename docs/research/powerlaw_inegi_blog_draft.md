# Borrador de divulgación: ¿hay leyes de potencias en localidades e ingresos?

**Estado:** texto para revisión de Daniel y Jesús. No publicar en el blog antes
de revisar el análisis técnico y enlazar la versión liberada de `economista`.

Una distribución puede tener muchos valores pequeños y unos pocos enormes.
Eso ocurre en distintos fenómenos económicos y sociales, pero la forma de una
gráfica no basta para decir que sigue una ley de potencias. Con la nueva función
`fit_power_law` de `economista` exploramos dos preguntas mexicanas: cómo se
distribuye la población entre localidades censales y cómo se distribuye el
ingreso corriente entre los hogares observados en la ENIGH.

Para la primera usamos los datos por localidad del Censo 2020 de INEGI.
Después de excluir filas que representan totales o agregados, analizamos
4 189 localidades con al menos 2 500 habitantes. El ajuste de la cola estimó
un exponente cercano a 1.95. Al subir el umbral a 5 000 y 10 000 habitantes,
la estimación cambió poco, aunque la muestra se redujo. En la comparación que
sí pudo calcularse, la ley de potencias resultó más favorecida que una
distribución exponencial. La biblioteca no consiguió un ajuste lognormal
válido, por lo que no sacamos conclusiones frente a esa alternativa. Una
localidad censal no es lo mismo que una ciudad o una zona metropolitana.

Para la segunda pregunta usamos el ingreso corriente trimestral de 91 408
hogares de la ENIGH 2024 con valores y factores de expansión positivos.
Al estudiar el 10 % superior **de la muestra observada**, el ajuste estimó un
exponente cercano a 3.76. La ENIGH se diseñó para producir resultados
poblacionales mediante factores de expansión, estratos y conglomerados.
La biblioteca estadística utilizada no incorpora esos elementos en el ajuste.
Por eso este número describe una exploración de la muestra: **no es una
estimación de la cola nacional de ingresos**. Mostramos la distribución
ponderada aparte para hacer visible esa diferencia.

En los dos casos falta una prueba de bondad de ajuste por bootstrap. Los
exponentes, las curvas y una comparación favorable no demuestran por sí solos
que exista una ley de potencias ni explican el mecanismo económico detrás de
los datos. La contribución útil de esta primera versión es una ruta clara y
reproducible para formular, ejecutar y criticar esa pregunta. Si el resultado
no respalda la hipótesis, también es conocimiento.

**Para ampliar:** enlazar aquí, tras la revisión, el release de `economista`,
el [análisis técnico](powerlaw_inegi_2026-11-11_draft.md), los dos notebooks y
las fuentes oficiales [ITER 2020](https://www.inegi.org.mx/contenidos/programas/ccpv/2020/datosabiertos/iter/iter_00_cpv2020_csv.zip)
y [ENIGH 2024](https://www.inegi.org.mx/contenidos/programas/enigh/nc/2024/microdatos/enigh2024_ns_concentradohogar_csv.zip).
