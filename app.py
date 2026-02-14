import os
import datetime
import secrets
from flask import Flask, request, render_template, jsonify
from werkzeug.utils import secure_filename

# --------------------------------------------------
# Configuration – edit these values before running
# --------------------------------------------------
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}

# ---- Email config (SMTP) ------------------------
SMTP_SERVER = 'smtp.gmail.com'      # Gmail
SMTP_PORT = 587
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
EMAIL_FROM = SMTP_USER
EMAIL_TO = os.environ.get("EMAIL_TO")
EMAIL_SUBJECT = 'Auto‑captured photo'
print("SMTP_USER =", SMTP_USER)
print("SMTP_PASSWORD length =", len(SMTP_PASSWORD) if SMTP_PASSWORD else None)
print("EMAIL_TO =", EMAIL_TO)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --------------------------------------------------
# Helpers
# --------------------------------------------------
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --------------------------------------------------
# Routes
# --------------------------------------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send-email', methods=['POST'])
def send_email():
    """
    Expects multipart/form-data with field 'photo' (binary image).
    Saves the image locally, then (optionally) emails it.
    """
    print(">>> send_email() called")
    if 'photo' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['photo']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        # Secure the filename
        filename = secure_filename(file.filename)
        # Unique name – avoids overwriting
        unique_id = secrets.token_hex(8)
        timestamp = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
        filename = f"{timestamp}_{unique_id}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # Save locally
        file.save(filepath)

        # --------------------------------------------------
        # ------------- OPTIONAL: Send via email -----------
        # --------------------------------------------------
        try:
            import smtplib
            from email.message import EmailMessage

            msg = EmailMessage()
            msg['Subject'] = EMAIL_SUBJECT
            msg['From'] = EMAIL_FROM
            msg['To'] = EMAIL_TO
            msg.set_content('Here is the photo you requested.')

            # Attach the image
            with open(filepath, 'rb') as img_file:
                img_data = img_file.read()
                msg.add_attachment(img_data, maintype='image',
                                   subtype=filename.rsplit('.', 1)[1],
                                   filename=filename)

            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                print("Sending email now...")
                server.ehlo()
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)

            print(f"[+] Email sent to {EMAIL_TO} – {filename}")
            print("[+] Email sent successfully")

        except Exception as e:
            print(f"[-] Failed to send email: {e}")
            import traceback
            traceback.print_exc()

        # --------------------------------------------------
        # Response
        # --------------------------------------------------
        return jsonify({'success': True, 'saved_as': filename}), 200

    else:
        return jsonify({'error': 'File type not allowed'}), 400

# --------------------------------------------------
# Main
# --------------------------------------------------
if __name__ == '__main__':
    # Make sure the upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Run locally
    # app.run(host='127.0.0.1', port=5000, debug=False)
app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

