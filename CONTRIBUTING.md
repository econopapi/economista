# Contribuir a economista

Gracias por contribuir. Antes de abrir un PR, lee [GOVERNANCE.md](GOVERNANCE.md)
y el [handbook](docs/development/handbook.md).

Las capacidades nuevas deben partir de una necesidad económica concreta y
proponer desde el inicio un caso de investigación con datos reales. Abre un
issue que indique el problema, la API prevista, las fuentes de datos, los
métodos existentes que conviene integrar y los límites del análisis. Durante
la pausa posterior a un release funcional se aceptan correcciones,
documentación, seguridad y mantenimiento, pero no nuevas capacidades.

Crea una rama `feat/<tema>` desde `development`. El PR hacia `development` debe
incluir implementación, pruebas sin dependencia de internet, documentación y un
ejemplo reproducible. Usa interfaces compatibles con `EconDataset` y pandas
cuando corresponda. No cambies la versión del paquete en un PR de feature.

Antes de solicitar revisión, ejecuta:

```bash
pytest -q
ruff check .
mypy
```

El equipo prepara la versión, el tag y PyPI mediante un PR de release separado.
Después publica el análisis reproducible y la divulgación del ciclo. Daniel y
Jesús registran su aprobación de ambos resultados antes de iniciar otra
funcionalidad.
