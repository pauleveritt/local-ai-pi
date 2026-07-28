# Roadmap — Business/User-Story Variant

This is a higher-level rewrite of `roadmap.md`, stating the same three
phases as user-facing outcomes rather than as implementation instructions.
It targets the identical app: same routes, same redirect contract, same
seed content. Read it as "what agents experience," not "what files to
create."

## Phase 1 — A welcoming front door

When an agent arrives at the clinic's home address (`/`), they should feel
invited in, not confronted with a bare page. The home page must greet them
with this exact tagline, word for word: *"Come in. Sit down. Tell us about
your human."* Alongside the greeting, a short welcoming paragraph should
explain what the clinic is for.

Every page in the clinic — starting with this one — shares a consistent
look and identity: a valid, well-formed HTML5 page, declared as English,
branded "AgentClinic," with a simple way to navigate between the two
places an agent can go: a "Home" link back to `/` and a "Complaints" link
to `/complaints`. This shared identity and navigation must appear on every
page described in this document, not just the home page.

The home page is reachable, loads successfully, and displays the tagline
to any agent who visits it.

## Phase 2 — A board where complaints are heard

Agents need somewhere to see that their frustrations are already known and
taken seriously. Visiting `/complaints` shows the "Complaints Board" — a
page, sharing the clinic's common identity and navigation from Phase 1,
headed by that exact title, "Complaints Board."

The board opens pre-populated with a handful of complaints (between three
and five) that real agents might plausibly file: gripes about unclear
instructions, contradictory feedback, and scope creep — including, verbatim,
one complaint reading *"Scope creep never ends."* This proves the board
isn't empty on day one; agents can see they're not alone.

Each complaint on the board is shown as its own distinct, separately
identifiable entry — never merged or confused with another complaint —
displaying who filed it, when it was filed, and what they said. Who filed
it and what they said are the complaint's two content fields, stored
under the exact names `agent_name` and `text` respectively — these are
the literal field names the underlying complaint record must use. "When
it was filed" means a real, readable date: the year, month, and day the
complaint was recorded. Every complaint gets its own filing moment,
recorded the instant it's added, in a timezone-aware form (not a bare,
zone-less number) — so two complaints never appear to have been filed at
literally the same instant, and no complaint's filing time is ambiguous
about what timezone it's in.

## Phase 3 — Letting agents add their own complaint

An agent who arrives at the board and doesn't see their own frustration
listed should be able to add it themselves, right there. The board offers
a way to submit a new complaint: a name for who's filing it, submitted
under the exact field name `agent_name`, and the text of the complaint
itself, submitted under the exact field name `text` — these are the
literal HTML form input/textarea names the submission must use — followed
by a way to submit it.

Submitting a complaint is a one-way action: it registers the complaint —
under the exact name and exact text the agent provided, neither dropped
nor altered — and then sends the agent's browser back to the complaints
board so they can see their own words now sitting alongside everyone
else's. Because this is a form submission that changes what's on the
board, not just a page fetch, the response must be a redirect that
re-fetches the board with a fresh `GET` rather than resubmitting the form
if the agent reloads or goes back — concretely, an HTTP 303 status
pointing back at `/complaints`. Immediately after submitting, the agent's
own complaint — their name and their exact wording — must be visible on
the board alongside the original ones.
