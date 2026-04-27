# Compass OS

Compass OS is a single-page web app for reflection, decision-making, adaptive thinking lenses, progress tracking, custom lenses, and life planning.

## What is in this folder

- `index.html`: the app
- `manifest.webmanifest`, `sw.js`, `icon.svg`: installable mobile/PWA support
- `app-config.example.js`: copy this to `app-config.js` and add your Supabase values
- `supabase-schema.sql`: database schema and row-level security for cloud save
- `vercel.json`: simple static deploy config for Vercel

## Current public links

- Live preview: https://raw.githack.com/Lj1372/thinkos/compass-os-live/index.html
- GitHub branch: https://github.com/Lj1372/thinkos/tree/compass-os-live
- Pull request target: https://github.com/Lj1372/thinkos/pull/new/compass-os-live
- One-click Vercel import: https://vercel.com/new/clone?repository-url=https://github.com/Lj1372/thinkos&project-name=compass-os&repository-name=thinkos&production-branch=compass-os-live

## Mobile note

- `raw.githack` is only a quick preview host and can be flaky on phones.
- For a stable mobile-friendly share link, deploy the `compass-os-live` branch to Vercel.

## Back it up right now

1. Keep this whole folder in a cloud-synced drive or Git repository.
2. In the app, use `Export backup JSON` often.
3. Copy `app-config.example.js` to `app-config.js` when you are ready to enable login and cloud sync.

## Make login and cloud sync work

1. Create a Supabase project.
2. In Supabase SQL editor, run `supabase-schema.sql`.
3. In Supabase Auth settings:
   - enable Email / Magic Link
   - set your Site URL to your live domain
   - add your live domain and preview domain as redirect URLs
4. Copy `app-config.example.js` to `app-config.js`.
5. Replace the placeholder URL and key with your Supabase project URL and publishable key.

Official docs:

- Supabase Auth: https://supabase.com/docs/guides/auth
- Supabase passwordless email login: https://supabase.com/docs/guides/auth/auth-magic-link
- Supabase RLS: https://supabase.com/docs/guides/database/postgres/row-level-security

## Deploy a shareable link

### Vercel

1. Open the one-click import link above, or import `Lj1372/thinkos` in Vercel manually.
2. When Vercel asks which branch to use, select `compass-os-live` first if you want to keep `main` untouched.
3. Deploy the static app with the default settings.
4. Copy the generated `*.vercel.app` URL into `app-config.js` as `publicAppUrl`.
5. Add that same URL to Supabase Auth site URL and redirect URLs.
6. Redeploy after adding your Supabase keys.

### Recommended production setup

1. Use the `compass-os-live` branch first if you want to keep `main` untouched.
2. After Vercel is connected, create:
   - a preview deployment from the branch
   - a production deployment after you are happy with the preview
3. Add `app-config.js` values before your final production deploy.

Official docs:

- Vercel deploys: https://vercel.com/docs/deployments
- Import an existing project: https://vercel.com/docs/getting-started-with-vercel/import
- Git deployments: https://vercel.com/docs/deployments/git

## Mobile and desktop

- The app is responsive and works in mobile browsers.
- The web manifest and service worker make it installable as a PWA on supported devices.
- After deployment, open it on phone or desktop and use browser install/add-to-home-screen.

## Important note

This app works locally without cloud sync because it uses browser storage. To avoid losing progress, use both:

- JSON export backups
- Supabase cloud sync after login is configured
