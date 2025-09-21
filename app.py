from flask import Flask, request, jsonify, render_template
import os
from dotenv import load_dotenv
from openai import OpenAI

from backend.scripts.rag_handler import create_system_prompt

load_dotenv()

app = Flask(__name__)

# --- API SETUP ---
api_key = os.environ["HF_TOKEN"]
base_url = os.environ["BASE_URL"]
model_name = "meta-llama/Llama-3.1-8B-Instruct:nebius"

client = OpenAI(api_key=api_key, base_url=base_url)


# --- FLASK ROUTES ---

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_msg = request.json.get("message", "")
    if not user_msg:
        return jsonify({"reply": "Please provide a message."}), 400

    # Step 1: Get the dynamically created system prompt from your module
    system_prompt = create_system_prompt(user_msg)

    # Step 2: Call the LLM with the new prompt
    try:
        chat_completion = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg}
            ],
        )
        reply = chat_completion.choices[0].message.content
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"reply": f"An error occurred with the AI model: {e}"}), 500

    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(debug=True)