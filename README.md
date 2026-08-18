# FastAPI Blog

A small blog application built with **FastAPI**, **async SQLAlchemy 2.0** and **SQLite**, serving both:

- a **server-rendered site** (Jinja2 + Bootstrap 5) for reading posts, and
- a **JSON REST API** under `/api` with auto-generated OpenAPI docs.

It is a learning/tutorial project, a FastAPI take on the classic Flask blog, built up commit by commit: templates first, then the database layer, then full CRUD, then a refactor to fully async SQLAlchemy.

---

## Features

- Async end to end: `async def` routes, `AsyncSession`, `aiosqlite` driver
- SQLAlchemy 2.0 declarative models with typed `Mapped[...]` columns
- Pydantic v2 schemas for request validation and response serialization (`EmailStr`, field constraints)
- Users and posts with a one-to-many relationship (deleting a user cascades to their posts)
- Eager loading via `selectinload` to avoid lazy-load errors in async context
- Content-negotiated error handling: `/api/*` errors return JSON, page routes render an `error.html` page
- Tables are created automatically on startup via the FastAPI `lifespan` handler
- Bootstrap 5 layout with a light/dark/auto theme toggle, PWA manifest and favicons

---

## Project structure

```text
.
├── main.py            # FastAPI app: page routes, API routes, exception handlers
├── database.py        # Async engine, session factory, Base, get_db dependency
├── models.py          # SQLAlchemy models: User, Post
├── schemas.py         # Pydantic schemas: Create / Update / Response
├── templates/         # Jinja2 templates
│   ├── layout.html    # Base layout (navbar, sidebar, footer, theme toggle)
│   ├── home.html      # Post feed
│   ├── post.html      # Single post
│   ├── user_posts.html
│   └── error.html
├── static/            # CSS, JS, icons, default profile picture
├── media/             # Uploaded profile pictures (served at /media)
├── pyproject.toml
└── blog.db            # SQLite database (created on first run)
```

---

## Requirements

- **Python 3.14+** (see [.python-version](.python-version))
- [uv](https://docs.astral.sh/uv/): recommended, the project ships a `uv.lock`

---

## Setup

```bash
git clone <repo-url>
cd FastAPI-Blog

# Install dependencies into a .venv from the lockfile
uv sync

# The media directory is required at startup (StaticFiles mount)
mkdir -p media/profile_pics
```

### Without uv (pip)

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install "fastapi[standard]" sqlalchemy aiosqlite
mkdir -p media/profile_pics
```

No environment variables or config files are needed, the database URL is set in
[database.py:4](database.py#L4) and points at a local `blog.db`, which is created automatically the
first time the app starts.

---

## Running the app

```bash
uv run fastapi dev main.py
```

The app is now at **<http://127.0.0.1:8000>** with auto-reload enabled.

For a production-style run (no reload):

```bash
uv run fastapi run main.py
# or
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## API documentation

FastAPI generates interactive docs from the route signatures and Pydantic schemas:

| URL | Description |
| --- | --- |
| [`/docs`](http://127.0.0.1:8000/docs) | Swagger UI: browse and *try out* every endpoint |
| [`/redoc`](http://127.0.0.1:8000/redoc) | ReDoc: clean, readable reference |
| [`/openapi.json`](http://127.0.0.1:8000/openapi.json) | Raw OpenAPI 3.1 schema |

The HTML page routes are registered with `include_in_schema=False`, so the docs show the JSON API only.

---

## Web pages

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/` | Home: feed of all posts |
| `GET` | `/posts` | Same as `/` |
| `GET` | `/posts/{post_id}` | Single post page |
| `GET` | `/users/{user_id}/posts` | All posts by one user |

Unknown pages and errors render `error.html` with the relevant status code.

---

## API endpoints

All API routes are prefixed with `/api` and speak JSON.

### Users

| Method | Path | Description | Success |
| --- | --- | --- | --- |
| `POST` | `/api/users` | Create a user | `201` |
| `GET` | `/api/users/{user_id}` | Get a single user | `200` |
| `PATCH` | `/api/users/{user_id}` | Partially update a user | `200` |
| `DELETE` | `/api/users/{user_id}` | Delete a user *and all their posts* | `204` |
| `GET` | `/api/users/{user_id}/posts` | List a user's posts | `200` |

### Posts

| Method | Path | Description | Success |
| --- | --- | --- | --- |
| `GET` | `/api/posts` | List all posts | `200` |
| `POST` | `/api/posts` | Create a post | `201` |
| `GET` | `/api/posts/{post_id}` | Get a single post | `200` |
| `PUT` | `/api/posts/{post_id}` | Replace a post (all fields required) | `200` |
| `PATCH` | `/api/posts/{post_id}` | Partially update a post | `200` |
| `DELETE` | `/api/posts/{post_id}` | Delete a post | `204` |

### Error responses

| Status | When |
| --- | --- |
| `400` | Username or email already taken |
| `404` | User or post not found |
| `422` | Request body fails validation (bad email, empty title, missing field…) |

---

## Using the API

### Create a user

```bash
curl -X POST http://127.0.0.1:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{"username": "sanjeev", "email": "sanjeev@example.com"}'
```

```json
{
  "username": "sanjeev",
  "email": "sanjeev@example.com",
  "id": 1,
  "image_file": null,
  "image_path": "/static/profile_pics/default.jpg"
}
```

`image_path` is a computed property: it falls back to the default avatar when the user has no
`image_file`, otherwise it points at `/media/profile_pics/<image_file>`.

### Create a post

`user_id` is currently supplied in the request body, once authentication exists it will come from
the logged-in user instead (see [schemas.py:41](schemas.py#L41)).

```bash
curl -X POST http://127.0.0.1:8000/api/posts \
  -H "Content-Type: application/json" \
  -d '{"title": "Hello FastAPI", "content": "My first post.", "user_id": 1}'
```

```json
{
  "title": "Hello FastAPI",
  "content": "My first post.",
  "id": 1,
  "user_id": 1,
  "date_posted": "2026-08-17T19:42:05.123456Z",
  "author": {
    "username": "sanjeev",
    "email": "sanjeev@example.com",
    "id": 1,
    "image_file": null,
    "image_path": "/static/profile_pics/default.jpg"
  }
}
```

### List and read posts

```bash
curl http://127.0.0.1:8000/api/posts
curl http://127.0.0.1:8000/api/posts/1
curl http://127.0.0.1:8000/api/users/1/posts
```

### Update a post

```bash
# Partial update — send only what changes
curl -X PATCH http://127.0.0.1:8000/api/posts/1 \
  -H "Content-Type: application/json" \
  -d '{"title": "Hello FastAPI (edited)"}'

# Full replace — title, content and user_id all required
curl -X PUT http://127.0.0.1:8000/api/posts/1 \
  -H "Content-Type: application/json" \
  -d '{"title": "New title", "content": "New content.", "user_id": 1}'
```

### Update a user

```bash
curl -X PATCH http://127.0.0.1:8000/api/users/1 \
  -H "Content-Type: application/json" \
  -d '{"username": "sanjeevz", "image_file": "sanjeevz.jpg"}'
```

### Delete

```bash
curl -X DELETE http://127.0.0.1:8000/api/posts/1   # 204 No Content
curl -X DELETE http://127.0.0.1:8000/api/users/1   # 204, also removes their posts
```

---

## Data model

**User**: [models.py:11](models.py#L11)

| Field | Type | Notes |
| --- | --- | --- |
| `id` | int | Primary key |
| `username` | str(50) | Unique, required |
| `email` | str(120) | Unique, required, validated as an email |
| `image_file` | str(200) | Optional profile picture filename |
| `posts` | list[Post] | `cascade="all, delete-orphan"` |

**Post**: [models.py:34](models.py#L34)

| Field | Type | Notes |
| --- | --- | --- |
| `id` | int | Primary key |
| `title` | str(100) | Required |
| `content` | Text | Required |
| `user_id` | int | FK → `users.id`, indexed |
| `date_posted` | datetime | Defaults to UTC now |
| `author` | User | Back-reference |

---

## Notes and limitations

This is a work in progress. Known gaps:

- **No authentication or authorization.** Anyone can create, edit or delete anything; the Login /
  Register buttons and the post Edit/Delete actions in the UI are placeholders.
- **`user_id` in the post body** is a stand-in for the authenticated user.
- **No migrations.** `Base.metadata.create_all` runs on startup, which creates missing tables but
  never alters existing ones, if you change a model, delete `blog.db` and restart (or add Alembic).
- **No pagination** on `GET /api/posts` or the home feed.
- **No profile-picture upload endpoint yet**, `image_file` is set by writing the filename directly.
- **No tests.**

`blog.db` is currently untracked but not ignored; add it to [.gitignore](.gitignore) if you don't
want to commit your local data.

---

## Roadmap

- [ ] User registration, login and sessions/JWT
- [ ] Authorization: only authors can edit or delete their own posts
- [ ] HTML forms for creating and editing posts
- [ ] Profile picture upload endpoint
- [ ] Pagination
- [ ] Alembic migrations
- [ ] Tests with `pytest` + `httpx`
