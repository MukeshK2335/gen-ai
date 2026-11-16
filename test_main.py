from fastapi.testclient import TestClient
from day3_fast import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok"
    }
def say_hello():
    response = client.get("/hello/John")
    assert response.status_code == 200
    assert response.json() == {
        "msg": "Hello John"
    }
def test_say_hello_invalid_name():
    response = client.get("/hello/abc")
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Name must be at least 4 characters"
    }
from unittest.mock import patch
def test_ask_question(): 
    with patch("day3_fast.ask_question") as mock_ask:     
         mock_ask.return_value = "Binance lost USD 6 billion"
 
         response = client.post(
            "/ask",
            json={
                "nam": "Nalla",
                "quest": "how much did binance loose?"
            }
         )     
         assert response.status_code == 200
         assert response.json()["answer"] == (
            "Binance lost USD 6 billion"
         )


def test_ask_question_llm_failure(): 

    with patch("day3_fast.ask_question") as mock_ask: 

        mock_ask.side_effect = Exception("Gemini API unavailabe")  

        response = client.post(

                    "/ask",

                    json={

                        "nam": "Nalla",

                        "quest": "how much did binance loose?"

                    }

                 ) 

        assert response.status_code == 500

        assert response.json()["detail"] == "Gemini API unavailabe"
    