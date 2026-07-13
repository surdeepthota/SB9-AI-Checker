# PeachCheck frontend

React + Vite UI for the PeachCheck trust pipeline. See the repository root
[README](../README.md) for the full project documentation, setup, and demo script.

```bash
npm ci
npm run dev     # dev server on :5173, proxies API calls to the backend on :8000
npm run build   # production bundle (served by FastAPI in the Docker image)
npm run lint    # oxlint
```

Design rule carried over from the backend: components render the trust report and
nothing else — every fact shown was written by a pipeline layer server-side, and the
UI never re-derives a verdict.
