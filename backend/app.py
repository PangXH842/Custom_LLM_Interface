from flask import Flask, request, jsonify, render_template
import os
from dotenv import load_dotenv
from openai import OpenAI  

# Load .env variables
load_dotenv()

app = Flask(__name__)

# Initialize the OpenAI client to point to Hugging Face's API
client = OpenAI(
    base_url="https://router.huggingface.co/v1/chat/completions", # The new recommended URL
    api_key=os.getenv("HF_TOKEN")
)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_msg = request.json.get("message", "")

    try:
        # The API call is now much cleaner
        chat_completion = client.chat.completions.create(
            # model="mistralai/Mistral-7B-Instruct-v0.2", # Or your desired model
            model = "HuggingFaceH4/zephyr-7b-alpha",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_msg},
            ]
        )
        reply = chat_completion.choices[0].message
        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"reply": f"Error: {e}"}), 500

if __name__ == "__main__":
    app.run(debug=True)