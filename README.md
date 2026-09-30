# 🛡️ Aegis — A Streaming Live RAG Engine

**Theme: Streaming Live RAG 04 · PRISM_GENAI_HACKATHON_Y2026**

Aegis is an ultra-low latency, conversational Retrieval-Augmented Generation (RAG) engine designed for real-time voice and streaming interfaces. It starts retrieving **before the user finishes speaking**, splits compound queries into discrete sub-intents, fuses grounded evidence, and **patches existing answers with late constraints instead of restarting the entire pipeline**.

---

## 📌 Submission Deliverables & Links

* **Hackathon Release Tag:** PRISM_GENAI_HACKATHON_Y2026
* **Demo Video Link (GDrive):** *[Click here to watch the Demo Video](https://drive.google.com/file/d/11YE5tzn1XtS09P18pabqhoy7KuI7gPUi/view?usp=sharing)*
* **Presentation (PPT):** Included in repository: *[Click here for PPT]([https://drive.google.com/file/d/11YE5tzn1XtS09P18pabqhoy7KuI7gPUi/view?usp=sharing](https://docs.google.com/presentation/d/1cOkf3m1hIk4gn8sUGFUrRhid28ryyhtb/edit?usp=sharing&ouid=105587751018171349077&rtpof=true&sd=true))*
* **Architecture & Benchmark Report:** Documented below and in [eval/report.md](eval/report.md)

---

## ⚡ Quick Start

### Option A — Docker (One Command)
`ash
docker compose up --build
`
Open **<http://localhost:8000>**.

### Option B — Local Setup (Python 3.10+)
`ash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux / macOS:
source .venv/bin/activate

pip install -r requirements.txt
python -m corpus.build_index
uvicorn backend.main:app --reload
`
Open **<http://localhost:8000>**.

### Local LLM Mode (Ollama)
`ash
# Optional: Run local Llama 3.1 8B or Qwen
ollama run llama3.1:8b

# Environment variable (optional, defaults to local detection):
="ollama"    # Windows PowerShell
set AEGIS_LLM_PROVIDER=ollama       # Windows CMD
export AEGIS_LLM_PROVIDER=ollama    # macOS/Linux
`
*Note: If Ollama is not running, Aegis automatically falls back to deterministic heuristic parsing without failing.*

---

## 🏆 Benchmark & Evaluation Results

| Metric | Aegis | Naive Baseline | Target | Status |
|---|---|---|---|---|
| **Retrieval recall (overall)** | **91.0%** | 91.7% | ≥80% | **PASS** |
| — single-intent | 100.0% | 100.0% | — | **PASS** |
| — multi-intent | 78.8% | 80.3% | — | In range |
| **Answer groundedness** | **100% (39/39 claims)** | — | ≥85% | **PASS** |
| **Fabricated document IDs** | **0** | — | exactly 0 | **PASS** |
| **Median TTFT (Refine Turn)** | **11.2 ms** | 122.15 ms | below baseline | **PASS** |
| **Refine-turn retrieval reduction** | **42.9%** | n/a (no refine path) | >0 | **PASS** |
| **Trust Gauntlet (adversarial)** | **4/4 passed** | — | — | **PASS** |

---

## 🏗️ System Architecture

`mermaid
flowchart TD
    classDef user fill:#2C3E50,stroke:#34495E,stroke-width:2px,color:#fff
    classDef core fill:#2980B9,stroke:#2471A3,stroke-width:2px,color:#fff
    classDef retrieve fill:#27AE60,stroke:#1E8449,stroke-width:2px,color:#fff
    classDef synth fill:#8E44AD,stroke:#7D3C98,stroke-width:2px,color:#fff
    classDef output fill:#E67E22,stroke:#D35400,stroke-width:2px,color:#fff
    classDef db fill:#7F8C8D,stroke:#707B7C,stroke-width:2px,color:#fff

    User((User Voice Input)):::user
    
    subgraph Controller [Real-Time Controller]
        Buffer[Audio/Text Buffer]:::core
        Spec[Speculative Trigger]:::core
    end
    
    subgraph RetrievalLayer [Retrieval Engine]
        Prov[Provisional Search]:::retrieve
        Decomp[Decomposer Multi-Intent Splitter]:::retrieve
        Final[Final Parallel Retrieval]:::retrieve
        VDB[(Enterprise Corpus)]:::db
    end

    subgraph SynthesisLayer [Hybrid Synthesis]
        Route{Intent Router}:::synth
        Det[Deterministic Solver Regex/Math]:::synth
        LLM[LLM Engine Llama 3.1 8B]:::synth
        Patch[Delta Engine Patch Refinement]:::synth
        Gauntlet[Trust Gauntlet Anti-Hallucination]:::synth
    end

    OutDraft[Stateful Claim Drafts]:::output
    OutFinal((UI Output: Claims and Grounding Boundary)):::output

    User --> Buffer
    Buffer -- "Mid-sentence (2.7s)" --> Spec
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
`

### Core Architecture Components

| Module | Role |
|---|---|
| ackend/controller.py | Streaming controller, silence detection, drift gate, and speculative dispatch |
| ackend/decomposer.py | Sub-query decomposition, orthogonality guard, and refine-turn classifier |
| ackend/retrieval/ | Hybrid retrieval: Sparse BM25 + Dense vector search + Reciprocal Rank Fusion (RRF) |
| ackend/synthesis.py | Hybrid synthesis (Deterministic math solver + LLM), Delta Engine patcher, and Trust Gauntlet |
| ackend/suppression.py | Presentation-only query gate (zero-search cache reuse) |
| ackend/pipeline.py | Core orchestration pipeline with WebSocket streaming |
| rontend/ | Real-time text-delta client, telemetry trace, latency timers, and source inspector |

---

## 🌟 Key Innovations & Differentiators

1. **Speculative Provisional Retrieval:** Aegis retrieves candidate chunks while the speaker is mid-utterance, cutting conversational latency to near zero.
2. **Hybrid Synthesis (0% Math Hallucination):** Numerical and capacity constraints bypass the LLM and are resolved by deterministic solvers, guaranteeing 100% precision on venue seating, rates, and thresholds.
3. **Stateful Delta Refinement:** When constraints change (*"Actually make it 500 people"*), Aegis performs a semantic diff and patches *only* the affected claim in under 15ms without restarting the turn.
4. **Trust Gauntlet & Grounding Boundary:** Strict lexical and entailment checks prevent out-of-corpus hallucinations. Unanswerable components are cleanly isolated into the Grounding Boundary UI.

---

## 🛠️ Tech Stack & Requirements

* **Language:** Python 3.10+
* **Backend:** FastAPI, Uvicorn, WebSockets, Asyncio
* **Data & Models:** Local NumPy vector indices, BM25, Ollama (Llama 3.1 8B / Qwen)
* **Frontend:** Vanilla JavaScript, HTML5 WebSocket UI, Realtime CSS Audio Waveform
* **DevOps:** Docker, Docker Compose

---

## 📋 Hackathon Submission Checklist

- [x] Working code with clean repository structure
- [x] Minimal dependency manifest (
equirements.txt)
- [x] Comprehensive architectural README.md
- [x] Verification and test suite (pytest -q, eval/run_eval.py)
- [ ] Add your presentation PPT file (.pptx) in root folder
- [ ] Add your demo video or YouTube/Drive link in README.md
- [ ] Create GitHub Release Tag: PRISM_GENAI_HACKATHON_Y2026
