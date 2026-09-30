"""Replay a transcript as timestamped chunks against a running Aegis server.

Deterministic fallback for demo day: if live mic input misbehaves, this replays
the exact same utterance timeline over the WebSocket, so the demo never depends
on hardware.

    python scripts/transcript_simulator.py --scenario refine
    python scripts/transcript_simulator.py --text "your utterance here"
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SCENARIOS = {
    "fresh": ["I need a venue in Pune for 30 people and I want to know the "
              "cancellation policy and the catering options"],
    "refine": ["I need a venue in Pune for 30 people and I want to know the "
               "cancellation policy",
               "Actually make that 60 people instead"],
    "suppress": ["Tell me the expense submission deadline and the approval chain",
                 "Make that shorter"],
    "gauntlet": ["What is the parental leave policy and how many weeks are paid?"],
}


async def replay(url: str, turns: list[str], chunk_ms: int) -> None:
    try:
        import websockets
    except ImportError:
        print("pip install websockets", file=sys.stderr)
        raise SystemExit(1)

    async with websockets.connect(url) as ws:
        for turn in turns:
            print(f"\n>>> {turn}")
            words = turn.split()
            for i in range(0, len(words), 3):
                await ws.send(json.dumps({
                    "type": "chunk",
                    "text": " ".join(words[i:i + 3]),
                    "t": round(i / 3 * (chunk_ms / 1000), 3),
                }))
                await asyncio.sleep(chunk_ms / 1000)
            await ws.send(json.dumps({"type": "end"}))

            while True:
                msg = json.loads(await ws.recv())
                ev = msg.get("event")
                if ev == "controller_decision":
                    print(f"  [{msg['timestamp_s']:.2f}s] {msg['decision']:<22} {msg['reason']}")
                elif ev == "sub_query_dispatched":
                    print(f"  sub-queries: {msg['sub_queries']}")
                elif ev == "retrieval_suppressed":
                    print(f"  SUPPRESSED: {msg['reason']}")
                elif ev == "turn_result":
                    r = msg["result"]
                    print(f"  answer (v{r['answer_version']}): {r['answer'][:220]}")
                    print(f"  citations: {r['citations']}")
                    if r.get("uncertainty"):
                        print(f"  uncertainty: {r['uncertainty']}")
                    m = r["metrics"]
                    print(f"  TTFT {m['ttft_ms']}ms | calls {m['retrieval_calls']} | "
                          f"refine={m['is_refine_turn']} | ${m['estimated_cost_usd']:.6f}")
                    break
                elif ev == "error":
                    print(f"  ERROR: {msg['detail']}")
                    break


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="localhost:8000")
    ap.add_argument("--session", default="sim")
    ap.add_argument("--scenario", choices=sorted(SCENARIOS), default="refine")
    ap.add_argument("--text", default="")
    ap.add_argument("--chunk-ms", type=int, default=300)
    a = ap.parse_args()
    turns = [a.text] if a.text else SCENARIOS[a.scenario]
    asyncio.run(replay(f"ws://{a.host}/ws/{a.session}", turns, a.chunk_ms))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
