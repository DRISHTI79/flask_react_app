# Blog Auth App — React Frontend + Flask API Backend

This is a **separate** version of your auth/blog app: a React (Vite) frontend
talking to a Flask REST API backend over JWT tokens. Your original
`flask_auth_app` (Flask + Jinja templates) is untouched — you can run either
one, or both (just use different ports/databases if running simultaneously).

## Architecture

- `backend/` — Flask REST API (JSON only, no HTML rendering). Auth is via
  JWT: on login you get a token, which the frontend stores in `localStorage`
  and sends as `Authorization: Bearer <token>` on every request.
- `frontend/` — React app (Vite + React Router + Axios) that consumes the API.

They run as two separate processes on two separate ports:
- Backend: `http://localhost:5000`
- Frontend: `http://localhost:5173`

## 1. Backend setup

```bash
cd backend
pip install -r requirements.txt
```

Create the database (same schema as before — safe to reuse your existing
`auth_app` database, or point `DB_NAME` at a new one):
```bash
mysql -u root -p < schema.sql
```

Set your DB credentials (same as your original app):
```bash
export DB_HOST=localhost
export DB_USER=root
export DB_PASSWORD=your_mysql_password
export DB_NAME=auth_app
export SECRET_KEY=some-random-secret-string
```

Run the API:
```bash
python app.py
```
It starts on `http://localhost:5000`.

## 2. Frontend setup

In a **new terminal**:
```bash
cd frontend
npm install
npm run dev
```
It starts on `http://localhost:5173`. Open that URL in your browser.

## How it works

- `POST /api/register` — create account
- `POST /api/login` — returns `{ token, user }`
- `GET /api/me` — current user (requires token)
- `GET /api/blogs` — list your posts
- `POST /api/blogs` — create a post
- `GET /api/blogs/:id` — view one post
- `PUT /api/blogs/:id` — update a post
- `DELETE /api/blogs/:id` — delete a post

All `/api/blogs*` routes require the `Authorization: Bearer <token>` header
and are automatically scoped to the logged-in user.

## Notes

- If your frontend runs on a different port than `5173`, update
  `FRONTEND_ORIGIN` in the backend (env var) and the `API_BASE_URL` in
  `frontend/src/api.js`.
- Tokens expire after 24 hours (`TOKEN_EXP_HOURS` in `app.py`); after that
  the user is redirected to the login page automatically.
- For production: don't hardcode `SECRET_KEY`, run `npm run build` and serve
  the static `dist/` files, and put the Flask API behind gunicorn/nginx.
