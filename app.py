# server.py
from flask import Flask, request, jsonify
import json
from generate_proof import generate_proof 

app = Flask(__name__)

@app.route("/generate-proof", methods=["POST"])
def run_proof_generation():
    try:
        data = request.get_json()
        input_data = data["input"]
        queries = int(data["queries"])
        challenges = json.dumps(data["challenges"])
        proof_data = generate_proof(str(input_data), queries, challenges)
        return jsonify(proof_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
