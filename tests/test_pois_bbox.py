import pytest
from pydantic import ValidationError
from api.models.isochrones import PoisData


def test_bbox_validation():
    PoisData(bbox=[6.1, 46.1, 6.2, 46.3])
    for bbox in ([-180, -90, 180, 90], [6.2, 46.1, 6.1, 46.3], [6.1, 46.1, 6.2], [6.1, 46.1, 200, 46.3]):
        with pytest.raises(ValidationError):
            PoisData(bbox=bbox)


def test_source_validation():
    PoisData(bbox=[6.1, 46.1, 6.2, 46.3], source="geneva")
    with pytest.raises(ValidationError):
        PoisData(bbox=[6.1, 46.1, 6.2, 46.3], source="../../etc")
