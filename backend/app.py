from flask import Flask, request, jsonify, render_template
import os
from dotenv import load_dotenv
from openai import OpenAI  
from huggingface_hub import InferenceClient

# Load .env variables
load_dotenv()

app = Flask(__name__)

client = InferenceClient(
    provider="featherless-ai",
    api_key=os.environ["HF_TOKEN"],
)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_msg = request.json.get("message", "")

    try:
        chat_completion = client.chat.completions.create(
            model="mistralai/Mistral-7B-Instruct-v0.2",
            messages=[
                {
                    "role": "system",
                    "content": "You are a friendly and helpful AI assistant. Respond to the user's request concisely."
                },
                {
                    "role": "user",
                    "content": user_msg
                }
            ],
        )
        reply = chat_completion.choices[0].message.content
        
        return jsonify({"reply": reply})

    except Exception as e:
        print(f"An error occurred: {e}") # Good for debugging
        return jsonify({"reply": f"Error: {e}"}), 500

if __name__ == "__main__":
    app.run(debug=True)