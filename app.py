import os
import datetime
import secrets
import base64
import requests
from flask import Flask, request, render_template, jsonify
from werkzeug.utils import secure_filename

# -------------------------------
# Basic Configuration
# -------------------------------
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}

# Get Brevo API Key from Render
BREVO_API_KEY = os.environ.get("BREVO_API_KEY")

# ⚠️ IMPORTANT:
# Replace these with your emails
SENDER_EMAIL = "your_verified_sender@gmail.com"
RECEIVER_EMAIL = "receiver@gmail.com"

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# -------------------------------
# Helper Function
# -------------------------------
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# -------------------------------
# Routes
# -------------------------------
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/send-email', methods=['POST'])
def send_email():

    if 'photo' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['photo']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):

        filename = secure_filename(file.filename)
        unique_id = secrets.token_hex(8)
        timestamp = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
        filename = f"{timestamp}_{unique_id}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # Save image
        file.save(filepath)

        try:
            # Convert image to base64
            with open(filepath, "rb") as f:
                encoded_image = base64.b64encode(f.read()).decode()

            url = "https://api.brevo.com/v3/smtp/email"

            headers = {
                "accept": "application/json",
                "api-key": BREVO_API_KEY,
                "content-type": "application/json"
            }

            data = {
                "sender": {"email": SENDER_EMAIL},
                "to": [{"email": RECEIVER_EMAIL}],
                "subject": "Auto-captured photo",
                "htmlContent": "<p>Here is your captured photo.</p>",
                "attachment": [
                    {
                        "content": encoded_image,
                        "name": filename
                    }
                ]
            }

            response = requests.post(url, json=data, headers=headers)

            print("Brevo Response:", response.status_code, response.text)

        except Exception as e:
            print("Brevo Error:", e)

        return jsonify({'success': True}), 200

    return jsonify({'error': 'File type not allowed'}), 400


# -------------------------------
# Run App
# -------------------------------
if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
