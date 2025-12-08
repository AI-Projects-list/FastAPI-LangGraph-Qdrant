# Project Flow Documentation

## Table of Contents
1. [System Architecture Overview](#system-architecture-overview)
2. [Application Startup Flow](#application-startup-flow)
3. [Document Ingestion Flow](#document-ingestion-flow)
4. [PDF Upload Flow](#pdf-upload-flow)
5. [Query/RAG Flow](#queryrag-flow)
6. [Document Management Flow](#document-management-flow)
7. [Dependency Injection & Container Flow](#dependency-injection--container-flow)
8. [Error Handling Flow](#error-handling-flow)

---

## System Architecture Overview

```mermaid
graph TB
    Client[Client/Browser] --> API[FastAPI Application]
    API --> AppServices[Application Services Layer]
    AppServices --> Domain[Domain Layer - Ports/Interfaces]
    Domain --> Infrastructure[Infrastructure Layer - Adapters]
    
    subgraph "Infrastructure Adapters"
        Infrastructure --> Embeddings[Random Embeddings Service]
        Infrastructure --> VectorDB[Qdrant Vector Store]
        Infrastructure --> Workflow[LangGraph Workflow Engine]
        Infrastructure --> StateStore[In-Memory State Store]
    end
    
    VectorDB --> Qdrant[(Qdrant Database)]
    
    style Domain fill:#e1f5ff
    style AppServices fill:#fff4e1
    style Infrastructure fill:#f0fff0
```

---

## Application Startup Flow

```mermaid
sequenceDiagram
    participant Main as app.main
    participant Lifespan as Lifespan Context
    participant Container as Container Builder
    participant Config as Settings Loader
    participant Qdrant as Qdrant Client
    participant VectorStore as Vector Store
    participant Services as Application Services
    
    Main->>Lifespan: Application Start
    Lifespan->>Container: build_container()
    Container->>Config: load_settings()
    Config->>Config: Read ENVIRONMENT variable
    Config-->>Container: Settings (dev/staging/prod)
    
    Container->>Qdrant: Create QdrantClient(host, port)
    Container->>VectorStore: QdrantVectorStore(client, collection, dim)
    VectorStore->>Qdrant: Check if collection exists
    alt Collection does not exist
        VectorStore->>Qdrant: create_collection(vectors_config)
    end
    
    Container->>Services: Initialize Embeddings
    Container->>Services: Initialize Workflow Engine
    Container->>Services: Initialize State Store
    Container->>Services: Initialize Document Service
    Container->>Services: Initialize Query Service
    
    Container-->>Main: AppContainer (with all dependencies)
    Main->>Main: Attach container to app.state
    Main->>Main: Include all API routers
    Main-->>Client: Application Ready (HTTP 200)
```

### Startup Flow Details

1. **Environment Detection**
   - Reads `ENVIRONMENT` variable (dev/staging/prod)
   - Loads appropriate config class

2. **Qdrant Initialization**
   - Connects to Qdrant at configured host:port
   - Creates or verifies collection existence
   - Sets up vector parameters (dimension, distance metric)

3. **Service Wiring**
   - All services are instantiated with their dependencies
   - Dependency injection happens through constructor parameters
   - Container holds all service instances

4. **Router Registration**
   - Document routes
   - Query routes
   - Health check routes
   - Debug routes
   - Counter routes (example stateful service)

---

## Document Ingestion Flow

```mermaid
sequenceDiagram
    participant Client
    participant API as POST /ingest
    participant DocService as Document Service
    participant Embeddings as Embeddings Service
    participant VectorStore as Vector Store
    participant StateStore as State Store
    participant Qdrant as Qdrant DB
    
    Client->>API: POST {content, metadata}
    API->>Embeddings: embed(content)
    Embeddings-->>API: vector [float]
    
    API->>DocService: ingest_document(content, metadata)
    DocService->>DocService: Generate UUID
    DocService->>DocService: Create payload with timestamp
    DocService->>StateStore: save(doc_id, payload)
    StateStore-->>DocService: Success
    DocService-->>API: doc_id
    
    API->>DocService: ingest_with_vector(doc_id, vector, payload)
    DocService->>VectorStore: upsert_document(doc_id, vector, payload)
    VectorStore->>Qdrant: upsert(collection, points)
    Qdrant-->>VectorStore: Success
    VectorStore-->>DocService: Success
    DocService->>StateStore: save(doc_id, payload)
    DocService-->>API: Success
    
    API-->>Client: {id: doc_id, message: "Success"}
```

### Ingestion Flow Breakdown

1. **Request Reception**
   - Validate input schema (DocumentInput)
   - Extract content and metadata

2. **Embedding Generation**
   - Convert text content to vector representation
   - Currently uses RandomEmbeddingsService (deterministic random)

3. **Document ID Creation**
   - Generate unique UUID for document
   - Create payload with content, metadata, timestamp

4. **Dual Storage**
   - **State Store**: Stores raw document data (debugging/inspection)
   - **Vector Store**: Stores embedding + payload in Qdrant

5. **Response**
   - Return document ID to client for future reference

---

## PDF Upload Flow

```mermaid
flowchart TD
    A[Client Uploads PDF] --> B{Validate File Type}
    B -->|Not PDF| C[Return 400 Error]
    B -->|Valid PDF| D[Read PDF Bytes]
    
    D --> E[Parse PDF with PyPDF2]
    E --> F[Get Total Pages]
    
    F --> G[Loop Through Pages]
    G --> H{Extract Text from Page}
    
    H -->|No Text| I[Mark as Skipped]
    H -->|Has Text| J[Create Page Metadata]
    
    J --> K[Generate Embedding]
    K --> L[Create Document ID]
    L --> M[Store in Vector DB]
    M --> N[Store in State Store]
    
    N --> O{More Pages?}
    I --> O
    
    O -->|Yes| G
    O -->|No| P[Aggregate Results]
    
    P --> Q[Return Summary]
    Q --> R[filename, total_pages, successful_pages, results]
    
    style B fill:#ffe6e6
    style H fill:#e6f3ff
    style Q fill:#e6ffe6
```

### PDF Processing Details

**Per Page:**
- Extract text content
- Generate unique document ID
- Create metadata:
  ```json
  {
    "filename": "document.pdf",
    "page_number": 1,
    "total_pages": 10,
    "content_type": "application/pdf"
  }
  ```
- Generate embedding vector
- Store with metadata in Qdrant

**Response Structure:**
```json
{
  "filename": "document.pdf",
  "total_pages": 10,
  "successful_pages": 8,
  "results": [
    {"page": 1, "id": "uuid", "status": "success", "chars": 1234},
    {"page": 2, "status": "skipped", "reason": "No text found"},
    {"page": 3, "status": "error", "error": "Parse error"}
  ]
}
```

---

## Query/RAG Flow

```mermaid
sequenceDiagram
    participant Client
    participant API as POST /query
    participant QueryService as Query Service
    participant Workflow as LangGraph Workflow
    participant Embeddings as Embeddings Service
    participant VectorStore as Vector Store
    participant Qdrant as Qdrant DB
    
    Client->>API: POST {query, top_k}
    API->>QueryService: run_query(query, top_k)
    QueryService->>QueryService: Create initial_state
    
    QueryService->>Workflow: run(initial_state)
    
    Note over Workflow: Graph Execution Starts
    
    Workflow->>Embeddings: embed(query)
    Embeddings-->>Workflow: query_vector
    
    Workflow->>VectorStore: search(query_vector, top_k)
    VectorStore->>Qdrant: search(collection, vector, limit)
    Qdrant-->>VectorStore: Scored Results
    VectorStore-->>Workflow: retrieved_docs
    
    Workflow->>Workflow: Process/Augment Context
    Workflow->>Workflow: Generate Answer
    Workflow-->>QueryService: final_state
    
    Note over QueryService: Extract Results
    
    QueryService-->>API: {query, docs, answer, time}
    API-->>Client: WorkflowResult
```

### RAG Flow Breakdown

**Initial State Creation:**
```python
{
    "query": "user question",
    "top_k": 5,
    "retrieved_docs": [],
    "final_answer": "",
    "processing_steps": [],
    "error": None
}
```

**LangGraph Workflow Steps:**
1. **Embed Query**: Convert user query to vector
2. **Retrieve**: Search Qdrant for similar documents
3. **Augment**: Add retrieved context to state
4. **Generate**: Create answer based on context
5. **Return**: Final state with answer

**Response Format:**
```json
{
  "initial_query": "What is RAG?",
  "retrieved_docs": [
    {
      "id": "uuid",
      "content": "RAG stands for...",
      "score": 0.95
    }
  ],
  "final_answer": "RAG (Retrieval Augmented Generation)...",
  "processing_time": 0.234
}
```

---

## Document Management Flow

### List Documents

```mermaid
graph LR
    A[GET /documents?limit=10] --> B[Document Service]
    B --> C[Vector Store]
    C --> D[Qdrant Scroll]
    D --> E[Return Documents List]
    
    style E fill:#e6ffe6
```

**Response:**
```json
{
  "documents": [
    {
      "id": "uuid",
      "content": "First 100 chars...",
      "metadata": {"source": "api"}
    }
  ]
}
```

### Delete Document

```mermaid
sequenceDiagram
    participant Client
    participant API as DELETE /documents/{id}
    participant DocService as Document Service
    participant VectorStore as Vector Store
    participant StateStore as State Store
    participant Qdrant as Qdrant DB
    
    Client->>API: DELETE /documents/uuid-123
    API->>DocService: delete_document(doc_id)
    
    par Parallel Deletion
        DocService->>VectorStore: delete_document(doc_id)
        VectorStore->>Qdrant: delete(collection, points=[id])
        Qdrant-->>VectorStore: Success
    and
        DocService->>StateStore: delete(doc_id)
        StateStore-->>DocService: Success
    end
    
    DocService-->>API: Success
    API-->>Client: {message: "Document deleted"}
```

---

## Dependency Injection & Container Flow

```mermaid
graph TD
    A[build_container] --> B[Load Settings]
    B --> C{Environment?}
    
    C -->|dev| D[DevSettings]
    C -->|staging| E[StagingSettings]
    C -->|prod| F[ProdSettings]
    
    D --> G[Initialize Clients]
    E --> G
    F --> G
    
    G --> H[Qdrant Client]
    G --> I[Random Embeddings]
    
    H --> J[Vector Store Adapter]
    I --> K[Embeddings Port]
    
    J --> L[Document Service]
    K --> L
    
    M[Workflow Engine] --> N[Query Service]
    O[State Store] --> L
    
    L --> P[AppContainer]
    N --> P
    
    P --> Q[FastAPI app.state.container]
    
    style P fill:#ffe6cc
    style Q fill:#ccffcc
```

### Dependency Graph

```
Settings
    ├── Qdrant Client
    │   └── Vector Store (Infrastructure)
    │       └── Document Service (Application)
    │
    ├── Random Embeddings (Infrastructure)
    │   └── Workflow Engine (Infrastructure)
    │       └── Query Service (Application)
    │
    └── State Store (Infrastructure)
        └── Document Service (Application)
```

### Dependency Access in Routes

```python
# Dependency injection in FastAPI routes
@router.post("/ingest")
async def ingest_document(
    doc: DocumentInput,
    container: AppContainer = Depends(get_container),
    document_service: DocumentService = Depends(get_document_service),
):
    # Use injected dependencies
    vector = container.embeddings.embed(doc.content)
    doc_id = await document_service.ingest_document(...)
```

---

## Error Handling Flow

```mermaid
flowchart TD
    A[Request Arrives] --> B{Validation}
    B -->|Invalid Schema| C[422 Unprocessable Entity]
    B -->|Valid| D[Process Request]
    
    D --> E{Service Layer}
    E -->|Success| F[Return 200/201]
    E -->|Business Logic Error| G[Log & Return 400/404]
    E -->|Infrastructure Error| H[Log & Return 500]
    
    H --> I{Error Type}
    I -->|Qdrant Connection| J[Connection Error]
    I -->|Embedding Error| K[Processing Error]
    I -->|Unknown| L[Generic 500]
    
    J --> M[Detailed Error Message]
    K --> M
    L --> M
    
    M --> N[HTTPException with detail]
    
    style C fill:#ffcccc
    style F fill:#ccffcc
    style G fill:#ffffcc
    style H fill:#ffcccc
```

### Error Categories

**1. Validation Errors (422)**
- Invalid request schema
- Missing required fields
- Type mismatches

**2. Client Errors (400, 404)**
- Document not found
- Invalid file type (non-PDF)
- Business rule violations

**3. Server Errors (500)**
- Qdrant connection failures
- Database errors
- Unexpected exceptions

### Error Response Format

```json
{
  "detail": "Detailed error message explaining what went wrong"
}
```

---

## Complete Request-Response Flow

```mermaid
sequenceDiagram
    autonumber
    
    participant Browser
    participant Nginx/LB as Load Balancer
    participant FastAPI
    participant Middleware
    participant Router
    participant Dependency
    participant Service
    participant Adapter
    participant External as External Services
    
    Browser->>Nginx/LB: HTTP Request
    Nginx/LB->>FastAPI: Forward Request
    FastAPI->>Middleware: CORS, Logging, etc.
    Middleware->>Router: Route Match
    Router->>Dependency: Resolve Dependencies
    Dependency->>Dependency: get_container()
    Dependency->>Dependency: get_document_service()
    Dependency-->>Router: Injected Dependencies
    
    Router->>Service: Call Service Method
    Service->>Adapter: Call Infrastructure Port
    Adapter->>External: API Call (Qdrant/etc)
    External-->>Adapter: Response
    Adapter-->>Service: Transformed Data
    Service-->>Router: Service Response
    
    Router->>Router: Serialize to JSON
    Router-->>Middleware: HTTP Response
    Middleware-->>FastAPI: Add Headers
    FastAPI-->>Nginx/LB: HTTP Response
    Nginx/LB-->>Browser: Final Response
```

---

## Configuration Flow by Environment

```mermaid
graph TD
    A[Application Start] --> B{ENVIRONMENT Variable}
    
    B -->|dev| C[DevSettings]
    B -->|staging| D[StagingSettings]
    B -->|prod| E[ProdSettings]
    B -->|not set| F[Default to DevSettings]
    
    C --> G[Local Configuration]
    G --> H[qdrant_host: localhost]
    G --> I[qdrant_port: 6334]
    G --> J[log_level: DEBUG]
    
    D --> K[Staging Configuration]
    K --> L[qdrant_host: staging-qdrant]
    K --> M[qdrant_port: 6334]
    K --> N[log_level: INFO]
    
    E --> O[Production Configuration]
    O --> P[qdrant_host: qdrant]
    O --> Q[qdrant_port: 6334]
    O --> R[log_level: WARNING]
    
    style C fill:#e6f3ff
    style D fill:#fff3e6
    style E fill:#ffe6e6
```

---

## Testing Flow

```mermaid
graph LR
    A[pytest] --> B[conftest.py]
    B --> C[fake_services fixture]
    
    C --> D[FakeEmbeddings]
    C --> E[FakeVectorStore]
    C --> F[FakeWorkflowEngine]
    C --> G[InMemoryStateStore]
    
    D --> H[Real DocumentService]
    E --> H
    G --> H
    
    F --> I[Real QueryService]
    
    H --> J[test_ingest_and_list]
    H --> K[test_delete]
    I --> L[test_query_service]
    
    style C fill:#ccffcc
    style H fill:#ffffe6
    style I fill:#ffffe6
```

### Test Isolation

- **Unit Tests**: Use fake implementations
- **No External Dependencies**: Tests run without Qdrant, LangGraph, etc.
- **Fast Execution**: All in-memory operations
- **Deterministic**: Same input = same output

---

## Docker Deployment Flow

```mermaid
graph TD
    A[docker-compose up] --> B[Start Qdrant Service]
    B --> C[Pull qdrant/qdrant image]
    C --> D[Create qdrant_data volume]
    D --> E[Map port 6334:6333]
    E --> F[Qdrant Ready]
    
    A --> G[Build API Service]
    G --> H[Multi-stage Dockerfile]
    H --> I[Stage 1: Install Dependencies]
    I --> J[Poetry install]
    J --> K[Stage 2: Runtime Image]
    K --> L[Copy dependencies & code]
    L --> M[Expose port 8000]
    M --> N[CMD: uvicorn]
    
    F --> O[API Connects to Qdrant]
    N --> O
    O --> P[Application Ready]
    
    style F fill:#ccffcc
    style P fill:#ccffcc
```

---

## CI/CD Pipeline Flow

```mermaid
sequenceDiagram
    participant Dev as Developer
    participant Git as GitHub
    participant GHA as GitHub Actions
    participant Docker as Docker Hub
    participant Prod as Production
    
    Dev->>Git: git push origin main
    Git->>GHA: Trigger CI Workflow
    
    GHA->>GHA: Checkout Code
    GHA->>GHA: Setup Python 3.11
    GHA->>GHA: Install Poetry
    GHA->>GHA: poetry install
    
    GHA->>GHA: Start Qdrant Service
    GHA->>GHA: Set PYTHONPATH
    GHA->>GHA: poetry run pytest
    
    alt Tests Pass
        GHA->>Git: ✅ Status Check Pass
        Note over Dev: Safe to Deploy
    else Tests Fail
        GHA->>Git: ❌ Status Check Fail
        Git->>Dev: Notification
        Note over Dev: Fix Issues
    end
    
    opt Manual Deploy (if tests pass)
        Dev->>Docker: docker-compose build
        Dev->>Prod: docker-compose up -d
    end
```

---

## Summary of Key Flows

### 1. **Request Flow**
```
Client → FastAPI → Router → Dependency Injection → Service → Adapter → External Service
```

### 2. **Data Flow**
```
Raw Text → Embedding → Vector Store (Qdrant) → Retrieval → Context → LLM → Answer
```

### 3. **Configuration Flow**
```
ENV Variable → Settings Class → Container → Services → Infrastructure
```

### 4. **Error Flow**
```
Exception → Service Layer → HTTPException → FastAPI → JSON Error Response
```

### 5. **Test Flow**
```
pytest → Fixtures → Fakes → Real Services → Assertions
```

---

## Architecture Principles Applied

### 1. **Clean Architecture**
- **Independence**: Domain doesn't know about infrastructure
- **Testability**: Services tested with fakes
- **Flexibility**: Easy to swap implementations

### 2. **Hexagonal Architecture**
- **Ports**: Defined in domain layer
- **Adapters**: Implemented in infrastructure
- **Dependency Inversion**: Services depend on abstractions

### 3. **Dependency Injection**
- **Container Pattern**: Central wiring
- **Constructor Injection**: Dependencies passed explicitly
- **Lifecycle Management**: Single instance per request

### 4. **SOLID Principles**
- **Single Responsibility**: Each service has one job
- **Open/Closed**: Extend via new adapters, not modifications
- **Liskov Substitution**: Ports can be swapped
- **Interface Segregation**: Small, focused ports
- **Dependency Inversion**: Depend on abstractions

---

## Performance Considerations

### Optimization Points

1. **Embedding Cache**: Cache frequently used embeddings
2. **Connection Pooling**: Reuse Qdrant connections
3. **Batch Processing**: Batch ingest for multiple documents
4. **Async Operations**: All I/O is async
5. **Vector Index**: Qdrant's HNSW index for fast similarity search

### Scaling Strategy

```mermaid
graph LR
    A[Load Balancer] --> B[API Instance 1]
    A --> C[API Instance 2]
    A --> D[API Instance N]
    
    B --> E[Qdrant Cluster]
    C --> E
    D --> E
    
    E --> F[Shard 1]
    E --> G[Shard 2]
    E --> H[Shard N]
```

- **Horizontal Scaling**: Multiple API instances
- **Stateless**: No session state in API
- **Shared Vector DB**: All instances use same Qdrant
- **Container Orchestration**: Kubernetes/Docker Swarm

---

## Monitoring & Observability

### Recommended Metrics

1. **Request Metrics**
   - Request rate (req/s)
   - Response time (p50, p95, p99)
   - Error rate

2. **Service Metrics**
   - Embedding generation time
   - Vector search latency
   - Document ingestion rate

3. **Infrastructure Metrics**
   - Qdrant query performance
   - Memory usage
   - Connection pool stats

### Logging Flow

```
Application → Structured Logs → Log Aggregator → Analysis Dashboard
                                        ↓
                                   Alert System
```

---

**End of Project Flow Documentation**
