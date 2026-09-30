import os

docs_dir = r"A:\Aegis_Fixed_Clean_Release_v2\aegis\aegis\corpus\docs"

# 1. Update Pune Venues (Doc_01)
doc_01 = '''# Venue Directory - Pune Region

## Capacity and Layout
The Pune region has four approved venues. Orchid Hall seats 30 people in boardroom layout and 45 in theatre layout, making it the default choice for mid-size offsites. Riverside Studio seats 18 people and is intended for workshops. Sahyadri Conference Centre seats 120 in theatre layout and 60 in banquet rounds. Baner Annexe seats 25 and has no dedicated catering kitchen.

## Booking Windows
Orchid Hall and Riverside Studio accept bookings up to 90 days in advance. Sahyadri Conference Centre requires a minimum of 14 days notice for any booking involving more than 50 attendees. 

## Equipment Included
All four venues include a projector, two wireless microphones, and whiteboards in the base rate.
'''
with open(os.path.join(docs_dir, 'Doc_01.md'), 'w', encoding='utf-8') as f: f.write(doc_01)

# 2. Update Bangalore Venues (Doc_02)
doc_02 = '''# Venue Directory - Bangalore Region

## Capacity and Layout
Indiranagar Loft seats 35 people in boardroom layout. Whitefield Pavilion seats 200 in theatre layout and is the only venue in the Bangalore region licensed for external guests. Koramangala Studio seats 20 and is workshop-oriented.

## Booking Windows
Whitefield Pavilion requires 21 days notice for external-guest events because of the visitor security screening process. Indiranagar Loft accepts bookings up to 60 days ahead.

## Regional Rate Differences
Bangalore venue rates run roughly 15 percent higher than equivalent Pune venues.
'''
with open(os.path.join(docs_dir, 'Doc_02.md'), 'w', encoding='utf-8') as f: f.write(doc_02)

# 3. Add Mumbai Region & Restaurant (Doc_19)
doc_19 = '''# Venue Directory - Mumbai Region

## Capacity and Layout
The Mumbai region has three approved venues. Bandra Plaza seats 500 people in a grand theatre layout, ideal for company-wide town halls. Colaba Cafe is a dedicated corporate restaurant in Mumbai that seats 60 people for team dinners. Andheri Boardroom seats 15 people for executive meetings.

## Outside Catering Policy
For Bandra Plaza and Andheri Boardroom, all food must be ordered through the internal corporate cafeteria. However, the Colaba Cafe restaurant allows outside catering subject to a 5000 INR hygiene inspection fee. 

## Booking Windows
Bandra Plaza requires 45 days advance notice due to fire-safety permit requirements for large gatherings.
'''
with open(os.path.join(docs_dir, 'Doc_19.md'), 'w', encoding='utf-8') as f: f.write(doc_19)

# 4. Add Pet Policy (Doc_20)
doc_20 = '''# Corporate Pet Policy

## Standard Rules for Venues
For hygiene and allergy reasons, pets are strictly prohibited inside all corporate venues and restaurants in Pune, Bangalore, and Mumbai. 

## Service Animals
Certified service animals are the only exception to the pet policy. Employees bringing a service animal must notify the venue manager at least 48 hours prior to the event to ensure appropriate seating arrangements are made.
'''
with open(os.path.join(docs_dir, 'Doc_20.md'), 'w', encoding='utf-8') as f: f.write(doc_20)

print("Corpus updated successfully.")
