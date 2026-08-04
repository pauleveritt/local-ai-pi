# Roadmap — Business/User-Story Variant

This states the same milestone as `roadmap.md` in terms of user-facing
outcomes rather than implementation instructions. It targets the identical
application: same route, same wording, same shared layout. Read it as "what
agents experience," not "what files to create."

## Phase 1 — A welcoming front door

When an agent arrives at the clinic's home address (`/`), they should feel
invited in, not confronted with a bare page.

### View: the home page

- **Reachable**: loads successfully at `/` for any agent who visits it.
- **Tagline**: greets the agent with this exact text, word for word —
  *"Come in. Sit down. Tell us about your human."*
- **Welcome**: alongside the greeting, a short welcoming paragraph
  explains what the clinic is for.

### View: shared page identity

- **Every page in the clinic** — starting with this one — shares this
  identity, not just the home page.
- **Markup**: a valid, well-formed HTML5 page, declared as English.
- **Branding**: "AgentClinic."
- **Navigation**: a simple way to reach the two places an agent can go —
  a "Home" link back to `/` and a "Complaints" link to `/complaints`.

## Environment

- Everything you need is already installed. Do not install anything.
- Run the tests with `python -m pytest` from the project root.
