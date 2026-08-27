import importlib

from fastapi.testclient import TestClient


def test_service_modules_can_be_imported():
    db_module = importlib.import_module("app.service_db")
    web_module = importlib.import_module("app.service_web")

    assert hasattr(db_module, "app")
    assert hasattr(web_module, "app")
    assert hasattr(db_module.app, "routes")
    assert hasattr(web_module.app, "routes")


def test_service_names_are_normalized_for_linux_services(monkeypatch):
    monkeypatch.setenv("JADUS_SERVICE_NAME", "JadusPanelWeb")

    from app.logger import setup_logging
    logger = setup_logging(app_name="JadusPanelWeb", log_level="INFO")

    assert logger.name == "web"


def test_service_apps_expose_root_routes():
    import app.service_api as service_api
    import app.service_web as service_web

    api_routes = {route.path for route in service_api.app.routes}
    web_routes = {route.path for route in service_web.app.routes}

    assert "/" in api_routes
    assert "/" in web_routes


def test_static_web_pages_are_served():
    import app.service_web as service_web

    client = TestClient(service_web.app)

    assert client.get("/").status_code == 200
    assert client.get("/admin-login.html").status_code == 200
    assert client.get("/css/style.css").status_code == 200
