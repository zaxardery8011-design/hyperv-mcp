# Release Plan — hyperv-mcp v0.1 Public Launch (Day 31-60)

This is the operational playbook for taking the v0.1 spike from a local repo to a publicly-discoverable MCP server in the 30-day window from **2026-06-23** (Day 31) to **2026-07-22** (Day 60). It is *not* the engineering roadmap — see `release_roadmap.md` for code milestones.

> **Day 1 = 2026-05-24** (the day the v0.1 spike landed). Days 2-30 are reserved for v0.2 real-cmdlet integration, which is a prerequisite for most launch moves below.

## Why a launch window matters

Per `project_monetize_path_B_2026-05-10`, the strategic window for Windows + GPU + on-prem agentic tooling is **9-15 months** before Win365 for Agents goes GA. First-mover MCP standard-setting only pays off if there's adoption-time *before* the incumbent ships. Day 31-60 is when v0.2 is wired and we go from "scaffold visible to the BAE team" to "scaffold visible to the open-source MCP community."

## Pre-flight checklist (must clear before Day 31)

- [ ] v0.2 wired (real `Get-VM` / `Start-VM` / `Stop-VM` / `Checkpoint-VM` / metric counters). Mock mode still works behind `HYPERV_MCP_MODE=mock`.
- [ ] PyPI package published: `pip install hyperv-mcp` works on a fresh Windows venv.
- [ ] CI green on `windows-latest` matrix (Python 3.10, 3.11, 3.12) — mock test 3/3 + ruff + PowerShell parse-check.
- [ ] One live-host integration test passing on a clean Hyper-V Server 2025 install.
- [ ] Repo is public on GitHub (`github.com/zaxardery8011-design/hyperv-mcp`). README badges resolve, License visible.
- [ ] Demo VM screen-recording (~90 sec): "Claude Code lists my VMs → snapshots LINC-01 → starts LINC-02" — for embedding in the blog post.
- [ ] CHANGELOG `[0.2.0]` section drafted with breaking changes (if any) called out.

## Day 31 — Soft launch (GitHub public + Anthropic MCP community marketplace)

**Goal**: get a discoverable URL before any noisy outbound posts.

- Flip the GitHub repo from private to public. Pin issues: "v0.2 testers needed", "v1.0 GPU-PV hardware donations welcome".
- Submit to the **Anthropic MCP community marketplace** / awesome-mcp lists. As of 2026-Q2 the actual Anthropic registry is invite-only — community marketplace (community-maintained `awesome-mcp-servers` lists on GitHub) is the early-stage discovery channel. Submit a PR adding `hyperv-mcp` to:
  - `modelcontextprotocol/servers` (official registry) — submit as a community server entry.
  - `punkpeye/awesome-mcp-servers` (the largest community list).
  - `wong2/awesome-mcp-servers` (secondary list).
- Open a "Discussions" thread on the GitHub repo titled "v0.2 testing wanted — Hyper-V on Server 2025 / Win 11 Pro" to give early testers a place to land.

## Day 32-34 — Tier 0 audience: AIWFF /雷神 internal

- Internal Slack / Discord / DM pings to 5-10 people known to run Hyper-V + Claude Code (雷神 V2.0 operators are the natural first ring).
- Capture their first install friction. Triage anything blocking into a "Day 35 patch" milestone.
- Day 33 cut a `v0.2.1` if any blocker landed. Day 34 verify CI still green.

## Day 35-37 — Blog post + demo recording

- **Blog post** (~1500 words, target hosting on `aiwff.dev` or a personal Substack — wherever long-form lives):
  - Title (working): *"hyperv-mcp: a first-class Hyper-V control plane for Claude Code"*.
  - Outline:
    1. Why no Hyper-V MCP server exists today (Top 20 MCP ecosystem gap analysis).
    2. The five-tool design + the JSON-RPC error envelope choice.
    3. Live demo embed (~90 s GIF or video): list → snapshot → start → metric.
    4. Open-core trajectory — what's free forever, what's commercial in v1.1.
    5. How to install + register with Claude Code in 60 seconds.
  - Tone: technical first-person. No marketing fluff; let the demo do the selling.
- **Demo GIF**: 90 seconds, ScreenToGif or asciinema → mp4. Hosted on GitHub release assets, embedded into the README and the blog.

## Day 38 — Show HN

- **Title format**: *"Show HN: hyperv-mcp – MCP server for Microsoft Hyper-V VM lifecycle"*.
- Post **Tuesday 09:00 PT** for peak HN engagement (per Show HN analytics across 2024-2026; weekday morning consistently outperforms evening).
- First comment is mandatory: link to the demo GIF, list the five tools, state what's mock vs live, link to the blog post.
- Reserve the next 6 hours for response. Treat every "this doesn't work for me on $SKU" as a CI gap and file an issue *during* the thread, not after — visible responsiveness matters more than the answer.
- Do **not** cross-post to Reddit or Lobsters on the same day.

## Day 39-40 — Reddit (`r/sysadmin`, `r/HomeServer`, `r/PowerShell`)

- **r/sysadmin** (~900k subs as of 2026-Q1): post title *"I built an MCP server for Hyper-V so Claude can manage my VMs — feedback wanted"*. Angle: practical sysadmin workflow (snapshot before patch Tuesday, fleet of Server 2025 VMs).
- **r/HomeServer / r/homelab**: angle on the GPU-PV roadmap — homelab GPU passthrough crowd is the most receptive audience for v1.0.
- **r/PowerShell**: angle on the cmdlet wrapper layer — show that `tools/*.ps1` is a clean reusable boundary anyone can extend.
- Stagger posts across 48 hours (one per day) to avoid the spam classifier and to spread maintainer response load.
- Do **not** post to `r/MicrosoftFlow` (off-topic) or `r/programming` (too broad — gets buried).

## Day 41-44 — Community follow-through

- Respond to every issue / PR within 24h. Backlog visibly is fine; *silence* is not.
- If a community PR lands and is mergeable: merge same-day, tag a `v0.2.x` patch, update CHANGELOG.
- Refresh the GitHub Discussions thread daily with a short status update.
- Capture interesting feedback into `release_roadmap.md` notes — these become v0.3 priorities.

## Day 45-50 — Tier 2 outreach

- **Anthropic Discord** `#mcp-servers` channel: drop a one-line announcement with the GitHub link and a short list of the five tools. Don't repost — once is fine.
- **Hyper-V community**: post on `learn.microsoft.com/answers` Hyper-V tag with a "feedback wanted from Hyper-V admins" framing. Avoid spam-flag — make the post genuinely useful (link the spec, ask whether a missing tool would be valuable).
- **Twitter / X / Bluesky**: one technical thread (8-12 posts), screencap-heavy. Tag `@anthropicai` and `@modelcontext` if accounts exist. Cross-post the thread to LinkedIn.
- **HN follow-up**: if the original Show HN landed on the front page, write a 2-week retrospective thread for `r/programming` summarizing what we learned. If it flopped, skip.

## Day 51-55 — Conversion to repeat usage

- Add **two case studies** to the blog: one homelab user, one studio operator. Real stories beat marketing copy. Get permission, anonymize VM names, leave the workflow intact.
- Open a **`v0.3` design RFC** GitHub Discussion: notification semantics, Streamable HTTP transport, optional Server Card. Invite the early users to weigh in by name.
- Cut a tagged `v0.2.5` (or whatever the cumulative patch level is) with all the Day 39-50 feedback rolled in. Pin it in the README as "what most folks should install".

## Day 56-60 — Inflection check and decision

Decision gate: **is v1.0 still worth the engineering investment?**

Trigger thresholds (any one of):

- ≥ 50 GitHub stars *and* ≥ 3 external committers, or
- ≥ 2 enterprise pilot conversations (any pipeline), or
- mention in an Anthropic / MS / community blog post.

If yes → start v0.3 implementation immediately, slot v1.0 (GPU-PV + SR-IOV) for 2026-Q3.

If no → pause new feature work, focus on v0.2 reliability and watch the BAE P1 timeline for the Win365 for Agents announcement. Re-evaluate at Day 90.

## Anti-patterns to avoid

- **No "release announcement" tweet on Day 31.** The GitHub repo going public is not news. The Day 38 Show HN with a demo is.
- **No Reddit cross-posts in a single day.** That triggers spam filters and burns the audience.
- **No paid promotion.** Pre-product-market-fit, paid traffic teaches you nothing.
- **No comparison-table dunks on `terraform-mcp`.** Positioning matters; keep the framing as "different shape, complementary" (the `positioning.md` line).
- **No begging for stars.** Demo asset > demo ask.

## Owner / cadence

Single maintainer for v0.1-v0.2. Daily 15-minute triage during Day 31-50. Drops to weekly after Day 50.

## Open questions / decisions deferred to launch week

- Twitter / X handle vs Bluesky vs both (default: just Bluesky + a cross-post; X audience for sysadmin / MSPs is unclear in 2026).
- Whether to mirror the GitHub repo on Codeberg as a hedge (default: not for v0.1; revisit at v1.0).
- Whether the blog post should be guest-posted on someone else's higher-traffic blog (default: own it on `aiwff.dev`; outreach blog comes later).

## Success metric to track from Day 31

| Metric | How measured | Day 60 target |
|---|---|---|
| Unique installs | PyPI download count + GitHub clone events | 200+ |
| GitHub stars | GitHub | 100+ |
| External PRs merged | GitHub | 3+ |
| Live-host bug reports (vs install-friction) | GitHub Issues triage label | ≥ 5 substantive issues |
| Blog post traffic | hosting analytics | 2000+ unique reads |

These targets are aggressive but in-range for a Show HN front-page + Reddit double-tap. Missing them by 2x is still a viable trajectory; missing them by 10x is the signal to pivot to commercial-direct outreach instead.
