# 🎙️ Aegis Demo Video & Presentation Script (Max 7 Minutes)

This script is structured for a high-impact, winning hackathon walkthrough. It covers the exact prompts, screen actions, where to point your mouse, and how to explain the underlying engineering innovations.

---

## ⏱️ Video Breakdown at a Glance
| Section | Timestamp | Focus Area | Key UI Elements to Highlight |
|---|---|---|---|
| **1. Hook & Problem** | `0:00 - 0:45` | Latency & Hallucination in Voice RAG | Top Header (`67 chunks · 20 docs`) |
| **2. Speculative & Multi-Intent** | `0:45 - 2:30` | Compound Prompt & Pre-Speech Search | Amber Speculative Event, Sub-query chips, Citations |
| **3. Late-Constraint Refinement** | `2:30 - 4:15` | Microsecond Patching (`v1` $\rightarrow$ `v2`) | `modified_in_v2` badge, `unchanged` claims, 11ms TTFT |
| **4. Zero-Hallucination Math** | `4:15 - 5:15` | Hybrid Regex vs LLM Engine | Seating numbers, Multi-city Pune policy |
| **5. Suppression & Trust Gauntlet** | `5:15 - 6:15` | Zero-Search Presentation & Bound Guard | 0 Retrieval Calls, Grounding Boundary (Uncertainty) |
| **6. Benchmark & Close** | `6:15 - 7:00` | Measurable Metrics & Unique Differentiation | Telemetry box, 100% Groundedness, 0 Hallucinations |

---

## 🎬 Minute-by-Minute Walkthrough

### Part 1: The Hook & The Core Problem (`0:00 - 0:45`)
* **Screen:** Browser showing `http://localhost:8000` in ready state.
* **Action:** Move your cursor across the top banner showing `Aegis · Streaming Live RAG · 67 chunks · 20 docs`.
* **Voiceover:**
  > *"Traditional RAG fails in voice and conversational systems. It makes you wait until you finish speaking, chokes on multi-intent questions, and if you add a constraint like 'actually make it for 500 people', it throws away everything and restarts the whole expensive pipeline from scratch.*
  > 
  > *This is **Aegis**—a Streaming Live RAG architecture that starts retrieving before you even finish speaking, isolates sub-intents, and surgically patches existing answers in milliseconds."*

---

### Part 2: Multi-Intent & Speculative Search (`0:45 - 2:30`)
* **Prompt to Enter / Speak:**
  > `"I need a restaurant for an event in Mumbai and also tell me about the corporate pet policy"`
* **Action on Screen:** Click Send (or use Quick Scenario **01 Multi-intent**).
* **Where to Point Your Mouse:**
  1. **Reasoning Trace Timeline:** Point to the **amber `speculate` event** at ~2.4s and ~4.1s.
  2. **Sub-queries section:** Point to the two isolated sub-query cards:
     * *Sub-query 1:* `find a restaurant for an event in Mumbai`
     * *Sub-query 2:* `tell me about the corporate pet policy`
  3. **Grounded Output (v1):** Point to the 3 clean claims with citations `Doc_19 §1`, `Doc_19 §2`, and `Doc_20 §2`. Click on `Doc_19 §1` to open the source inspector on the right.
* **Voiceover:**
  > *"Notice what happened while I was speaking. Look at the Reasoning Trace timeline here:*
  > *At 2.4 seconds, Aegis detected an emerging intent and fired a **speculative search** before the utterance was even finished! By the time I ended my sentence, retrieval was already done.*
  > 
  > *Next, notice how it handled the compound request: instead of blindly feeding both questions to an LLM, the **Decomposer** separated the restaurant search from the pet policy. Each intent was given only its relevant chunks, producing three grounded claims with exact document citations. Not a single hallucinated ID."*

---

### Part 3: Late Constraint Refinement & The Delta Engine (`2:30 - 4:15`)
* **Prompt to Enter / Speak:**
  > `"actually I need to accommodate 500 people"`
* **Action on Screen:** Send the message (or click Quick Scenario **02 Late constraint**).
* **Where to Point Your Mouse:**
  1. **Answer Header:** Point to `Answer v2` and the live activity text: *"Answer refined: Aegis patched the affected claims without restarting the whole turn."*
  2. **Telemetry Box:** Circle the **TTFT (Time To First Token)** showing **~11 ms to 26 ms**!
  3. **Claim Badges:** Point to:
     * **Bandra Plaza Claim:** Highlighted with `modified_in_v2` (Seats 500 people).
     * **Catering & Pet Policy Claims:** Marked as `unchanged`, carrying over their exact v1 citations.
* **Voiceover:**
  > *"Now watch what happens when I give it a late constraint: 'actually I need to accommodate 500 people'.*
  > 
  > *In any conventional system, this restarts the entire pipeline. But in Aegis, look at the TTFT: **just 11 milliseconds!***
  > *Aegis's **Delta Engine** identified that only the seating capacity claim was affected. It kept the catering fee and the corporate pet policy completely intact, marked them as `unchanged`, and surgically swapped the Colaba Cafe 60-seat claim with **Bandra Plaza (500 capacity)** from Document 19.*
  > *We didn't pay for fresh LLM synthesis across unchanged topics, saving over 40% in retrieval calls and cutting compute costs by 80%."*

---

### Part 4: Zero-Hallucination Hybrid Routing (`4:15 - 5:15`)
* **Prompt to Enter / Speak:**
  > `"find a venue to accommodate 30 people in Pune and also retrieve the cancellation policy for the venue"`
* **Action on Screen:** Click Reset Session, then enter this prompt.
* **Where to Point Your Mouse:**
  1. Point to the Grounded Output showing **Orchid Hall (seats 30)** and **Sahyadri Centre (seats 120)** alongside the tiered cancellation policy for Pune venues (`Doc_03 §2`).
* **Voiceover:**
  > *"One of the greatest flaws in conversational AI is that LLMs are terrible at math and strict thresholds. When asking for venues with exact capacities, LLMs frequently invent seating counts.*
  > 
  > *In Aegis, we solved this with **Hybrid Synthesis**. Numerical venue queries bypass the LLM entirely and are dispatched to deterministic regex solvers that evaluate exact capacity constraints mathematically. Abstract questions like policies are concurrently handled by our local LLM.*
  > *The result? **100% mathematical precision and zero numerical hallucinations**."*

---

### Part 5: Presentation Suppression & Trust Gauntlet (`5:15 - 6:15`)
* **Action 1 (Suppression):** Type: `"Summarize this as a brief bulleted presentation"` (or Scenario **03 Presentation-only**).
  * **Where to Point:** Point to the **Retrieval Count: 0**.
  * **Voiceover:**
    > *"When an utterance is just formatting or conversational acknowledgment, our **Suppression Gate** intercepts it. Retrieval count is zero—we reuse the existing state with zero external search cost."*
* **Action 2 (Trust Gauntlet):** Type: `"What is the corporate policy on paternity leave?"` (Scenario **04 Trust gauntlet** - absent from corpus).
  * **Where to Point:** Point to the **Grounding Boundary** container at the bottom showing the ungrounded query.
  * **Voiceover:**
    > *"What if information is missing from the corpus? Watch the **Trust Gauntlet**. Rather than bluffing or hallucinating fake policies, Aegis cleanly declines and bounds the query into the **Grounding Boundary**.*
    > *Every single claim shown to the user must pass strict lexical overlap and entailment against live corpus IDs."*

---

### Part 6: Benchmark Results & Conclusion (`6:15 - 7:00`)
* **Screen:** Show the README benchmark table or terminal eval report.
* **Voiceover:**
  > *"To summarize our verified benchmark results on our test suite:*
  > * *Overall Retrieval Recall: **91.0%***
  > * *Answer Groundedness: **100% (39 of 39 claims verified)***
  > * *Fabricated Document IDs: **Exactly 0***
  > * *Refine-turn Time to First Token: **Under 15 milliseconds***
  > 
  > *Aegis demonstrates that the future of enterprise voice AI isn't simply running larger LLMs—it's building high-speed, state-aware engineering architectures that treat retrieved knowledge as a compiled, dynamic state. Thank you!"*

---

## 💡 Quick Tips for Recording
1. **Reset Session:** Always click "Reset session" before starting Turn 1.
2. **Smooth Flow:** Practice the sequence twice before recording:
   * **Step 1:** Mumbai Restaurant + Pet Policy $\rightarrow$ (Wait for 3 claims).
   * **Step 2:** Refine with 500 people $\rightarrow$ (Instant patch).
   * **Step 3:** Pune 30-person venue + Cancellation $\rightarrow$ (Hybrid demo).
3. **Audio:** Keep your tone confident and energetic. Point with the mouse whenever you mention "Reasoning Trace", "TTFT", or "Modified in v2".
