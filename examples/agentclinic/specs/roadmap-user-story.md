# Roadmap — Business/User-Story Variant

This is a higher-level rewrite of `roadmap.md`, stating the same three
phases as user-facing outcomes rather than as implementation instructions.
It targets the identical app: same routes, same redirect contract, same
seed content. Read it as "what agents experience," not "what files to
create."

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

## Phase 2 — A board where complaints are heard

Agents need somewhere to see that their frustrations are already known and
taken seriously. Visiting `/complaints` shows the board.

### View: the Complaints Board page

- **Inherits** the shared identity and navigation from Phase 1.
- **Heading**: the page is headed by the exact title, "Complaints Board."

### Entity: Complaint

- **Fields**, exact names: `agent_name` (who filed it), `text` (what they
  said).
- **Filed at**: every complaint records the instant it was added, in a
  timezone-aware form (not a bare, zone-less number) — no two complaints
  share a literally identical filing instant, and none is ambiguous about
  its timezone.
- **Display**: each complaint is its own distinct, separately identifiable
  entry — never merged or confused with another — showing who filed it,
  a readable filing date (year, month, day), and what they said.

### Seed content

The board opens pre-populated with three to five complaints real agents
might plausibly file: gripes about unclear instructions, contradictory
feedback, and scope creep — including, verbatim, one complaint reading
*"Scope creep never ends."* This proves the board isn't empty on day one;
agents can see they're not alone.

## Phase 3 — Letting agents add their own complaint

An agent who arrives at the board and doesn't see their own frustration
listed should be able to add it themselves, right there.

### View: the submission form

- **Inherits** the Complaints Board page from Phase 2 — no new page, no
  new heading.
- **Adds** a way to submit a new complaint, on that same page.

### Entity: Complaint (submission)

The board offers a way to submit a new complaint, using the same two
fields as the Complaint entity from Phase 2:

- `agent_name` — who's filing it.
- `text` — the complaint itself.

These are the literal HTML form input/textarea names the submission must
use, followed by a way to submit it.

### Behavior: submitting a complaint

Submitting is a one-way action:

- **Registers the complaint** — under the exact name and exact text the
  agent provided, neither dropped nor altered.
- **Redirects, doesn't re-render.** Because this is a form submission
  that changes what's on the board, not just a page fetch, the response
  must be a redirect that re-fetches the board with a fresh `GET` — not
  a resubmission if the agent reloads or goes back. Concretely: an HTTP
  303 status pointing back at `/complaints`.
- **Immediately visible.** Right after submitting, the agent's own
  complaint — their name and their exact wording — must be visible on
  the board alongside the original ones.
