from flask import Flask, request, jsonify, render_template
import os
from dotenv import load_dotenv
from openai import OpenAI

# Load .env variables
load_dotenv()

app = Flask(__name__)

# --- CORRECTED CLIENT INITIALIZATION ---
# Get the key and base_url from your .env file
api_key = os.environ.get("PROXY_API_KEY")
base_url = os.environ.get("PROXY_BASE_URL")

# Configure the OpenAI client to point to the third-party service
client = OpenAI(
    api_key=api_key,
    base_url=base_url
)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_msg = request.json.get("message", "")

    try:
        # The API call itself does not change, just the client config
        # You can use the models mentioned in the image
        chat_completion = client.chat.completions.create(
            model="gpt-3.5-turbo", # This model is listed as supported
            messages=[
                {
                    "role": "system",
                    "content": "You are a friendly and helpful AI assistant."
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
        print(f"An error occurred: {e}")
        return jsonify({"reply": f"Error: {e}"}), 500

if __name__ == "__main__":
    app.run(debug=True)