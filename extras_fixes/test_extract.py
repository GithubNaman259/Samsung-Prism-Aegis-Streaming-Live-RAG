from aegis.backend.synthesis import _extract_venue_claim
from aegis.backend.retrieval.engine import ScoredChunk
from aegis.backend.schemas import Chunk

chunk_text = "The Pune region has four approved venues. Orchid Hall seats 30 people in boardroom layout and 45 in theatre layout, making it the default choice for mid-size offsites. Riverside Studio seats 18 people and is intended for workshops. Sahyadri Conference Centre seats 120 in theatre layout and 60 in banquet rounds. Baner Annexe seats 25 and has no dedicated catering kitchen."
query = "find a venue to accommodate 30 people in Pune"

class MockChunk:
    def __init__(self, text):
        self.text = text

class MockScored:
    def __init__(self, chunk):
        self.chunk = chunk

sc = MockScored(MockChunk(chunk_text))

result = _extract_venue_claim(query, [sc])
print("RESULT:", result)
