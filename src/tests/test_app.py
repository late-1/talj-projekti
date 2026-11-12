from src.app import app


def test_homepage_displays_expected_sentence():
    response = app.test_client().get("/")

    assert response.status_code == 200
    assert response.get_data(as_text=True).strip() == "HELLO WORLD AND GOODBYE"
