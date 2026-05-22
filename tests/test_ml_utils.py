from app.services.ml_utils import get_ml_service


def test_get_ml_service_returns_singleton():
    service = get_ml_service()
    assert service is not None
    assert get_ml_service() is service
