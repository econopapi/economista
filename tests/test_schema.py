import pandas as pd
import pytest

from economista.core.errors import SchemaValidationError
from economista.core.schema import EconSchema


def test_schema_validates_required_columns() -> None:
    schema = EconSchema(required_columns=("geo", "time", "value"))
    frame = pd.DataFrame(
        {
            "geo": ["MEX"],
            "time": [2024],
            "value": [1.0],
        }
    )

    schema.validate(frame)


def test_schema_raises_for_missing_columns() -> None:
    schema = EconSchema(required_columns=("geo", "time", "value"))
    frame = pd.DataFrame({"geo": ["MEX"], "value": [1.0]})

    with pytest.raises(SchemaValidationError):
        schema.validate(frame)
