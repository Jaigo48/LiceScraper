import pandas as pd
from pathlib import Path

data = {
    "post_id": ["lead-001", "lead-002"],
    "source": ["custom_csv", "custom_xlsx"],
    "author": ["helsinki_cafe_owner", "espoo_restaurateur"],
    "title": [
        "Switching our POS system ahead of spring",
        "Looking for better POS reporting options"
    ],
    "body": [
        "Our current credit card processing fees are way too high and the terminal keeps freezing.",
        "We need better analytics and lower transaction fees for our second location."
    ],
    "url": ["https://example.com/1", "https://example.com/2"],
    "street_address": ["Aleksanterinkatu 10", "Itätuulenkuja 1"],
    "postal_code": ["00100", "02100"],
    "municipality": ["Helsinki", "Espoo"]
}

df = pd.DataFrame(data)
data_dir = Path("data")
data_dir.mkdir(exist_ok=True)

# Save valid test files
df.to_csv(data_dir / "customleads.csv", index=False)
df.to_excel(data_dir / "prospects.xlsx", index=False, engine="openpyxl")

print("Generated customleads.csv and prospects.xlsx successfully!")
