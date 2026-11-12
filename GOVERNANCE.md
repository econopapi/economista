# Gobernanza de desarrollo e investigación

Decisión del equipo core, 11 de noviembre de 2026. Este documento establece el
flujo vigente para las nuevas capacidades públicas de `economista`.

## Propósito y selección

Las funcionalidades parten principalmente de las agendas de investigación de
Daniel Limón y Jesús Morales y de necesidades técnico-económicas verificables de
la comunidad. Cada propuesta debe identificar el problema económico, el usuario,
los datos disponibles y qué conocimiento permitirá generar. La adopción por
personas y agentes de IA es una meta de claridad, documentación, ejemplos,
descubribilidad y fiabilidad de la API; no justifica sumar funciones sin terminar.

## Ciclo obligatorio

1. **Proponer.** Abrir un issue o PR que describa problema, alcance, método,
   fuentes, caso de estudio y límites previsibles.
2. **Desarrollar y revisar.** Implementar una capacidad acotada con pruebas,
   documentación, ejemplo reproducible e integración con `EconDataset` y pandas
   cuando corresponda. El PR de feature entra a `development` sin cambiar versión.
3. **Publicar el software.** Preparar un PR de release de `development` a `main`,
   ejecutar los controles de calidad, incrementar SemVer y publicar tag, GitHub
   Release y PyPI conforme al handbook.
4. **Investigar.** Ejecutar la capacidad sobre datos reales y publicar en GitHub
   pregunta, procedencia y versión de datos, código, parámetros, resultados,
   comparaciones, limitaciones y versiones del software. Un resultado que no
   confirme la hipótesis también cuenta si está bien documentado.
5. **Divulgar.** Publicar una explicación accesible en Econopapi o el futuro
   blog de `economista.py`, con enlaces al análisis y al release. Un video es
   deseable, pero no obligatorio.

Daniel y Jesús revisan tanto el análisis como la divulgación. Sus aprobaciones
y los enlaces públicos se registran en el issue o PR de seguimiento del ciclo.
El ciclo termina cuando ambos han aprobado los resultados publicados.

## Pausa entre funcionalidades

Después de publicar una funcionalidad nueva, no se inicia otra hasta cerrar
su ciclo de investigación y divulgación. La pausa no impide corregir errores,
vulnerabilidades, documentación, compatibilidad, infraestructura o mantenimiento
de capacidades existentes. Los estudios de una misma funcionalidad pueden
completarse durante la pausa.

## Primera aplicación: análisis de colas

El primer ciclo aplica a la integración de `powerlaw`. Los casos comprometidos
son población por localidad del ITER 2020 e ingreso corriente por hogar de la
ENIGH 2024. Este último será exploratorio sobre la muestra no ponderada; su
descripción ponderada se presentará por separado y no se afirmará inferencia
nacional a partir del ajuste de `powerlaw`.

El documento fundacional original conserva su valor histórico. Su actualización
fechada se encuentra en
[el apéndice de noviembre de 2026](docs/development/foundational_addendum_2026-11-11.md).
