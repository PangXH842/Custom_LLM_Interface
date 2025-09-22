# proj/app.py

from flask import Flask, request, jsonify, render_template, session
import os
import uuid # Make sure uuid is imported
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from openai import OpenAI

# Import the UPDATED functions from your RAG script
from backend.scripts.rag_handler import create_system_prompt, index_uploaded_file

load_dotenv()

# --- App Configuration ---
app = Flask(__name__) # Use the default paths for templates and static
app.config['SECRET_KEY'] = os.urandom(24) # Absolutely required for sessions

# Configure the upload folder path correctly
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'backend', 'data', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- API SETUP (no changes) ---
api_key = os.environ.get("HF_TOKEN")
base_url = os.environ.get("BASE_URL")
model_name = "meta-llama/Llama-3.1-8B-Instruct:nebius"
client = OpenAI(api_key=api_key, base_url=base_url)


# --- FLASK ROUTES ---

@app.route("/")
def index():
    # ** THE FIX **: Create a unique 'library card' the moment the user arrives.
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
        print(f"New session created: {session['session_id']}")
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_msg = request.json.get("message", "")
    # ** THE FIX **: Get the user's existing 'library card'
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({"error": "Session not found. Please refresh the page."}), 400

    print(f"Chat request for session: {session_id}") # Good for debugging

    # Pass the session_id to the RAG handler
    system_prompt = create_system_prompt(user_msg, session_id)

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

@app.route('/upload', methods=['POST'])
def upload_file():
    # ** THE FIX **: Get the user's existing 'library card'
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({"error": "Session not found. Please refresh the page."}), 400

    print(f"Upload request for session: {session_id}") # Good for debugging

    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and file.filename.endswith('.txt'):
        filename = secure_filename(f"{session_id}_{file.filename}")
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Pass the session_id to the indexing function
        index_uploaded_file(file_path, session_id)

        return jsonify({"success": f"File '{file.filename}' uploaded and processed."}), 200
    else:
        return jsonify({"error": "Invalid file type, please upload a .txt file"}), 400

if __name__ == "__main__":
    app.run(debug=True, port=5001)