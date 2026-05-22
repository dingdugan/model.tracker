# Security Policy

## Reporting a vulnerability

If you find a security issue, please **do not** open a public GitHub issue.

Instead, open a [security advisory](https://github.com/dingdugan/model.tracker/security/advisories/new) on the repository, or contact the maintainer privately.

We will acknowledge within 72 hours.

## What's in scope

- Server-side request forgery in scrapers (we fetch arbitrary URLs)
- Leakage of Supabase service-role keys via GitHub Actions logs
- Cross-site scripting in vendor-supplied content rendered on the frontend
- Prompt-injection vectors that could cause the LLM extractor to misbehave

## What's out of scope

- Inaccurate model metadata or pricing — open a regular issue
- Public anon-key visibility in browser bundle — this is by design (RLS allows
  public reads only). See `supabase/migrations/0001_initial.sql` for policies.
