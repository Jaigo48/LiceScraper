from flask import Flask, request, send_file
from pathlib import Path
import tempfile
import os

from finland.importer import (
    load_finland_licences,
    add_location_key,
    detect_new_locations,
)

app = Flask(__name__)


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
        button { padding: 10px 20px; cursor: pointer; margin: 5px 0; font-size: 1rem; }
        input[type="file"] { margin: 10px 0; }
        .section { border: 1px solid #ddd; border-radius: 8px; padding: 20px; margin-top: 20px; }
      </style>
    </head>
       <body>
      <h1>Lead Enrichment Tool</h1>

      <div class="section">
        <h2>Get Hot Leads</h2>
        <p>New Finnish locations that haven't opened yet. Actively choosing a POS system now.</p>
        <p>Data as of 27.9.2026.</p>
        <form method="POST" action="/hot-leads">
          <button type="submit">Get Hot Leads</button>
        </form>
        <p>Source: <a href="https://avoindata.suomi.fi/data/fi/dataset/alkoholielinkeinorekisteri" target="_blank">Finnish Open Data Portal — Alcohol Licence Register (LVV)</a></p>
      </div>

      <div class="section">
        <h2>Import Updated Data</h2>
        <p>The LVV register is updated periodically by the government. If a newer version has been published, download it from the <a href="https://avoindata.suomi.fi/data/fi/dataset/alkoholielinkeinorekisteri" target="_blank">source</a> and upload it here to get the latest hot leads.</p>
        <form method="POST" enctype="multipart/form-data" action="/import-data">
          <input type="file" name="file" accept=".xlsx" required>
          <br>
          <button type="submit">Import &amp; Get Hot Leads</button>
        </form>
      </div>

      <div class="section">
        <p>A "new location" means the business has never held a licence at that address before, they are opening from scratch with no existing POS system. The opening date tells you when to reach out.</p>
      </div>

            <div class="section">
        <h2>Where This Can Go</h2>
        <p>This tool is built to expand as your pipeline grows:</p>
        <p>Auto-generated outreach emails for each hot lead, ready to copy and send.</p>
        <p>Contact info enrichment: pull email and phone from the Finnish business registry (PRH) automatically.</p>
        <p>Weekly alerts: get notified the moment a new hot lead appears in the register.</p>
        <p>Regional filtering: narrow results to specific municipalities or regions.</p>
        <p>CRM sync: push new leads directly into Pipedrive, Salesforce, or HubSpot.</p>
        <p>Lead tracking: mark leads as contacted, replied, or closed so you never follow up twice.</p>
      </div>   

    </body>   
    </html>
    """


@app.route("/hot-leads", methods=["POST"])
def hot_leads():
    df = load_finland_licences()
    df = add_location_key(df)
    result = detect_new_locations(df)
    result = result[result["signal_type"] == "NEW_LOCATION_UPCOMING"]

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
    tmp.close()
    result.to_excel(tmp.name, index=False)

    return send_file(
        tmp.name,
        as_attachment=True,
        download_name="hot_leads.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@app.route("/import-data", methods=["POST"])
def import_data():
    f = request.files.get("file")
    if not f or f.filename == "":
        return "No file uploaded.", 400

    if not f.filename.lower().endswith(".xlsx"):
        return "Please upload the .xlsx file from the LVV source.", 400

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
    tmp.write(f.read())
    tmp.close()

    try:
        df = load_finland_licences(Path(tmp.name))
        df = add_location_key(df)
        result = detect_new_locations(df)
        result = result[result["signal_type"] == "NEW_LOCATION_UPCOMING"]

        out = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
        out.close()
        result.to_excel(out.name, index=False)

        return send_file(
            out.name,
            as_attachment=True,
            download_name="hot_leads_updated.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    except Exception as e:
        return f"Import error: {str(e)}", 500
    finally:
        os.unlink(tmp.name)


@app.route("/health")
def health():
    return "ok"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))   