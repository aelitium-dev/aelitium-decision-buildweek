# Frontend

The Next.js Decision Console implements the first three spec §8 screens:

1. Case and evidence view, including citations and the post-F5 evidence diff
2. Human approval view with permitted/prohibited actions and a declared identity
3. Receipt, verification, and the EUR 18,000 → EUR 14,000 tamper demonstration

The Decision Timeline remains D3 scope; a dashboard or queue is optional only
after the vertical workflow remains green.

The historical Command Center is visual reference only. No source component,
style, markup, fixture, or media is copied into this directory.

Install and run:

```bash
npm install
npm run dev
```

The browser calls `/api/backend/*`; Next rewrites that path to
`http://127.0.0.1:8000` by default. Set `AELITIUM_API_BASE_URL` before starting
Next to use a different backend origin. No API key is needed for the DEMO path.

Development output is isolated under `.next-dev/`; production builds use
`.next/`. This prevents `next dev` and `next build` from mixing React Client
Manifests and Webpack chunks when validation builds run during a visual session.
