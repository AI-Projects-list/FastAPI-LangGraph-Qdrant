
# ✅ **Code Quality & Design Principles Review**

### *Based on the intentionally messy FastAPI + LangGraph + Qdrant implementation provided*

[![Watch the video](https://img.youtube.com/vi/NciTzm6zMbA/hqdefault.jpg)](https://www.youtube.com/watch?v=zINWveB95Zc)

---

## 1. Folder Structure (Clean + Hexagonal)

```text
app/
├── main.py                    # FastAPI app factory / entrypoint
├── core/
│   ├── config.py              # Settings (env + defaults)
│   ├── logging.py             # Logging setup
│   ├── container.py           # Lightweight "service container"
│   ├── config_dev.py
│   ├── config_staging.py
│   └── config_prod.py│
├── domain/
│   ├── models/
│   │   └── document.py        # Domain entity
│   ├── ports/
│   │   ├── embeddings.py      # Embedding service port
│   │   ├── vector_store.py    # Vector store port
│   │   ├── workflow.py        # Workflow engine port (LangGraph, etc)
│   │   └── state_store.py     # Debug / state store port (optional)
├── application/
│   ├── services/
│   │   ├── document_service.py  # Ingest/list/delete documents
│   │   ├── query_service.py     # RAG query flow
│   │   └── counter_service.py   # Example stateful service
├── infrastructure/
│   ├── embeddings/
│   │   └── random_embeddings.py # Current naive embedding impl
│   ├── vectorstores/
│   │   └── qdrant_vector_store.py   # Qdrant adapter
│   ├── workflows/
│   │   └── langgraph_workflow.py    # LangGraph adapter
│   └── state/
│       └── in_memory_state_store.py # Debug/inspection store
├── api/
│   ├── deps.py                 # FastAPI dependencies (DI)
│   ├── schemas.py              # Pydantic request/response models
│   ├── routes_documents.py     # /ingest, /batch_ingest, /documents, /documents/{id}
│   ├── routes_query.py         # /query
│   ├── routes_health.py        # /health
│   ├── routes_debug.py         # /debug/state, /chaos
│   └── routes_misc.py          # /counter
└── __init__.py
tests/
├── conftest.py
├── test_document_service.py
├── test_query_service.py
└── fakes/
    ├── fake_embeddings.py
    ├── fake_vector_store.py
    └── fake_workflow_engine.py
```

You can run via:

```bash
uvicorn app.main:create_app --factory --reload
```
---

# **1. Analysis of the Existing Code (Design Smells & Risks)**

The supplied implementation is functional, but exhibits several architectural and design problems that make the system fragile, hard to extend, and difficult to test. Below is a structured analysis based on the categories provided.

---

# **1. State and Scope**

### **How state is currently managed**

* The code relies heavily on **module-level global variables**, including:

  * `global_qdrant_client`
  * `global_workflow`
  * `global_state_store`
  * `messy_counter`
  * `global_embedding_dim`

### **Problems**

* ❌ **Global mutable state** is dangerous in a concurrent environment (FastAPI defaults to async + multi-worker).
* ❌ Globals make the system **not thread-safe** and can cause nondeterministic behavior.
* ❌ Hidden dependencies — functions read and modify global variables without the caller knowing.
* ❌ Very difficult to mock or replace in tests.

### **Risks**

* Race conditions in **`messy_counter`**
* Inconsistent workflow or Qdrant behavior across requests
* Unpredictable failures under load

### **Conclusion**

The design must eliminate globals and replace them with **explicit dependency injection** and **container-managed services**.

---

# **2. OOP, Modularity, and Cohesion**

### **Findings**

* Responsibilities are not grouped logically:

  * FastAPI routes contain core logic, Qdrant access, embeddings, and workflow orchestration.
  * Workflow nodes directly access global Qdrant and embeddings rather than abstract interfaces.
* Mixed concerns:

  * `main.py` does everything: app creation, DB setup, workflow creation, embedding logic, API endpoints.
* Tight coupling:

  * The workflow depends directly on the embedding implementation.
  * Qdrant API logic is embedded in route handlers.
  * Changing Qdrant → requires editing business logic → violates SRP.
* No boundary between:

  * Domain logic
  * Application use-cases
  * Infrastructure

### **Conclusion**

This original code violates **Single Responsibility Principle**, **Open/Closed Principle**, and is **not modular**.

A clean architecture with domain ports & adapters is required.

---

# **3. Extensibility and Change**

### Example questions:

### **What if we add a new embedding model?**

Currently:

* Must modify `generate_embedding`
* Must modify workflow nodes
* Must modify ingest and query routes
* Risk of breaking existing behavior

### **What if we replace Qdrant with Pinecone / Milvus?**

Currently:

* Qdrant calls are everywhere in the code.
* No abstraction layer.
* Would require large-scale, risky rewrite.

### **Which parts need careful regression testing when making changes?**

* Any change to `main.py` cascades through the entire system.
* Any refactor risks breaking:

  * ingest
  * query
  * workflow execution
  * state handling

### **Conclusion**

The system needs **interfaces for external services**, so concrete implementations can be swapped without touching business logic.

---

# **4. Testability**

### **Current state**

* No tests.
* Impossible to write unit tests without starting the entire app.
* Qdrant calls cannot be mocked.
* Workflow graph cannot be tested in isolation.
* Debug state is global and mutable.

### **Problems**

* High coupling to running Qdrant instance → brittle CI.
* No fake / in-memory alternatives.
* Can't test ingestion or query logic independently.

### **Conclusion**

Must introduce:

* **FakeVectorStore**, **FakeEmbeddings**, **FakeWorkflowEngine**
* Unit tests with dependency injection
* Integration tests with docker-compose + Qdrant

This was completed in the refactored version.

---

# **5. Configuration and Environment Sensitivity**

### **Current state**

* Hardcoded values:

  * `global_embedding_dim`
  * `localhost:6334`
  * `collection_name="messy_documents"`

### **Problems**

* Cannot run in staging/prod without changing code.
* Harder to deploy in containers.
* Cannot manage configuration via environment variables.

### **Conclusion**

Introduce centralized `Settings` (Pydantic Settings) + separate dev/staging/prod configs.

This was added in the new architecture.

---

# ❗ Summary of Key Design Smells

| Issue                     | Impact                                           |
| ------------------------- | ------------------------------------------------ |
| Global state              | Concurrency failures, nondeterministic behavior  |
| No separation of concerns | Hard to test, hard to extend                     |
| Hardcoded config          | Not deployable to different environments         |
| Tight coupling            | Impossible to replace Qdrant/embeddings/workflow |
| Logic inside routes       | Mixing delivery + business logic                 |
| No tests                  | Hard to guarantee reliability                    |

---

# ✅ **2. What I Would Prioritize Refactoring (and Why)**

Below is the prioritized refactor plan:

---

## **Priority 1 — Remove Global State (Critical)**

Why:

* Biggest risk for concurrency bugs
* Prevents testability
* Encourages implicit shared state

Solution:

* Build a **dependency injection container** (`AppContainer`)
* Inject Qdrant, embeddings, workflow, services into FastAPI via `Depends`

---

## **Priority 2 — Split Architecture into Layers (Clean + Hexagonal)**

Why:

* We need modularity, testability, swappable infrastructure

Solution:

* Domain = pure models + ports
* Application = business services
* Infrastructure = Qdrant, embeddings, workflow adapters
* API = only routing

This was done in the refactored repo.

---

## **Priority 3 — Introduce Interfaces (Ports)**

Why:

* Avoid hard dependencies on Qdrant, workflow, embeddings

Solution:

* `EmbeddingsPort`
* `VectorStorePort`
* `WorkflowEnginePort`
* `StateStorePort`

Now it’s trivial to replace Qdrant or embeddings.

---

## **Priority 4 — Add Unit Tests with Fakes**

Why:

* Ensures behavior without infrastructure
* Catches regression early

Solution:

* Fake embeddings, vector store, workflow engine
* pytest suite

Already implemented.

---

## **Priority 5 — Centralize Configuration**

Why:

* Avoid hardcoded values
* Support multi-environment deployments

Solution:

* `.env`
* Pydantic Settings
* Config profiles: dev, staging, prod

Done.

---

## **Priority 6 — Add Docker & CI**

Why:

* Ensures reproducibility, correct environment parity, and automated testing.

Solution:

* Dockerfile
* docker-compose (API + Qdrant)
* GitHub CI workflow

Included above.

---

# ✅ **3. Migration Strategy (Incremental, Safe, Non-breaking)**

This strategy preserves the original functionality while progressively improving architecture.

---

## **Step 1 — Wrap Qdrant & Embedding Logic Behind Interfaces**

* Create ports
* Implement simple adapters
* Modify routes to use them

---

## **Step 2 — Introduce App Container (Dependency Injection)**

* Build container on startup
* Store in `app.state.container`
* Replace all globals with container-managed singletons

---

## **Step 3 — Extract Services (DocumentService, QueryService)**

* Move logic out of routes → into application layer
* Keep API thin and simple

---

## **Step 4 — Extract Workflow to Its Own Adapter**

* Encapsulate LangGraph
* Make workflow composable and testable

---

## **Step 5 — Add Configuration System**

* Create `.env`, `Settings`, dev/prod/staging configs
* Remove all hard-coded values

---

## **Step 6 — Add Testing Infrastructure**

* Create fake implementations
* Write unit tests for ingestion, querying

---

## **Step 7 — Containerize**

* Multi-stage Dockerfile
* docker-compose with Qdrant

---

## **Step 8 — Add CI Pipeline**

* pytest
* optional integration tests

---

## **Step 9 — Refactor Folder Structure**

Move to:

```
app/
  core/
  domain/
  application/
  infrastructure/
  api/
```

Already implemented in the refactored project.

---

# 💡 **4. Final Evaluation**

The original messy code is not “bad”—it’s just **early-stage**, typical of prototypes.

But as the system grows, the costs become significant:

* risky changes
* hard to add new capabilities
* bugs difficult to trace
* inability to test
* inconsistent configuration
* brittle deployment

The final architecture I generated solves all of these.

You now have a complete:

* Clean architecture
* Hexagonal ports & adapters
* DI container
* Config profiles
* Full unit test suite
* Docker + docker-compose
* GitHub CI
* Ready-to-scale RAG pipeline



---

## 1. Big Picture – What This Project Is

You now have a **production-style RAG microservice**:

* **FastAPI** app (HTTP interface)
* **LangGraph** workflow engine (RAG pipeline)
* **Qdrant** vector database (document store)
* **Clean + Hexagonal architecture**
* **Config profiles** (dev / staging / prod)
* **Unit tests** with fake adapters
* **Docker + docker-compose** for local/production
* **GitHub Actions CI** for tests

The main idea:

> Build once (stable core + abstractions), then only swap adapters/config to change embeddings, vector DB, environment, or workflow.

---

## 2. Architecture Overview (Clean + Hexagonal)

### Layers:

1. **Domain** (`app/domain`)

   * Pure business contracts and models
   * Has no idea about FastAPI, Qdrant, LangGraph, Docker, etc.
   * Ports:

     * `EmbeddingsPort`
     * `VectorStorePort`
     * `WorkflowEnginePort`
     * `StateStorePort`
   * Model:

     * `Document` entity

2. **Application** (`app/application`)

   * Orchestrates use cases
   * Stateless services:

     * `DocumentService`
     * `QueryService`
     * `CounterService`
   * Depends only on **domain ports**, not concrete implementations.

3. **Infrastructure** (`app/infrastructure`)

   * Adapters that implement ports:

     * `RandomEmbeddingsService` → `EmbeddingsPort`
     * `QdrantVectorStore` → `VectorStorePort`
     * `LangGraphWorkflowEngine` → `WorkflowEnginePort`
     * `InMemoryStateStore` → `StateStorePort`
   * Can be replaced without touching application/domain code.

4. **API / Web Layer** (`app/api`)

   * FastAPI routers + schemas + dependency wiring
   * Endpoints:

     * `/ingest`, `/batch_ingest`, `/documents`, `/documents/{id}`
     * `/query`
     * `/health`
     * `/debug/state`, `/chaos`
     * `/counter`

5. **Core / Composition** (`app/core`)

   * `Settings` + environment-specific configs (dev/staging/prod)
   * Logging setup
   * `AppContainer` → wires all dependencies (mini DI container)
   * `build_container()` → single point to:

     * Choose settings based on `ENVIRONMENT`
     * Instantiate Qdrant client, embeddings, vector store, workflow, state store
     * Instantiate services

6. **Entry Point** (`app/main.py`)

   * Uses FastAPI `lifespan` to build container once on startup
   * Attaches `container` to `app.state`
   * Includes all routers

---

## 3. Unit Tests with Fakes

Goal: **test services without Qdrant, LangGraph, or HTTP**.

### Fakes:

* `FakeEmbeddings` → deterministic tiny vectors
* `FakeVectorStore` → simple in-memory dict, mimics basic vector store behavior
* `FakeWorkflowEngine` → returns canned retrieval + answer for any query

These live in:

```text
tests/fakes/
  fake_embeddings.py
  fake_vector_store.py
  fake_workflow_engine.py
```

### `tests/conftest.py`

* Builds a `fake_services` fixture:

  * `embeddings` = `FakeEmbeddings`
  * `vector_store` = `FakeVectorStore`
  * `state_store` = `InMemoryStateStore`
  * `document_service` = real `DocumentService`, but with fakes
  * `query_service` = real `QueryService`, but with `FakeWorkflowEngine`

So your tests hit **real application logic** with **fake infrastructure**.

### DocumentService tests

* `test_ingest_and_list`:

  * Ingest a document
  * Push embedding + payload
  * Assert that listing returns exactly that doc

* `test_delete`:

  * Ingest + upsert doc
  * Delete it
  * Assert list is empty

### QueryService test

* `test_query_service`:

  * Calls `run_query("test query")`
  * Asserts there is `final_answer` and `retrieved_docs`
  * Ensures answer structure is correct

➡️ This setup gives you **fast, deterministic tests** that don’t require any external service.

Run them locally (inside project):

```bash
poetry install
pytest
```

---

## 4. Docker & docker-compose

### Dockerfile

* Uses **multi-stage build**:

  1. **Builder stage**:

     * Installs dependencies via Poetry (`pyproject.toml`)
     * Copies `app/` code
  2. **Runtime stage**:

     * Copies Python env + app
     * Launches using:

       ```bash
       uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000
       ```

This gives a **small final image** and proper reproducible environment.

### docker-compose.yml

Services:

* `api`:

  * Builds from local Dockerfile
  * Exposes port 8000
  * Env config:

    * `ENVIRONMENT=prod`
    * `QDRANT_HOST=qdrant`
    * `QDRANT_PORT=6334`
  * Depends on `qdrant`.

* `qdrant`:

  * Uses official `qdrant/qdrant` image
  * Exposes port 6334
  * Persists data with `qdrant_data` volume

Run everything:

```bash
docker-compose up --build
```

Then hit:

* `http://localhost:8000/docs` → FastAPI docs
* Ingest/query like before, but in a clean architecture setup.

---

## 5. Config Profiles (dev / staging / prod)

Under `app/core`:

* `config.py` → base `Settings` (Pydantic Settings)
* `config_dev.py` → `DevSettings`
* `config_staging.py` → `StagingSettings`
* `config_prod.py` → `ProdSettings`

`build_container()` chooses settings based on:

```python
env = os.getenv("ENVIRONMENT", "dev").lower()
```

So:

* `ENVIRONMENT=dev` → `DevSettings`
* `ENVIRONMENT=staging` → `StagingSettings`
* `ENVIRONMENT=prod` → `ProdSettings`

Each profile can override:

* `qdrant_host`
* `port`
* `log_level`
* etc.

This lets you deploy the **same code** to local/dev/staging/prod with **only env changes**.

---

## 6. CI Skeleton (GitHub Actions)

`/.github/workflows/ci.yml`:

* Triggers on:

  * Push to `main` or `dev`
  * Any PR
* Steps:

  * Checkout repo
  * Set up Python 3.11
  * Install dependencies via Poetry
  * Run tests with pytest
* Also spins up a **Qdrant service** in case later you add integration tests that depend on it.

This gives you:

* Automatic test runs on every PR/commit
* Early detection of breaking changes

---

## 7. How to Run This Project

### Locally (no Docker)

```bash
cd clean_langgraph_qdrant
pip install poetry
poetry install

# run API
poetry run uvicorn app.main:create_app --factory --reload
```

Make sure Qdrant is running locally (`localhost:6334`) or adjust config/env.

---

### With Docker & docker-compose

```bash
docker-compose up --build
```

Open: `http://localhost:8000/docs`

---

### Run Tests

```bash
poetry run pytest
```

---
