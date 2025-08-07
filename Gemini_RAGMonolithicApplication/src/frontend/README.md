# Gemini RAG Frontend (Create React App)

This frontend uses [Create React App (CRA)](https://create-react-app.dev/) for local development and builds.

## Development

Install dependencies:
```bash
npm install
```

Start the development server (auto-opens at http://localhost:3000 or next free port):

```bash
npm start
```

## Building for Production

```bash
npm run build
```

The production build will appear in the `build/` directory.
To serve it using the FastAPI backend, copy the contents of `build/` to `../static/`.

## Directory Structure

- `src/` - React source code (components, pages, styles)
- `public/` - Static files and `index.html`

---

**Previous Vite scripts/config have been replaced by CRA.**
