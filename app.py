from flask import Flask, request, send_file
from pathlib import Path
import tempfile
import os

from main import run_pipeline, save_csv

app = Flask(__name__)

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".json"}


@app.route("/")
def index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>Lead Enrichment Tool</title>
      <style>
        body { font-family: sans-serif; max-width: 600px; margin: 40px auto; padding: 0 20px; }
        h1 { font-size: 1.5rem; }
        input[type="file"] { margin: 10px 0; }
        button { padding: 8px 16px; cursor: pointer; }
        #status { margin-top: 15px; color: #555; }
      </style>
    </head>
    <body>
      <h1>Lead Enrichment Tool</h1>
      <p>Upload a CSV, XLSX, or JSON file with your leads.</p>
      <form method="POST" enctype="multipart/form-data" action="/process">
        <input type="file" name="file" accept=".csv,.xlsx,.json" required>
        <br>
        <button type="submit">Process</button>
      </form>
      <div id="status"></div>
    </body>
    </html>
    """


@app.route("/process", methods=["POST"])
def process():
    f = request.files.get("file")
    if not f or f.filename == "":
        return "No file uploaded.", 400

    ext = Path(f.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return f"Unsupported file type: {ext}. Use .csv, .xlsx, or .json.", 400

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    tmp.write(f.read())
    tmp.close()

    try:
        leads = run_pipeline("mock", tmp.name)
        csv_path = save_csv(leads)
        return send_file(
            str(csv_path),
            as_attachment=True,
            download_name="enriched_leads.csv",
            mimetype="text/csv",
        )
    except Exception as e:
        return f"Processing error: {str(e)}", 500
    finally:
        os.unlink(tmp.name)


@app.route("/health")
def health():
    return "ok"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))   