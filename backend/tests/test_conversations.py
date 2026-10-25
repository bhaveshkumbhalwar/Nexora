from unittest.mock import patch


def test_conversation_lifecycle(client):
    with patch("app.api.routes.chat.chat_completion", return_value="answer"):
        r = client.post("/api/chat", json={"message": "first question"})
        assert r.status_code == 200
        cid = r.json()["conversation_id"]

    r = client.get("/api/conversations")
    assert r.status_code == 200
    assert any(c["id"] == cid for c in r.json())

    r = client.get(f"/api/conversations/{cid}")
    assert r.status_code == 200
    assert len(r.json()["messages"]) == 2

    r = client.patch(f"/api/conversations/{cid}", json={"title": "Renamed"})
    assert r.status_code == 200
    assert r.json()["title"] == "Renamed"

    r = client.delete(f"/api/conversations/{cid}")
    assert r.status_code == 204

    r = client.get(f"/api/conversations/{cid}")
    assert r.status_code == 404


def test_context_passed(client):
    with patch("app.api.routes.chat.chat_completion", return_value="first") as m:
        r = client.post("/api/chat", json={"message": "What is BERT?"})
        cid = r.json()["conversation_id"]
    with patch("app.api.routes.chat.chat_completion", return_value="second") as m2:
        r = client.post("/api/chat", json={"conversation_id": cid, "message": "How is it different from GPT?"})
        assert r.status_code == 200
        # verify second call received prior context
        args = m2.call_args
        msgs = args.args[0] if args.args else args.kwargs.get("messages")
        # chat_completion called with messages list
        assert any("BERT" in (msg.get("content", "") if isinstance(msg, dict) else str(msg)) for msg in msgs)
