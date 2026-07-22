# RAG Knowledge Assistant — Project Plan

## 1. Project overview

The RAG Knowledge Assistant is a backend application where authenticated users can upload documents and ask questions about their contents. The system retrieves the most relevant document sections and sends them to a Hugging Face language model to generate an answer supported by source references.

### Example

**Question:** How many paid leaves are provided?

**Answer:** Employees receive 18 paid leaves annually.

**Source:** `employee_policy.pdf`, page 6

## 2. Goals

- Learn Retrieval-Augmented Generation end to end.
- Build a production-style FastAPI backend.
- Generate embeddings using a Hugging Face model.
- Store and search embeddings using PostgreSQL and pgvector.
- Generate grounded answers through the Hugging Face Inference API.
- Return document and page citations with answers.
- Add authentication, testing, Docker, and evaluation.

## 3. Technology stack

| Area | Technology |
| --- | --- |
| Language | Python |
| API framework | FastAPI |
| Database | PostgreSQL |
| Vector search | pgvector |
| ORM | SQLAlchemy 2 |
| Migrations | Alembic |
| Embeddings | Hugging Face Sentence Transformers |
| Initial embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| Answer generation | Hugging Face Inference API |
| PDF extraction | PyMuPDF |
| Authentication | JWT |
| Validation | Pydantic |
| Testing | Pytest |
| Code quality | Ruff |
| Containerization | Docker and Docker Compose |
| API testing | Swagger and Postman |

## 4. System workflow

### Document indexing

1. User uploads a PDF or TXT document.
2. The application validates and stores the file.
3. Text is extracted and cleaned.
4. Text is divided into overlapping chunks.
5. Hugging Face generates an embedding for every chunk.
6. Chunks, metadata, and embeddings are stored in PostgreSQL.

### Question answering

1. User submits a question.
2. The application generates an embedding for the question.
3. pgvector finds the most similar document chunks.
4. The retrieved chunks are added to a controlled prompt.
5. A Hugging Face language model generates the answer.
6. The API returns the answer with document and page references.

## 5. Development phases

### Phase 1 — Project foundation

- Create the project structure.
- Install FastAPI and core dependencies.
- Configure environment variables and application settings.
- Configure structured logging and centralized error handling.
- Add `GET /api/v1/health`.

**Completion condition:** FastAPI starts successfully and the health endpoint returns a healthy response.

### Phase 2 — PostgreSQL and pgvector

- Start PostgreSQL through Docker Compose.
- Enable the PostgreSQL `vector` extension.
- Configure SQLAlchemy database sessions.
- Configure Alembic migrations.
- Create and verify the initial migration.

**Completion condition:** The application connects to PostgreSQL and can read and write a vector column.

### Phase 3 — Authentication

- Register a user.
- Hash passwords securely.
- Log in and issue a JWT access token.
- Add a current-user dependency.
- Enforce document and conversation ownership.

Endpoints:

```http
POST /api/v1/auth/register
POST /api/v1/auth/login
GET  /api/v1/auth/me
```

### Phase 4 — Document management

- Support PDF and TXT documents initially.
- Validate file extension, MIME type, and size.
- Generate safe stored filenames.
- Extract and validate text.
- Track document-processing status.
- List, inspect, and delete documents.

Endpoints:

```http
POST   /api/v1/documents
GET    /api/v1/documents
GET    /api/v1/documents/{document_id}
DELETE /api/v1/documents/{document_id}
```

Processing states:

```text
pending -> processing -> completed
                      -> failed
```

### Phase 5 — Text chunking

- Preserve page numbers and document metadata.
- Avoid splitting sentences where practical.
- Start with a chunk size of approximately 600 words or model-appropriate tokens.
- Start with an overlap of approximately 100 words or 10–20%.
- Make chunk settings configurable.
- Test the strategy using real documents.

Every chunk will store:

- Document ID
- Chunk index
- Content
- Page number
- Embedding
- Additional metadata

### Phase 6 — Hugging Face embeddings

- Use `sentence-transformers/all-MiniLM-L6-v2` initially.
- Load the model once during application startup.
- Generate embeddings locally and in batches.
- Validate the expected 384-dimensional vector.
- Store embeddings in pgvector.

### Phase 7 — Semantic retrieval

- Embed the user's question.
- Filter searchable chunks by the current user and selected documents.
- Run vector similarity search.
- Retrieve the top matching chunks and their metadata.
- Begin with `top_k = 5` and make it configurable.
- Return similarity scores for debugging and evaluation.

Internal search endpoint:

```http
POST /api/v1/search
```

Example request:

```json
{
  "question": "How many paid leaves are provided?",
  "document_ids": ["document-uuid"],
  "top_k": 5
}
```

### Phase 8 — RAG answer generation

- Build a prompt from the user question and retrieved chunks.
- Send the prompt to a Hugging Face generation model.
- Require the model to use only the supplied context.
- Return an explicit response when the answer is unavailable.
- Include source document, page, chunk, and similarity information.
- Treat instructions inside uploaded documents as untrusted content.

Endpoint:

```http
POST /api/v1/chat/ask
```

Example response:

```json
{
  "answer": "Employees receive 18 paid leaves annually.",
  "sources": [
    {
      "document_id": "document-uuid",
      "filename": "employee_policy.pdf",
      "page_number": 6,
      "chunk_id": "chunk-uuid",
      "score": 0.87
    }
  ]
}
```

### Phase 9 — Conversations and history

- Create and list conversations.
- Store user questions, assistant answers, sources, model name, and response time.
- Retrieve and delete a conversation.
- Limit the amount of previous conversation included in a prompt.

Endpoints:

```http
POST   /api/v1/conversations
GET    /api/v1/conversations
GET    /api/v1/conversations/{conversation_id}
DELETE /api/v1/conversations/{conversation_id}
POST   /api/v1/conversations/{conversation_id}/messages
```

### Phase 10 — Testing

Test the following areas:

- Registration, login, password hashing, and JWT validation
- Document ownership and authorization
- File type and size validation
- PDF and TXT extraction
- Empty and unreadable documents
- Text chunking and metadata
- Embedding dimensions
- Vector similarity search
- Empty retrieval results
- Answer grounding and citations
- Hugging Face API errors and timeouts
- Database failures

Testing levels:

- Unit tests
- API integration tests
- Retrieval-quality tests
- Manual Swagger/Postman testing

### Phase 11 — Dockerization

Docker Compose services:

- `rag-api`
- `postgres-pgvector`

The setup will include:

- Persistent PostgreSQL volume
- Uploaded-document volume
- Environment variables
- Container health checks
- Repeatable database migrations

Target startup command:

```bash
docker compose up --build
```

Swagger target:

```text
http://localhost:8000/docs
```

### Phase 12 — RAG evaluation

Create a small dataset containing:

- Question
- Expected answer
- Expected document
- Expected page or chunk

Example:

```json
{
  "question": "What is the annual leave allowance?",
  "expected_answer": "18 paid leaves",
  "expected_source": "employee_policy.pdf",
  "expected_page": 6
}
```

Evaluate:

- Whether the correct chunk was retrieved
- Whether the answer is supported by the retrieved context
- Whether the source is correct
- Whether the system refuses unsupported questions
- Retrieval and generation latency

## 6. Database design

### `users`

- `id`
- `name`
- `email`
- `hashed_password`
- `is_active`
- `created_at`
- `updated_at`

### `documents`

- `id`
- `user_id`
- `original_filename`
- `stored_filename`
- `content_type`
- `file_size`
- `status`
- `page_count`
- `error_message`
- `created_at`
- `updated_at`

### `document_chunks`

- `id`
- `document_id`
- `chunk_index`
- `content`
- `page_number`
- `embedding vector(384)`
- `metadata`
- `created_at`

### `conversations`

- `id`
- `user_id`
- `title`
- `created_at`
- `updated_at`

### `messages`

- `id`
- `conversation_id`
- `role`
- `content`
- `model_name`
- `response_time_ms`
- `created_at`

### `message_sources`

- `id`
- `message_id`
- `chunk_id`
- `similarity_score`
- `rank`

## 7. Planned project structure

```text
rag_knowledge_assistant/
├── app/
│   ├── api/
│   │   ├── dependencies.py
│   │   └── v1/
│   │       ├── auth.py
│   │       ├── documents.py
│   │       ├── search.py
│   │       └── conversations.py
│   ├── core/
│   │   ├── config.py
│   │   ├── exceptions.py
│   │   ├── logging.py
│   │   └── security.py
│   ├── db/
│   │   ├── base.py
│   │   └── session.py
│   ├── models/
│   ├── schemas/
│   ├── repositories/
│   ├── services/
│   │   ├── document_service.py
│   │   ├── extraction_service.py
│   │   ├── chunking_service.py
│   │   ├── embedding_service.py
│   │   ├── retrieval_service.py
│   │   ├── generation_service.py
│   │   └── rag_service.py
│   ├── prompts/
│   │   └── rag_prompt.py
│   └── main.py
├── alembic/
├── tests/
│   ├── unit/
│   └── integration/
├── uploads/
├── scripts/
├── .env.example
├── .gitignore
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## 8. Planned environment variables

```env
APP_NAME=RAG Knowledge Assistant
APP_ENV=development
SECRET_KEY=replace-with-a-secure-secret

DATABASE_URL=postgresql+psycopg://postgres:secret@db:5432/rag_db

HUGGINGFACE_TOKEN=your-token
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
GENERATION_MODEL=selected-hugging-face-model

CHUNK_SIZE=600
CHUNK_OVERLAP=100
RETRIEVAL_TOP_K=5
MAX_FILE_SIZE_MB=10
```

The real `.env` file must never be committed to Git.

## 9. Security requirements

- Secure password hashing
- Expiring JWT access tokens
- File-size and file-type restrictions
- Safe generated storage names
- User ownership verification on every protected resource
- Parameterized database queries
- No committed tokens or secrets
- Prompt-injection defenses
- Context and output size limits
- Safe error responses without internal details

## 10. MVP scope

The first working release will include:

- Registration and login
- PDF and TXT uploads
- Text extraction and chunking
- Local Hugging Face embeddings
- pgvector storage and retrieval
- Hugging Face-generated answers
- Document and page citations
- Docker Compose setup
- Basic automated tests

The following features are postponed until the MVP is stable:

- Frontend
- OCR for scanned PDFs
- DOCX and website ingestion
- Background task queues
- Hybrid search
- Reranking
- Streaming answers
- Admin dashboard
- Cloud deployment

## 11. Future improvements

- DOCX, CSV, and webpage ingestion
- OCR for image-based documents
- Redis and Celery for background processing
- PostgreSQL full-text plus vector hybrid search
- Cross-encoder reranking
- Streaming responses
- Multiple knowledge bases
- Document-level sharing and access control
- RAG monitoring and analytics
- Completely local language-model support
- React frontend
- Cloud deployment

## 12. Implementation order

```text
Foundation
  -> Database and pgvector
  -> Document upload and extraction
  -> Chunking
  -> Embeddings
  -> Retrieval
  -> Answer generation
  -> Authentication and ownership
  -> Conversation history
  -> Testing
  -> Docker hardening
  -> Evaluation
```

## 13. First milestone

The first milestone is complete when:

1. FastAPI runs locally.
2. PostgreSQL runs in Docker.
3. The pgvector extension is enabled.
4. FastAPI connects to PostgreSQL.
5. Alembic migrations run successfully.
6. `GET /api/v1/health` confirms that both the API and database are healthy.
