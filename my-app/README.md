# BauChess viewer

React/Vite game review dashboard, local Node API, and Electron entry point for BauChess.

See the [project README](../README.md) for the full pipeline, configuration, and setup.

```bash
npm ci
npm run backend  # API on 127.0.0.1:8000
# In another terminal:
npm run dev      # Viewer on localhost:5173
```

For Electron, stop the separate API, run `npm run build`, then `npm run desktop`.
Run `npm run check` for lint and the production build. Both the Node API and Vite read the repository-root `.env`; keep it private.
