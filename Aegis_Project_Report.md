# 🛡️ Aegis: Next-Generation Live Streaming RAG

## 1. Project Theme & Vision
**Aegis** is an ultra-low latency, conversational Retrieval-Augmented Generation (RAG) architecture built for real-time voice and streaming interfaces. Designed specifically for complex enterprise environments (corporate policies, venue booking, expense management), Aegis abandons the traditional "wait-and-generate" RAG paradigm. Instead, it introduces **Streaming Live RAG**—a stateful, hybrid intelligence system that begins searching before the user finishes speaking and intelligently patches answers in real-time.

## 2. Existing Solutions & Respective Gaps
Traditional RAG architectures suffer from critical limitations when applied to real-time voice interfaces:
* **High Latency (The TTFT Problem):** Standard systems wait for the `utterance_end` signal, embed the query, retrieve documents, and pass them to an LLM. This creates a 3–5 second delay, making voice interactions feel unnatural.
* **Multi-Intent Collapse:** When users ask compound questions (*"I need a venue and what's the pet policy?"*), naive RAG pulls top-k chunks that dilute the context window, causing the LLM to hallucinate or drop one of the intents entirely.
* **Inefficient Refinement (Late Constraints):** If a user adds a late constraint (*"Actually, make it for 500 people"*), traditional RAG re-runs the entire heavy pipeline from scratch, wasting compute and time.
* **Numeric Hallucinations:** LLMs are inherently bad at mathematical constraints (e.g., strictly filtering venues that seat `>= 500` people). They often hallucinate capacities or merge numbers from unrelated chunks.

## 3. Our Solution & Architecture
Aegis completely reimagines the RAG pipeline by treating the AI as a **stateful claim processor** rather than a stateless text generator. 

### Core Architectural Pillars:
1. **Speculative Provisional Retrieval:** Aegis begins querying the vector database mid-utterance. By the time the user stops speaking, the retrieval is often already complete.
2. **Hybrid Synthesis Engine:** Aegis routes subqueries based on intent. Highly structured constraints (Venue Capacity, Cancellations) bypass the LLM and are routed to deterministic, mathematically proven regex solvers. Abstract queries (Policies) are isolated and sent sequentially to the LLM (Llama 3.1 8B).
3. **The Delta Engine (Late Constraints):** When a user refines an answer, Aegis doesn't start over. It uses a semantic diffing engine to identify *only the affected claim*, retrieves the new constraint, and dynamically "patches" the single claim in milliseconds while preserving the rest of the answer state.

### Architecture Diagram
```mermaid
flowchart TD
    %% Define Node Styles
    classDef user fill:#2C3E50,stroke:#34495E,stroke-width:2px,color:#fff
    classDef core fill:#2980B9,stroke:#2471A3,stroke-width:2px,color:#fff
    classDef retrieve fill:#27AE60,stroke:#1E8449,stroke-width:2px,color:#fff
    classDef synth fill:#8E44AD,stroke:#7D3C98,stroke-width:2px,color:#fff
    classDef output fill:#E67E22,stroke:#D35400,stroke-width:2px,color:#fff
    classDef db fill:#7F8C8D,stroke:#707B7C,stroke-width:2px,color:#fff

    User((🗣️ User Voice\nInput)):::user
    
    subgraph Controller [Real-Time Controller]
        Buffer[Audio/Text Buffer]:::core
        Spec[Speculative Trigger]:::core
    end
    
    subgraph RetrievalLayer [Retrieval Engine]
        Prov[Provisional Search]:::retrieve
        Decomp[Decomposer\n(Multi-Intent Splitter)]:::retrieve
        Final[Final Parallel Retrieval]:::retrieve
        VDB[(Enterprise\nCorpus)]:::db
    end

    subgraph SynthesisLayer [Hybrid Synthesis]
        Route{Intent Router}:::synth
        Det[Deterministic Solver\n(Regex/Math)]:::synth
        LLM[LLM Engine\n(Llama 3.1 8B)]:::synth
        Patch[Delta Engine\n(Patch Refinement)]:::synth
        Gauntlet[Trust Gauntlet\n(Anti-Hallucination)]:::synth
    end

    OutDraft[Stateful Claim Drafts]:::output
    OutFinal((UI Output:\nClaims & Grounding Boundary)):::output

    %% Flow Connections
    User --> Buffer
    Buffer -- "Mid-sentence" --> Spec
    Spec --> Prov
    Prov --> VDB
    
    Buffer -- "Utterance Complete" --> Decomp
    Decomp -- "Subqueries" --> Final
    Final <--> VDB
    
    Prov -. "Reused Cache" .-> Final
    
    Final --> Route
    Route -- "Venue/Math" --> Det
    Route -- "Abstract Policy" --> LLM
    Route -- "Late Constraint" --> Patch
    
    Det --> OutDraft
    LLM --> OutDraft
    Patch --> OutDraft
    
    OutDraft --> Gauntlet
    Gauntlet -- "Pass" --> OutFinal
    Gauntlet -- "Fail/Uncertain" --> OutFinal
```

## 4. Demo and Product Walkthrough
The Aegis platform showcases its superiority through four specific scenarios:

* **Scenario 1: Multi-Intent (Parallel Search)**
  * *Input:* "I need a restaurant for an event in Mumbai and also tell me about the corporate pet policy."
  * *Action:* Aegis decomposes this into two distinct subqueries, fetches evidence independently, processes them (routing the venue mathematically and the policy via LLM), and presents **perfectly isolated claims**.
* **Scenario 2: Late Constraint (Refine Answer)**
  * *Input:* "Actually I need to accommodate 500 people."
  * *Action:* Instead of regenerating the pet policy, Aegis's Delta Engine flags only the capacity claim, triggers a targeted fresh retrieval, and **patches the restaurant claim** to "Bandra Plaza" in sub-20ms TTFT.
* **Scenario 3: Presentation-Only (Reuse Evidence)**
  * *Input:* User makes conversational acknowledgments or asks to "present this".
  * *Action:* Aegis bypasses retrieval entirely via the Suppression Gate, saving compute and responding instantly.
* **Scenario 4: Trust Gauntlet (Grounding Test)**
  * *Action:* Aegis structurally binds every claim to an exact `chunk_id`. The Trust Gauntlet mathematically validates word-overlap and semantic similarity. Hallucinated numbers (e.g., confusing a 5000 INR hygiene fee with a 25000 INR expense limit) are ruthlessly filtered and pushed to the **Grounding Boundary** (Uncertainty UI).

## 5. Tools & Tech Stack
* **Language:** Python (Asyncio)
* **Backend Framework:** FastAPI / Uvicorn (Streaming APIs)
* **LLM Engine:** Llama 3.1 8B (Hosted locally via Ollama)
* **Retrieval / DB:** Custom In-Memory Vector Engine with Chunk Management
* **Embeddings:** Fast local embedding model (Cosine Similarity)
* **NLP & Processing:** Regular Expressions (Regex) for deterministic data extraction, exact token-overlap algorithms.

## 6. Impact & Use Cases
> [!TIP] Immediate ROI
> By reusing unchanged claims during refinement turns, Aegis slashes API costs and compute overhead by up to **80% per refinement**. 

* **Corporate Travel & Event Desks:** instantly querying dynamic capacities, policies, and pricing without hallucinating limits.
* **HR & Compliance:** Employees can ask multi-intent questions ("What's the maternity leave policy and can I expense a monitor?") and get fully grounded, legally safe answers.
* **Customer Support Agents:** Real-time conversational copilot that retrieves answers *while* the customer is still talking on the phone.

## 7. Innovation & Highlight Results
* **Microsecond Patching:** Refine turns execute in as little as **11ms TTFT** (Time-To-First-Token) by skipping full LLM re-generation.
* **Zero-Hallucination Routing:** By routing numeric constraints (venue capacities) to mathematical regex solvers while bypassing the LLM entirely, Aegis achieves **0% hallucination rates** on hard numbers.
* **Isolated LLM Contexts:** Multi-intent queries are executed iteratively. The LLM is only given the evidence belonging to *that specific subquery*, structurally eliminating "cross-contamination" of facts.

## 8. Limitations
* **Hardware Bottlenecks on Local LLMs:** Running concurrent generation streams on small local hardware via Ollama can cause massive latency spikes (e.g., 200+ second TTFTs). Aegis mitigates this by aggressively prioritizing sequential LLM queuing.
* **Sensitivity to Cutoffs:** Because the system leverages speculative retrieval, if a user pauses mid-sentence before a critical noun (e.g., "actually I need to accommodate 500... [pause] ...people"), the speculative search may lock in a flawed context. We built an explicit bypass to ignore speculative results specifically for Refine turns to resolve this.

## 9. What's Next
* **Dynamic Model Routing:** Routing complex reasoning queries to frontier models (e.g., GPT-4o / Claude 3.5 Sonnet) while keeping simple extractions on local edge models (Llama 3.1 8B).
* **Predictive Speculation:** Using small language models (SLMs) to predict the end of the user's sentence and pre-fetch the most likely chunks, compensating for speech pauses.
* **Knowledge Graph Integration:** Expanding the deterministic solver to navigate Graph databases for deeper relationship tracking (e.g., reporting chains and localized policies).

## 10. Differentiation (The "Brownie Points")
Aegis doesn't just pass retrieved text to a Large Language Model and hope for the best. **Aegis treats knowledge as a stateful, compiled object.** 

Most RAG pipelines are stateless chains. Aegis is a state machine. When a user changes their mind, Aegis performs a semantic `diff` of the conversation, surgically removes the outdated claim, and inserts the new one. Furthermore, Aegis recognizes that **LLMs are the wrong tool for math**. By architecting a Hybrid Synthesis engine that uses LLMs for abstract language and deterministic regex for exact capacities, Aegis solves the most notorious flaw in modern AI: confidently hallucinated numbers. 

Aegis proves that the future of AI isn't just bigger models—it's smarter, highly-orchestrated engineering systems surrounding them.
