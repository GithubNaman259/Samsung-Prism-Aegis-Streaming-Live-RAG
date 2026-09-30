import os

docs_dir = r"A:\Aegis_Fixed_Clean_Release_v2\aegis\aegis\corpus\docs"

doc_19 = '''# Venue Directory - Mumbai Region

## Capacity and Layout
The Mumbai region has three approved venues. Bandra Plaza seats 500 people in a grand theatre layout, ideal for company-wide town halls. Colaba Cafe is a dedicated corporate restaurant in Mumbai that seats 60 people for team dinners. Andheri Boardroom seats 15 people for executive meetings.

## Outside Catering Policy
For Bandra Plaza and Andheri Boardroom in Mumbai, all food must be ordered through the internal corporate cafeteria. However, the Colaba Cafe restaurant in Mumbai allows outside catering subject to a 5000 INR hygiene inspection fee. 

## Booking Windows
Bandra Plaza requires 45 days advance notice due to fire-safety permit requirements for large gatherings in Mumbai.
'''
with open(os.path.join(docs_dir, 'Doc_19.md'), 'w', encoding='utf-8') as f: f.write(doc_19)

if os.path.exists(r"A:\Aegis_Fixed_Clean_Release_v2\aegis\aegis\corpus\index.json"):
    os.remove(r"A:\Aegis_Fixed_Clean_Release_v2\aegis\aegis\corpus\index.json")

print("Doc_19 updated and index deleted.")
