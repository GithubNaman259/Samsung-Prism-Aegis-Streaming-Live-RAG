# 🛡️ Aegis --- Streaming Live RAG

**PRISM_GENAI_HACKATHON_Y2026 · Streaming Live RAG**

> **Aegis makes RAG conversational by retrieving before speech ends,
> isolating intents, routing work to the right reasoning mechanism, and
> patching only what changes.**

Aegis is a low-latency, stateful Retrieval-Augmented Generation (RAG)
engine for real-time conversational interfaces.

## 🔖 Final Submission

**Required release tag:**
[`PRISM_GENAI_HACKATHON_Y2026`](../../tree/PRISM_GENAI_HACKATHON_Y2026)

**The tagged commit is the exact version submitted for evaluation.**

### 🔗 Submission Resources

-   🎥 **[Demo Video --- Google
    Drive](https://drive.google.com/file/d/11YE5tzn1XtS09P18pabqhoy7KuI7gPUi/view?usp=sharing)**
-   📊 **[Final Presentation](https://docs.google.com/presentation/d/1cOkf3m1hIk4gn8sUGFUrRhid28ryyhtb/edit?usp=sharing&ouid=105587751018171349077&rtpof=true&sd=true)**
-   🏗️ **[Architecture Diagram](./architecture_diagram.png)**
-   📋 **[Requirements](./requirements.txt)**
-   🐳 **[Dockerfile](./Dockerfile)**
-   🐳 **[Docker Compose](./docker-compose.yml)**

> **Repository note:** Commit the final presentation using the filename
> `Aegis_Final_Presentation.pptx` so the link above opens the PPT
> directly from the repository.

------------------------------------------------------------------------

## 1. Problem

Conventional conversational RAG commonly follows:

``` text
User finishes speaking → Retrieve → Generate → Answer
```

Aegis changes the execution model:

``` text
User starts speaking
        ↓
Speculative retrieval
        ↓
Intent decomposition
        ↓
Parallel evidence retrieval
        ↓
Hybrid synthesis
        ↓
Stateful claims
        ↓
Patch only changed claims
```

### Problems addressed

  -----------------------------------------------------------------------
  Problem                             Aegis approach
  ----------------------------------- -----------------------------------
  Voice / streaming latency           Provisional retrieval begins before
                                      the utterance ends

  Compound queries                    Independent intent decomposition
                                      and retrieval

  Late constraints                    Delta Engine patches affected
                                      claims instead of rebuilding
                                      everything

  Numerical / structured constraints  Deterministic processing where
                                      appropriate

  Unsupported answers                 Claim-level grounding checks and a
                                      visible grounding boundary
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 2. Architecture

The complete architecture is provided as a rendered image in the
repository.

**[Open the full Aegis Architecture
Diagram](./architecture_diagram.png)**

![Aegis Architecture Diagram](./architecture_diagram.png)

------------------------------------------------------------------------

## 3. Core Features

### Speculative Provisional Retrieval

Retrieval can begin from useful partial input while the user is still
speaking. Reusable provisional evidence can be carried into the
completed turn.

### Multi-Intent Decomposition

Compound requests are split into independent sub-intents so evidence for
one intent does not contaminate another.

### Hybrid Synthesis

Different work is routed to the appropriate mechanism:

``` text
Structured / numerical constraint → Deterministic Solver
Abstract policy / language         → LLM
Late constraint                    → Delta Engine
```

### Delta Engine

When a user changes a constraint, Aegis performs a semantic refinement
instead of restarting the complete pipeline.

``` text
"Find a venue for my event"
              ↓
"Actually, I need capacity for 500 people"
              ↓
Identify affected claim
              ↓
Retrieve updated evidence
              ↓
Patch only that claim
```

### Trust Gauntlet

Claims are checked against retrieved evidence. Unsupported or uncertain
content is kept outside the trusted answer boundary.

------------------------------------------------------------------------

## 4. Evaluation Results

  Metric                                                 Aegis    Baseline
  ---------------------------------- ------------------------- -----------
  Retrieval recall --- overall                       **91.0%**       91.7%
  Single-intent recall                              **100.0%**      100.0%
  Multi-intent recall                                **78.8%**       80.3%
  Answer groundedness                  **100% (39/39 claims)**         ---
  Fabricated document IDs                                **0**         ---
  Median TTFT --- refine turn                      **11.2 ms**   122.15 ms
  Refine-turn retrieval reduction                    **42.9%**         N/A
  Trust Gauntlet adversarial tests              **4/4 passed**         ---

Key refinement results: **11.2 ms median TTFT** and **42.9% lower
retrieval activity** on refine turns.

------------------------------------------------------------------------

## 5. Technology Stack

  Layer                      Technology
  -------------------------- ----------------------------------------------------
  Language                   Python 3.10+
  Backend                    FastAPI, Uvicorn, Asyncio
  Streaming                  WebSockets
  LLM                        Llama 3.1 8B via Ollama
  Retrieval                  Local vector retrieval + evidence/chunk management
  Embeddings                 Local embedding model
  Deterministic processing   Regex / token-based processing
  Frontend                   HTML, CSS, JavaScript
  Deployment                 Docker, Docker Compose

------------------------------------------------------------------------

## 6. Repository Structure

``` text
Aegis/
├── backend/
│   ├── controller.py
│   ├── decomposer.py
│   ├── pipeline.py
│   ├── synthesis.py
│   ├── suppression.py
│   └── retrieval/
├── corpus/
├── frontend/
├── eval/
├── architecture_diagram.png
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── README.md
└── Aegis_Final_Presentation.pptx
```

  ----------------------------------------------------------------------------------------
  Path                                                 Purpose
  ---------------------------------------------------- -----------------------------------
  [`backend/controller.py`](./backend/controller.py)   Streaming control and speculative
                                                       dispatch

  [`backend/decomposer.py`](./backend/decomposer.py)   Multi-intent and refinement
                                                       handling

  [`backend/retrieval/`](./backend/retrieval/)         Evidence retrieval

  [`backend/synthesis.py`](./backend/synthesis.py)     Hybrid synthesis, Delta Engine,
                                                       Trust Gauntlet

  [`backend/pipeline.py`](./backend/pipeline.py)       End-to-end orchestration and
                                                       streaming

  [`frontend/`](./frontend/)                           Real-time interface and telemetry

  [`eval/`](./eval/)                                   Evaluation / benchmark scripts
  
  ----------------------------------------------------------------------------------------

------------------------------------------------------------------------

## 7. Reproducible Setup

### Requirements

-   Python **3.10+**
-   Git
-   Docker + Docker Compose **or** a local Python environment
-   Ollama is optional

### Option A --- Docker

From the repository root:

``` bash
docker compose up --build
```

Open **<http://localhost:8000>**.

Stop the application:

``` bash
docker compose down
```

### Option B --- Local Python

Create the environment:

``` bash
python -m venv .venv
```

**Windows**

``` bat
.venv\Scripts\activate
```

**macOS / Linux**

``` bash
source .venv/bin/activate
```

Install dependencies:

``` bash
pip install -r requirements.txt
```

Build the corpus index:

``` bash
python -m corpus.build_index
```

Start Aegis:

``` bash
uvicorn backend.main:app --reload
```

Open **<http://localhost:8000>**.

### Optional --- Ollama

``` bash
ollama run llama3.1:8b
```

Set the provider:

**Windows CMD**

``` cmd
set AEGIS_LLM_PROVIDER=ollama
```

**Windows PowerShell**

``` powershell
$env:AEGIS_LLM_PROVIDER="ollama"
```

**macOS / Linux**

``` bash
export AEGIS_LLM_PROVIDER=ollama
```

------------------------------------------------------------------------

## 8. Verification

Run the automated tests:

``` bash
pytest -q
```

Run the evaluation suite:

``` bash
python eval/run_eval.py
```

Then verify the application at **<http://localhost:8000>**.

------------------------------------------------------------------------
**[🎥 Watch the Aegis
Demo](https://drive.google.com/file/d/11YE5tzn1XtS09P18pabqhoy7KuI7gPUi/view?usp=sharing)**
