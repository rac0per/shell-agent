from flask import Flask, jsonify, request


MOCK_RESPONSES = {
    "list all files in current directory": "ls",
    "show hidden files too": "ls -la",
    "delete a file named test.txt": "rm test.txt",
    "create a new directory": "mkdir new_directory",
    "check disk usage": "df -h",
}


def create_app():
    app = Flask(__name__)

    @app.route("/generate", methods=["POST"])
    def generate():
        data = request.json or {}
        prompt = data.get("prompt", "")

        if not prompt:
            return jsonify({"error": "prompt is required"}), 400

        response = "echo 'Command not found'"
        for key, cmd in MOCK_RESPONSES.items():
            if key.lower() in prompt.lower():
                response = cmd
                break

        return jsonify({"response": response})

    return app


def test_mock_server_generate_success():
    app = create_app()
    client = app.test_client()

    resp = client.post("/generate", json={"prompt": "please list all files in current directory"})

    assert resp.status_code == 200
    assert resp.get_json()["response"] == "ls"


def test_mock_server_generate_missing_prompt():
    app = create_app()
    client = app.test_client()

    resp = client.post("/generate", json={})

    assert resp.status_code == 400
    assert "prompt is required" in resp.get_json()["error"]


def test_mock_server_generate_fallback_response():
    app = create_app()
    client = app.test_client()

    resp = client.post("/generate", json={"prompt": "unknown request"})

    assert resp.status_code == 200
    assert resp.get_json()["response"] == "echo 'Command not found'"
