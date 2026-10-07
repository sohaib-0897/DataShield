from flask import Flask, request
import os

from sensitivity import calculate_hash, build_sensitive_hashes
from database import initialize_database, log_transfer


app = Flask(__name__)

UPLOAD_FOLDER = "test_uploads"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# Build fingerprints of known sensitive files
SENSITIVE_HASHES = build_sensitive_hashes()


@app.route("/")
def home():
    return """
    <html>
        <body>
            <h2>AI-DLP Upload Test Server</h2>

            <form method="POST" enctype="multipart/form-data"
                  action="/upload">

                <input type="file" name="file">

                <button type="submit">
                    Upload
                </button>

            </form>
        </body>
    </html>
    """


@app.route("/upload", methods=["POST"])
def upload():

    uploaded_file = request.files.get("file")

    if not uploaded_file:
        return "No file selected", 400

    destination = os.path.join(
        UPLOAD_FOLDER,
        uploaded_file.filename
    )

    uploaded_file.save(destination)

    # Calculate SHA-256 of uploaded file
    file_hash = calculate_hash(destination)

    match = SENSITIVE_HASHES.get(file_hash)

    if match:

        source_path = match["source_path"]
        sensitivity = match["sensitivity"]

        print()
        print("===================================")
        print("[SENSITIVE FILE UPLOAD]")
        print("===================================")
        print(f"Source:      {source_path}")
        print(f"Destination: LOCAL_TEST_SERVER")
        print(f"Sensitivity: {sensitivity}")
        print(f"SHA-256:     {file_hash}")
        print("===================================")

        log_transfer(
            event_type="SENSITIVE_UPLOAD",
            source_path=source_path,
            destination_path="LOCAL_TEST_SERVER",
            sensitivity=sensitivity,
            destination_type="UPLOAD",
            file_hash=file_hash
        )

    else:

        print()
        print("===================================")
        print("[NORMAL FILE UPLOAD]")
        print("===================================")
        print(f"File:   {uploaded_file.filename}")
        print(f"SHA-256: {file_hash}")
        print("===================================")

    return "Upload successful!"


if __name__ == "__main__":

    initialize_database()

    print("===================================")
    print("       AI-DLP UPLOAD SERVER")
    print("===================================")

    print(
        f"Sensitive fingerprints loaded: "
        f"{len(SENSITIVE_HASHES)}"
    )

    print("Server: http://127.0.0.1:5000")
    print("===================================")

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )