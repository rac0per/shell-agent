"""
Mock model server for testing without loading the full model
"""
from flask import Flask, request, jsonify

app = Flask(__name__)

# Predefined responses for testing
MOCK_RESPONSES = {
    "list all files in current directory": "ls",
    "show hidden files too": "ls -la",
    "delete a file named test.txt": "rm test.txt",
    "create a new directory": "mkdir new_directory",
    "check disk usage": "df -h",
}

@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    prompt = data.get("prompt", "")
    
    if not prompt:
        return jsonify({"error": "prompt is required"}), 400
    
    # Simple mock logic: look for keywords in prompt
    response = "echo 'Command not found'"
    
    for key, cmd in MOCK_RESPONSES.items():
        if key.lower() in prompt.lower():
            response = cmd
            break
    
    return jsonify({"response": response})

if __name__ == "__main__":
    print("=" * 60)
    print("Mock Model Server Starting")
    print("=" * 60)
    print("This is a lightweight mock server for testing purposes.")
    print("It returns predefined shell commands without loading the model.")
    print("Server running at: http://127.0.0.1:8000")
    print("=" * 60)
    app.run(host="127.0.0.1", port=8000)
