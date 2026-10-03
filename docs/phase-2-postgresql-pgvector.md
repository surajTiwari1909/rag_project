# Phase 2: PostgreSQL and pgvector

This document explains what was implemented in Phase 2 of the `rag_knowledge_assistant` project, why each step was needed, and how the pieces work together.

## Phase 2 Goal

The goal of Phase 2 was to move the project from a FastAPI-only foundation into a database-backed application that can:

- run PostgreSQL locally through Docker Compose
- enable the PostgreSQL `vector` extension
- connect to PostgreSQL from the FastAPI application
- manage schema changes through Alembic migrations
- create a real table that contains a `vector(384)` column
- prove that a vector value can be written to and read back from the database

In short, Phase 2 established the full database foundation for later RAG features.

## Key Definitions

### PostgreSQL

PostgreSQL is a relational database management system. It stores structured data in tables and supports SQL queries, indexing, JSON, transactions, and extensions.

In this project, PostgreSQL is the primary database used to store application data.

### pgvector

`pgvector` is a PostgreSQL extension that adds support for vector data types and vector similarity operations.

A vector is an ordered list of numbers, for example:

```text
[0.12, -0.04, 0.88, ...]
```

In retrieval-augmented generation systems, text is converted into embeddings, and embeddings are stored as vectors. Later, similarity search can compare one vector to another to retrieve the most relevant chunks.

### Embedding

An embedding is a numerical representation of text. Similar text tends to produce similar vectors.

In this project, Phase 2 prepared the database to store embeddings with dimension `384`.

### SQLAlchemy

SQLAlchemy is the Python database toolkit and ORM layer used by the application.

In this project, SQLAlchemy is responsible for:

- building the database engine
- managing database sessions
- defining database models in later phases
- connecting FastAPI code to PostgreSQL

### Alembic

Alembic is the migration tool used with SQLAlchemy.

A migration is a versioned, repeatable database schema change. Instead of manually creating tables in PostgreSQL, migrations record each schema change in code.

In this project, Alembic is responsible for:

- enabling the `vector` extension
- creating the initial database table
- tracking schema version history

## What Was Done in Phase 2

Phase 2 was completed in several focused steps.

### Step 1: Docker Compose for PostgreSQL and pgvector

A new file was added:

- `docker-compose.yml`

This file defines a `postgres` service using the image:

```yaml
pgvector/pgvector:pg17
```

This image is important because it provides PostgreSQL with pgvector support already installed in the image.

The Compose file does the following:

- starts a PostgreSQL container
- sets the database name, username, and password
- maps a host port to container port `5432`
- creates a persistent Docker volume for database storage
- adds a healthcheck using `pg_isready`

This step gave the project a local PostgreSQL runtime.

### Step 2: Database Environment Variables

The environment configuration was extended with PostgreSQL-related settings.

Files involved:

- `.env`
- `.env.example`

Variables added:

- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`
- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `DB_ECHO`
- `VECTOR_DIMENSION`

These variables are used for two purposes:

1. Docker Compose uses them to configure the PostgreSQL container.
2. The FastAPI application uses them to connect to the same database.

This keeps the infrastructure and application configuration aligned.

### Step 3: Centralized Database Configuration in FastAPI

File involved:

- `app/core/config.py`

This file already handled Phase 1 settings. In Phase 2 it was extended to include database settings.

The `Settings` class now contains the PostgreSQL fields and a computed property:

- `sqlalchemy_database_uri`

This property builds a connection string in the form:

```text
postgresql+psycopg://user:password@host:port/database
```

This is the central database URL used by the application and Alembic.

### Step 4: Database Dependencies

File involved:

- `requirements.txt`

Phase 2 added these dependencies:

- `SQLAlchemy`
- `psycopg`
- `pgvector`
- `alembic`

Why they were needed:

- `SQLAlchemy` provides engine and session management.
- `psycopg` is the PostgreSQL driver.
- `pgvector` provides vector type support in Python and SQLAlchemy.
- `alembic` manages schema migrations.

### Step 5: Database Package Foundation

A new package was added:

- `app/db/`

Files added:

- `app/db/__init__.py`
- `app/db/base.py`
- `app/db/session.py`

#### `app/db/base.py`

This file defines the shared SQLAlchemy declarative base.

Purpose:

- future database models inherit from this base
- Alembic uses the base metadata to understand the schema

#### `app/db/session.py`

This file defines the application’s database access foundation.

It contains:

- the SQLAlchemy `engine`
- the `SessionLocal` session factory
- the `get_db_session()` helper
- the `check_database_connection()` startup check

Conceptually:

- `engine` manages database connectivity and the connection pool
- `SessionLocal` creates session objects
- `get_db_session()` safely opens and closes a session
- `check_database_connection()` verifies the app can reach PostgreSQL

This step created the Python-side database layer.

### Step 6: Application Startup Connection Check

Files involved:

- `app/db/session.py`
- `app/main.py`

The FastAPI app was updated to check the database connection during startup using a lifespan hook.

Why this matters:

- if PostgreSQL is unavailable, the app fails early
- configuration issues are caught at startup instead of during requests
- the database is treated as a required application dependency

The actual test used is a simple query:

```sql
SELECT 1
```

This confirms the application can open a real PostgreSQL connection.

### Step 7: Alembic Migration Setup

Files added:

- `alembic.ini`
- `alembic/env.py`
- `alembic/script.py.mako`
- `alembic/README`
- `alembic/versions/`

#### `alembic.ini`

This is Alembic’s top-level configuration file.

It tells Alembic:

- where the migration environment lives
- how logging should work
- what default database URL to use

#### `alembic/env.py`

This is the most important Alembic integration file.

It connects Alembic to the application by:

- loading settings from `app/core/config.py`
- using `settings.sqlalchemy_database_uri`
- loading `Base.metadata` from `app/db/base.py`

That means the migration system and the application share the same database configuration.

#### `alembic/script.py.mako`

This is the template Alembic uses when generating new revision files.

#### `alembic/versions/`

This folder stores the actual revision files.

This step created a proper schema migration system.

### Step 8: Enable the PostgreSQL `vector` Extension

A migration file was added:

- `alembic/versions/20260722_01_enable_pgvector_extension.py`

This migration runs:

```sql
CREATE EXTENSION IF NOT EXISTS vector
```

This step is necessary because having a Docker image with pgvector support is not enough by itself. PostgreSQL still needs the `vector` extension enabled inside the target database.

Without this step, PostgreSQL would not recognize the `vector` type.

### Step 9: Create the Initial Table with a Vector Column

A second migration file was added:

- `alembic/versions/20260722_02_create_document_chunks_table.py`

This migration creates the `document_chunks` table with these columns:

- `id`
- `source_document`
- `chunk_text`
- `metadata_json`
- `embedding`
- `created_at`

The most important column is:

- `embedding vector(384)`

This is the actual proof that the schema supports vector storage.

### Final Verification

After the migrations were applied, the setup was verified by:

- confirming the `vector` extension existed
- confirming the `document_chunks` table existed
- confirming the `embedding` column type was `vector`
- inserting a sample row with a 384-length vector
- reading the row back successfully
- deleting the test row

This completed the Phase 2 acceptance condition.

## Files Added or Updated in Phase 2

### Infrastructure and Configuration

- `docker-compose.yml`
- `.env.example`
- `.env`
- `requirements.txt`
- `app/core/config.py`

### Database Package

- `app/db/__init__.py`
- `app/db/base.py`
- `app/db/session.py`

### Application Integration

- `app/main.py`

### Alembic Migration System

- `alembic.ini`
- `alembic/env.py`
- `alembic/script.py.mako`
- `alembic/README`
- `alembic/versions/20260722_01_enable_pgvector_extension.py`
- `alembic/versions/20260722_02_create_document_chunks_table.py`

## How All Pieces Work Together

The Phase 2 flow is:

1. Docker Compose starts PostgreSQL with a pgvector-capable image.
2. `.env` provides database settings.
3. `app/core/config.py` reads those settings.
4. `app/db/session.py` builds the SQLAlchemy engine and sessions.
5. `app/main.py` verifies database connectivity at startup.
6. Alembic uses the same configuration through `alembic/env.py`.
7. The first migration enables the `vector` extension.
8. The second migration creates the `document_chunks` table.
9. The database can now store and return `vector(384)` values.

This means the project is now prepared for later phases that require:

- storing document chunks
- storing embeddings
- performing vector similarity search
- building RAG retrieval logic

## Why Phase 2 Matters for Later Phases

Phase 2 is the structural bridge between application setup and real RAG behavior.

Without Phase 2:

- there is no persistent database layer
- there is no schema management system
- there is no vector data type
- there is no way to store embeddings properly

With Phase 2 complete:

- PostgreSQL is available locally
- the FastAPI app can connect to it
- schema changes are versioned
- vector storage is supported
- the project is ready for chunk storage and embedding workflows

## Acceptance Condition Achieved

Phase 2 is considered complete when:

- the application connects to PostgreSQL
- the `vector` extension is enabled
- a table contains a `vector(384)` column
- the application can write and read a vector value

That condition was met by the implemented setup and verification.
