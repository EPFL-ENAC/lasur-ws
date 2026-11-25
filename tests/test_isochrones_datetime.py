import pytest
from pydantic import ValidationError
from api.models.isochrones import IsochronePoisData


def test_datetime_validation():
    def make(value):
        return IsochronePoisData(lon=6.1, lat=46.2, cutoffSec=[600], datetime=value)

    for value in ("2026-11-25T08:00:00", "2026-11-25T08:00:00Z", "2026-11-25T08:00:00+01:00"):
        assert make(value).datetime == value
    for value in ("", "tomorrow", "2026-13-01T08:00:00"):
        with pytest.raises(ValidationError):
            make(value)
