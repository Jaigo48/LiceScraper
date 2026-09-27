# Intent-Trigger Lead Engine

A lightweight Python CLI that analyzes public restaurant-operator discussions for POS-related buying signals, identifies operational pain points, and generates personalized outreach drafts.

The project is designed as an offline-first portfolio demonstration. It can run with zero API keys and zero paid services.

## What it does

The pipeline takes restaurant operator posts and:

1. Detects POS migration intent.
2. Classifies intent as High, Medium, or Low.
3. Assigns a confidence score.
4. Extracts operational pain points.
5. Generates personalized outreach copy.
6. Exports structured CSV and JSON lead data.

## Architecture

```text
Restaurant posts
       |
       v
   scraper.py
       |
       v
 Enrichment Engine
       |
       +-------------------+
       |                   |
       v                   v
   Mock Engine        Gemini API
   (offline)           (optional)
       |                   |
       +---------+---------+
                 |
                 v
          Structured leads
                 |
          +------+------+
          |             |
          v             v
        CSV           JSON
ls
ls
cat > .gitignore <<'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class

# Virtual environments
.venv/
venv/
env/

# Environment secrets
.env

# macOS
.DS_Store

# Generated output
output_leads.csv
output_leads.json

# Local backups
*_backup.py
*_working.py
