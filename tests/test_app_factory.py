def test_app_factory_uses_test_config(app):
    assert app.config["TESTING"] is True
    assert app.debug is True
    assert app.import_name == "app"


def test_home_route_returns_200(client):
    response = client.get("/", follow_redirects=True)
    assert response.status_code == 200
    assert b"Tap to Scan Plant" in response.data


def test_login_route_is_accessible(client):
    response = client.get("/login", follow_redirects=True)
    assert response.status_code == 200
    assert b"Login" in response.data
