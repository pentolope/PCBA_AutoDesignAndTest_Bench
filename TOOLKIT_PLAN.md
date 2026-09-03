# Toolkit plan after eight boards

Written 2026-09-02 against toolkit `PCBA_AutoDesignAndTest @ 3516aa6`, from the
eight `TOOLKIT_REQUEST.md` files of boards 01–08 (~2,780 lines, ~110 line
items), read in full, and `AUTONOMOUS_PCBA_AGENT.md` §§4, 21–26, 30, 32–35.
The phase structure is consistent with the architecture doc's own workstreams
(§33) and capability roadmap (§35); this plan sequences them by the eight
boards' measured evidence.

The toolkit has not moved since board 02 was finished — boards 03–08 were
designed against the same commit and their requests are all still open. The
~110 line items collapse into 33 work packages across six phases.

---

## Diagnosis

**1. The analysis layer is strong; the board-facing layer is thin.**
Board 04 said it best after surveying `pcbqa/`: extraction, propagation,
coupling geometry, claims and closure all exist — and every board hand-rolls
the path to them. Boards 03, 04, 07 and 08 each carry 250–450 lines of
near-identical routing and copper-repair code; board 08 copied board 03's
orientation deriver verbatim minus one line. The plan is mostly not new
physics — it is moving the seams so a board declares instead of implements.

**2. The dangerous seams are the router and the outside world.**
Every "would have shipped a wrong board" trap sits where a board silently
inherits someone else's standards: the vendored router lowering the DRC floor
it is later graded by (04), rewriting design-authored copper (06, 08), a
declared orientation registry the build never applies (03 *and* 08), a
discontinued part nothing checked (01). These get fixed by *enforcing* the
toolkit's standards at the boundary — never by relaxing anything.

**3. The remaining UNKNOWNs cluster in four missing domains.**
Thermal, DC power integrity, conductor current capacity, and reactive (L/C/Z0)
extraction. The architecture doc names all four (§21–24); five boards wrote
their own thermal code or left thermal UNKNOWNs, and
`extract.path_resistance` refuses exactly the nets whose drop matters — poured
power and ground. These close real claims; everything else closes cost.

### Demand, by boards asking

| Capability cluster | Boards |
|---|---|
| Routing pipeline, tidy passes, safe pcbnew mutation | 02 03 04 06 07 08 |
| Reactive extraction (L/C/Z0), post-layout SI | 02 03 04 05 06 08 |
| Claims / requirements / release-policy governance | 01 02 03 04 05 06 |
| Thermal | 01 03 04 06 08 |
| Fabricator-catalog gaps (plating, mask, stackup, spacing) | 03 05 06 07 08 |
| DC power integrity over poured copper | 01 04 05 06 |
| Orientation as a toolkit facility | 02 03 05 08 |
| Manifest schema, discoverability, build coherence | 03 04 07 08 |
| Simulation primitives (isource, .ac, ic, sweep) | 01 03 06 |
| Fast gate evaluation outside full validate | 01 03 07 |
| Conductor / via current capacity | 06 08 |
| Part lifecycle & availability snapshots | 01 02 |

### The four traps that would have shipped wrong hardware

- **T1** — The router lowers the project's DRC floor to the tightest value it
  used, then the board is graded against the relaxed rule — check-weakening
  through the back door (04·A1).
- **T2** — Design-authored copper is ripped and rerouted; connectivity still
  passes, so the loss of a required topology is silent (06·A1, 08·2).
- **T3** — A declared `cpl_orientation` registry is applied only when
  `fab_format` is also declared; otherwise the CPL ships raw angles and the
  build reports success. Hit independently by two boards (03·3, 08·9).
- **T4** — A discontinued part sailed through selection; found by accident
  several iterations later (01·6).

T1–T3 are closed in Phase 0–1; T4 in Phase 4. Each lands with a negative
fixture proving the gate bites.

---

## Program rules

1. **Nothing weakens.** Several requests exist because the toolkit refused
   correctly; the deliverable is always a new model or a new seam, never a
   relaxed threshold. Requests that would strengthen the router boundary
   (T1, T2) are enforcement work.
2. **Genericity holds.** Every capability is manifest-declared, opt-in,
   NOT_APPLICABLE with a reason until declared. `GenericSourceHygiene` stays
   at zero allowlisted names.
3. **Additive versioning.** A consumer pinned to an older commit keeps
   working; new manifest keys never repurpose old ones. The
   missing-block-is-ERROR model stays out (per `CLAUDE.md`) — Phase 2's
   `required_domains` is the sanctioned way to make declining explicit.
4. **No network in a verdict.** Lifecycle, orientation and catalog work all
   follow the `fab refresh` pattern: fetch to scratch, review,
   commit-as-approval, hash-verified at load.
5. **Every new gate ships with proof it bites** — a negative fixture or
   mutation, from Phase 0 onward (04·C3 made this a request; it is the
   standing rule immediately, with the retrofit harness in Phase 5).
6. **Few, coherent toolkit releases.** The toolkit is a closure member, so
   every pin move invalidates all eight boards' committed artifacts. One
   release per phase, followed by one batch rebuild-and-revalidate across the
   bench (WP 0.1 makes that a single command).
7. **Router fixes go upstream.** `KiCadRoutingTools` is vendored and never
   edited in-tree; the wrapper (1.3) defends the boundary now, upstream fixes
   on `pcba-autonomy` move the pin deliberately (1.4).
8. **A request is closed by deletion.** Done means the filing board can delete
   its workaround (paths are named in the request files) and a toolkit test
   covers the behaviour — not a status note.

Sizes: **S** = contained change, one module or gate. **M** = new module or
schema surface, with fixtures. **L** = new subsystem, multiple gates and
fixtures.

---

## Phase 0 — Program enablers

Make toolkit iteration cheap and manifest declarations safe before anything
else lands. Everything here multiplies the value of every later phase.

### 0.1 Closure transparency and batch revalidation — M (02·7, 02·8, 07·15)

Store the closure member map in `fabrication.json`; make `ARCH.PROVENANCE`
report which member differs instead of two bare digests. Add a bench-level
command that rebuilds and revalidates every board whose only stale input is
the toolkit pin.

*Done when* a toolkit release costs one command across the bench, and "your
artifacts are stale" names the input that moved. Do this first: the rest of
the program is a stream of toolkit commits.

### 0.2 Manifest JSON Schema and preflight — M (03·1, 04·A8)

Publish the manifest schema in `schemas/`; `validate`/`build` check against it
before any gate runs and *refuse unknown keys* — the fail-closed rule the
model registry already applies. Refuse output paths outside declared generated
locations. Board 03 called reverse-engineering keys from gate source "the
single largest cost of this board."

*Done when* a misspelled or misplaced key is a named preflight error, not four
gate failures later.

### 0.3 Build coherence: declared-but-unconsumed is an error — S (03·3, 08·9)

A declared capability whose application step is unreachable (the T3 trap:
`cpl_orientation` without `fab_format`) refuses the build, naming the missing
key.

*Done when* the trap two boards hit independently cannot recur for any
capability pair.

### 0.4 Gate discoverability — S (08·10, 03·1, 04·B1)

`run.py gates --missing <manifest>`: every NOT_APPLICABLE gate with the key
that would enable it and the evidence that key needs. Generated gate→key
table; module index grouped by question answered. Board 08 reimplemented three
modules it failed to find.

*Done when* "what would declaring X turn on" is a query, not an archaeology
session.

### 0.5 Gates as a library; fast paths — L (07·5, 07·13, 01·8, 03·6)

Expose gate evaluation over a board file — `gates.evaluate(board, manifest,
only=…)` and `validate --no-build` — so a routing candidate is judged by the
gates that will judge the release, in seconds not tens of minutes. Gates
declare a class (`design` / `release-artifact` / `fixture`) so `--only=design`
replaces board-maintained acceptance lists that rot. Add sub-second
`check-board` (adopted-routing hash + closure digests) and a bench concurrency
guard — board 03 lost an hour to a second session silently replacing its
routed board.

*Done when* "would this board pass `ROUTE.TINY_SEGMENTS`?" costs a second, and
the answer at routing time equals the answer at release time. Keystone for
Phase 1.

### 0.6 Small correctness fixes — S (02·10, 06·C5, 04·A4, 04·A6, 07·7)

`toolkit_identity()` records a failed `git status` as a refusal, not a clean
tree. `geom.configure` errors name the manifest field. `item_id()` helper
returns `m_Uuid.AsString()` everywhere (the SWIG address-reuse trap gave one
board 3 distinct ids across 1190 tracks). Geometry findings carry board-frame
coordinates plus net/layer/KIID/pad; gate messages state their counting rule.

*Done when* a finding resolves to the item it is about without a coordinate
conversion in the reader's head.

---

## Phase 1 — Own the mutation and routing pipeline

The largest duplication and the worst debugging costs in the corpus. Six
boards asked; four carry parallel implementations today. Ends with boards
deleting their `design/route.py`.

### 1.1 `pcbqa.board` — safe pcbnew mutation — L (08·1, 07·2, 07·3, 07·9, 07·10, 06·A2)

One module owning the SWIG hazards no error message reveals:
custody-preserving `discard()` (uuid read first, proxy retained),
`endpoints()` returning copies not aliases, connectivity rebuild-and-retry,
refill-before-connectivity discipline, one-board-per-process sessions with
resumable phases, `open_nets()`, `staged()` (board + library tables + project)
and `drc(board, project)` so scratch-directory checks stop lying. Plus the
documented mutation contract. Board 08: this class of failure "cost more time
than every other item here combined, twice."

*Done when* no board-side code calls `board.Remove`, reads a raw endpoint, or
runs DRC without its project.

### 1.2 Post-route normalization, one definition of "attached" — L (07·1, 07·12, 06·A3, 04·A3, 02·6)

The ~10 board-agnostic tidy passes (snap-to-via, pull-to-pad-anchor, drop
collapsed, fold sub-floor fragments, restore narrowed widths/vias, dedupe,
move via off mask, split at T, prune to fixpoint) become toolkit transforms —
each with the connectivity-invariance guard built in, run to a bounded
fixpoint, reporting what changed into the routing record. The gate and the
transforms share one definition of "attached" (today KiCad connectivity, KiCad
DRC and `ROUTE.GEOMETRY_HYGIENE` disagree three ways). Includes canonical PCB
serialization (uuid5, sorted) and timestamp-free deterministic export, so a
no-op rebuild is byte-identical.

*Done when* a board declares a transform list and tolerances; boards
03/04/07/08 delete their copies; a rebuild that changes no input changes no
bytes.

### 1.3 `pcbqa.route` — the candidate search, owned — L (08·2, 04·A1, 04·A2, 06·A1, 06·A4, 06·A5, 07·6, 07·11, 07·14)

The toolkit runs the loop; the board declares options, orderings, attempt
budget and acceptance predicate. Non-negotiables, each from a real failure:
fab-floor overrides derived from the board's declared constraints on every
invocation, and a candidate *refused* when the router's reported minimum
clearance is below the declared one (T1); authored copper first-class —
locked, `KICAD_RIP_PREEXISTING=0`, verified returned unchanged, refusal not
warning (T2); reserved-net copper restored by text splice; router project-file
rewrites detected as findings; router summary reconciled against adopted-board
connectivity; zone-owning nets always in scope; grid step derived from finest
pad pitch; attempt matrix that refuses two identical attempts; the tree
restored on *any* exit; replay of recorded candidates through changed
transforms without re-searching; `min_segment_mm` single-sourced from the
manifest. Acceptance judges via 0.5's gate library, so routing accepts nothing
release will reject.

*Done when* a board gets an accepted, recorded routing run without owning a
loop, and no board-owned code knows `fab_tiers.py` exists.

### 1.4 Upstream KRT fixes (separate lane) — M (03·5a, 07·6, 06·A1)

Real fixes belong on `pcba-autonomy`, with the pin moved deliberately: honour
or at least report `--clearance`; apply `--same-net-pad-clearance` in
plane-finalize taps; apply the fab floor to emitted fragments, not only
checked ones; make protect-authored-copper an explicit interface rather than a
lock-flag side effect. Until each lands, 1.3's wrapper defends the boundary.

*Done when* the wrapper's defenses become assertions that never fire.

### 1.5 Placement and pour support — M (01·7, 04·A7, 06·B1, 06·B3, 03·5c, 08·11)

`PLACEMENT.COURTYARD` / `PLACEMENT.EDGE_CLEARANCE` as fast in-process checks
documented into the routing acceptance set (a courtyard overlap currently
costs three routed candidates to discover). Footprint geometry queries against
the library before a board exists (courtyard extent, pad-1 position at
rotation). Pour-island reporting with area and stranded pads. The net-wide
stitch-to-plane driver over the existing `stitch_to_plane` primitive — three
boards have written the loop. A documented seed→optimise→adopt placement cycle
for the copper-refusing placer, or `run.py place`.

*Done when* a placement defect is caught in milliseconds, and "which pads
could not be stitched, and why" is one call.

### 1.6 Project-preserving save — S (04·A5)

A save entry point that does not let `pcbnew.SaveBoard` rewrite `.kicad_pro`
severities to KiCad defaults (surfaced as `DRC.NO_SUPPRESSED_RULES` failing on
rules the board never set).

*Done when* no call site has to remember the restore.

---

## Phase 2 — Evidence governance

Six boards asked for pieces of one subsystem: requirements → claims → policy →
release verdict. Design the schema change once, not as four bolt-ons. This is
what makes RELEASE READY mean what it says.

### 2.1 Requirement records: kind, methods, and the enforced join — M (03·7, 06·E1, 04·B7, 05·4)

First-class `kind` (§4: user / derived / assumption / design decision, with
per-kind validation) and `verification_methods` (§26's closed vocabulary,
including naming a method the claim does *not* have as the one required to
close it). A requirements register joined to the claim set in both directions
by a gate — an unregistered requirement and an unjudged registration are both
defects. A verdict shape for "physical validation required" that is neither
FAIL nor a gap-shaped UNKNOWN; per-significance minimum-method policy so
safety-relevant requirements cannot rest on DOCUMENTATION alone.

*Done when* board 06's 67 requirements stop all citing the bare string
`BRIEF.md`, and board 04's connector-mating UNKNOWN reads as the correct
statement "bench test required."

### 2.2 Claim policy for unresolved claims — M (01·1, 02·5)

A `claims` manifest block and `CLAIM.POLICY` gate: every non-PASS verdict
classified; each permitted UNKNOWN enumerated with scope, reason, owner and
review date; a permitted entry that no longer matches a live claim fails, so
stale waivers cannot accumulate. §32 requires exactly this and no board can
express it.

*Done when* "there are some UNKNOWNs" becomes an enumerated, owned, expiring
list that `release-check` reads.

### 2.3 Board-facing claim harness — M (02·5, 06·C4)

Boards register claim evaluators; the toolkit runs them and reports the claim
matrix through `validate`/`release-check` — board 02 hand-rolled 757 lines of
harness that its release commands never see. One shared entry point builds the
model registry a manifest declares, so a board's tests and the gate call the
same code by construction.

*Done when* a board's claims are gate-visible without a private harness.

### 2.4 External and manual release dependencies — S/M (04·B6, 05·5, 06·E2, 02·10)

An `external_dependencies` manifest block — statement, §26 method, owner,
status, closing evidence with digest, blocking or not — and a gate;
`release-check` prints open dependencies and refuses while a blocking one is
unacknowledged. The fabricator's assembly preview and bench-only tests stop
being silently assumed.

*Done when* a release that still needs a bench test says so in its artifact.

### 2.5 Policy states and required domains — M (01·2, 01·3, 05·5)

`validate`/`release-check` emit a §30 policy state (`analysis-only` …
`release-ready`) derived from which domains ran, what was declined, and what
claim policy says. `release_profile.required_domains` makes declining a domain
an explicit manifest act — a board that declares no thermal block and no claim
policy lands on `requires-additional-evidence`, not READY. Board 01 reached
READY with 13 of 36 gates NOT_APPLICABLE.

*Done when* a board cannot reach release-ready by declining the blocks that
would have tested it hardest.

### 2.6 Device parameters with a knowledge level — M (01·12, 03·2b)

Device-parameter records mirroring `extract.physical_parameter`: `knowledge`
(exact / typical / bounded / unknown), measurement conditions, validity
range — including thermal boundary conditions, so a θJA quoted on one square
inch of 2-oz copper is checkable against the board's actual stackup.
Extrapolation beyond the range must be declared; a claim on a typical-only
figure cannot come out EXACT.

*Done when* "the low rail rests on an extrapolation" is visible in the
verdict, not a commit message.

### 2.7 Provenance completion — M (03·8, 08·9, 04·C2)

`PROV.EVIDENCE_INTEGRITY`: every document an evidence index names exists,
hashes correctly, sits in the closure; every cited document id resolves. A
manifest-declared regeneration order (`run.py regenerate`) plus
`PROV.DERIVED_DOCUMENTS` re-running each generator and comparing — three
boards wrote this test by hand. An omission-closure report listing every claim
whose stated omissions name a quantity the current stage can now measure: the
post-layout work list as a query.

*Done when* a swapped datasheet revision fails a gate, and "what is left to
verify" is derived, not judged.

---

## Phase 3 — The missing physics

The four domains where boards currently answer "we cannot say." Ordered by
value per unit of work; 3.1 feeds everything after it. All results are claims
with model, validity window, assumptions and omissions attached — and refusal
outside the window, never extrapolation.

### 3.1 Catalog evidence prerequisites — M (06·E3, 08·7, 03·11, 05·6, 07·8, 08·6, 06·D3, 01·13)

Substantiate and freeze what five boards asked for: hole-wall plating
thickness (a `copper-plated-hole` category), mask expansion / registration /
minimum dam and the via-to-mask process limit (turns on two permanently dark
gates on every board), `from_approved_catalog` physical-stackup composition
for 4-layer selections (the 2-layer path exists since `3516aa6`), a freezable
low-voltage conductor-spacing basis, and `from_catalog` manifest references so
boards cite instead of restate. Plus a narrow read-only accessor over the
committed catalog that validation may import — no network capability.
Anything unsubstantiatable stays board policy, per the promotion rules.
(Note: commit `9528bfa` may partially cover 01·13 — verify before building.)

*Done when* `VIA.MASK_CLEARANCE_PROCESS` and `VIA.NATIVE_GERBER_AGREEMENT` run
on real boards, and via models rest on evidence, not an assumed 18 µm.

### 3.2 Conductor and via current capacity — M (06·D1, 06·C2, 08·3)

An ampacity model (temperature rise vs cross-section, external/internal, basis
stated), via-barrel resistance and area from 3.1's plating evidence so
`path_resistance` returns bounded quantities across vias, and a check over
declared current-carrying paths. Claim-shaped conductor primitives (Z0,
damping/overshoot, barrel area) exposed for board arithmetic. Board 06: "the
single most load-bearing unchecked thing on this board, and on every board the
toolkit has produced." Cheapest item in this phase; do it first.

*Done when* "does this conductor carry its current" and "does this layer
change narrow it" are gate questions.

### 3.3 Thermal — L (01·4, 03·2, 04·B4, 06·D2, 08·5)

`pcbqa/thermal.py` plus a `thermal` manifest block and `THERMAL.*` gates:
declared ambient and boundary conditions; full dissipation attribution;
steady-state derating at the declared ambient (board 03 caught a transient
rating applied to a continuous part); θJA validity checked against actual
copper — mismatch forces the conditional-margin form ("the path may be this
much worse before the limit"), never an invented junction temperature; the
pad-through-via-array closed form; a coarse 2-D spreading solve over real
copper for board rise. Estimates labelled APPROXIMATE carrying their boundary
conditions; a part with no θJA yields UNKNOWN. Closes 2 UNKNOWNs each on
boards 03 and 08; boards 01 and 03 have reference implementations to lift.

*Done when* boards delete `design/thermal.py` and the two board-rise UNKNOWNs
become bounded claims with stated assumptions.

### 3.4 DC power integrity over real copper — L (01·5, 04·B3, 05·3, 06·C1)

A network DC solve where copper is parallel (an explicitly requested answer
with its own claim shape — the series-path refusal stays for the case it was
written for), a nodal solve over filled zones with vias as inter-layer links,
multi-pad chain traversals (through-pad conductors are ordinary practice),
declared source/loads/currents per rail, `PDN.DC_DROP` and `PDN.RETURN_PATH`
gates, and naming of the narrowest cross-section and highest-current vias.
Solver, mesh and convergence stated in the claim; refusal on stale fill.

*Done when* a poured rail and a ground return are measurable; board 04 can
state the drop on the 4 A path it currently budgets blind.

### 3.5 Reactive extraction: L, C, Z0, richer interconnect models — L (02·1, 03·10, 05·2, 06·C3, 08·4)

Per-unit-length C and L, Z0 and delay from the same geometry and stackup the
propagation model already uses — so impedance and delay can never disagree;
loop inductance over a declared current loop (the claim vocabulary reserves
it, nothing produces it); via barrel inductance beside the existing via delay
model; RLC or transmission-line subcircuits under the extracted-model alias
mechanism, segment count from electrical length, R-only still selectable,
reference-interruption refusals inherited from the delay model.

*Done when* board 02 deletes its microstrip arithmetic and keeps the same
claim; §22's ringing questions become simulable instead of analytic asides.

### 3.6 Coupled lines and differential impedance — M (05·1)

Edge-coupled microstrip (bare and coated) and stripline: odd/even →
differential/common-mode impedance, validity windows with refusals, shared
effective-permittivity helpers, consuming the existing coupled-run-length
inventory so the model applies to the length actually run coupled.
`fab impedance --mode differential` stops refusing inside the window;
`SI.PAIR_IMPEDANCE` gate over a `differential` interface block; the
fabricator-report path plus the first-class fact that controlled impedance
starts at 4 layers.

*Done when* the one unresolved electrical claim on board 05 resolves, before
the differential-heavy queue (boards 10, 22, 25–29) arrives.

### 3.7 Simulation expansion — M (01·9, 03·9, 06·C6)

`isource_dc`/`isource_pulse`, inductor initial conditions with `.ic` emission,
`.ac` analysis with magnitude/phase measurements (PSRR, PDN impedance, filter
response), DC sweep, current and differential measurements, a regulator model
class (tolerance, dropout, load regulation — the numbers rail claims rest on),
and extended monotonic-knowledge templates (series chains, parallel loads,
divider-with-shunt) so real networks keep theorem-level provenance instead of
dropping to `assumed`.

*Done when* an LED array is a current sink, a coil turn-off has a decay time,
and a filter has a response.

### 3.8 Stage linkage and path-integrity generalization — M (02·2, 04·B2, 06·B2, 05·8)

A scenario declares it supersedes a pre-layout twin with named extracted
models substituted; a gate reports the per-measurement delta and fails when
post-layout crosses a limit pre-layout met — the delta is the artifact.
Reference continuity exposed under a neutral declaration (the machinery exists
inside `timing.interfaces`; a return-path requirement is not a timing budget).
Matched-group skew cancels provably-shared endpoint ambiguity — checked
against junction identities, with the cancelled amount reported.

*Done when* "did layout cost this margin, and how much" is an artifact, not
two reports diffed by eye.

### 3.9 Netlist topology API — S (01·10)

`pcbqa/netlist_topology.py`: `bridges(net_a, net_b)`,
`reachable_through(net, kinds)`, `pins_on(net)`. Board 01's hand-rolled graph
walks broke twice when topology changed — static lists are how board-specific
assumptions get baked into rules.

*Done when* topology questions are asked of the netlist, not of a list that
was true last week.

---

## Phase 4 — Fabrication-facing: orientation, lifecycle, assembly

The seams to the physical supply chain. Everything follows the
freeze-review-commit pattern; nothing reaches the network from a verdict.

### 4.1 Orientation as versioned, pinned toolkit code — M (08·8, 03·4, 05·7, 02·9)

The deriver ships as toolkit code the board *pins by digest* in its manifest —
the gate still verifies the exact script that ran, the board still owns the
version choice, and a scorer fix stops being pasted into every shipped board
(08 copied 486 lines from 03 with one line changed). Algorithm requirements
from board 03's hard-won experience: pair by pad number where libraries agree,
positional fallback recorded, scoring from the raw response body. A freeze
helper with backoff and resume (rate-limiting hit twice at part 18 and 24 of
26); candidate-registry emission so opting in costs a review, not a build; a
`review_basis` vocabulary distinguishing human comparison from evidence
re-derivation.

*Done when* the board with the most to gain from `CPL.ORIENTATION` no longer
opts out, and no two boards diverge silently.

### 4.2 Part lifecycle and availability — M (01·6, 02·4)

A frozen lifecycle/stock snapshot (a `fab refresh`-style acquisition, commit
as approval) and a `BOM.LIFECYCLE` gate: fail on discontinued, warn on low
stock and single-source, compare declared build quantity against stock — and
hold an *unestablished* lifecycle as unknown rather than absent, because
unknown is not PASS anywhere else in this system. Closes T4.

*Done when* a discontinued part is a gate failure before the first routing
attempt, not a chance discovery.

### 4.3 Assembly policy and DFA — L (02·3, 01·14, 04·B5, 08·11)

A board-declared assembly policy (reflow passes, peak profile, sides, cleaning
process, hand-solder exceptions) checked against per-part declared process
requirements, with explicit per-part waivers — board 02 has a real recorded
conflict (cleaning recommended vs no-wash membrane) that nothing objects to.
Geometry DFA: paste aperture ratio and segmented-pad coverage bounds, no via
under paste, courtyard-to-courtyard spacing, population side, height regions
and connector mating keep-clear volumes attached to the existing connector
contracts.

*Done when* §25 judges a PCBA, not a bare board plus parity files.

### 4.4 Board contract export for firmware — M (04·B8)

A generated machine-readable contract — pin assignments, voltage domains,
polarities, boot-state constraints — derived from the netlist, so firmware
never maintains a second hand-edited copy of facts the board already declares
(inverted PWM polarity, boot pull states: get one wrong and the fans run
backwards).

*Done when* the contract is generated, and the firmware repos for boards 13–16
consume it.

---

## Phase 5 — Toolkit self-verification and long-horizon seams

The discipline the toolkit applies to boards — unknown is not pass, a check
must be shown to bite — applied to the toolkit itself, plus the seams the back
half of the queue will need.

### 5.1 Per-gate negative coverage by mutation — M (04·C3)

Programmatic mutation of a clean fixture — shrink a via, add a dangling track,
break parity, relax a project rule — asserting that exactly the corresponding
gate fails. Retrofits the 21 of 36 gates that today have no proof they bite;
the standing per-new-gate rule started in Phase 0.

*Done when* no gate is indistinguishable from one that always passes.

### 5.2 Flow repeatability evidence — M (04·C1)

Run generate→route→validate N times from the same sources; report verdict
stability, which gates ever differ, and the routing accept rate. The honest
release statement for any board whose copper came from a non-deterministic
search — today, all of them.

*Done when* "this board routes clean" is a statement about a distribution,
recorded in release evidence.

### 5.3 Datasheet curve digitizer — M (01·11)

`pcbqa/digitize.py`: page, crop, two-point axis calibration (linear/log),
traced series with stated pixel-pitch uncertainty and the crop's digest —
reproducible and bound to the frozen document. The most repetitive manual task
board 01 reported, and the queue's precision-analog boards will lean on
digitised curves harder.

*Done when* a traced curve is evidence with uncertainty, not pixel
archaeology.

### 5.4 The full-wave seam — M (05·9)

Not a solver — the boundary: a documented region export (an electrical path,
surrounding copper within a stated distance, the stackup, ports at named
terminals) a solver can consume and a claim can cite, refusing release-grade
claims where ports, references or de-embedding cannot be established. Decide
the seam before boards 24–28 (SDR, USB3, GbE, HDMI, DDR3) force it as an
accident. Per the roadmap's own rule: no backend dispatch abstraction until a
real backend exists.

*Done when* a connector launch can be handed to a solver through a defined,
citable interface.

### 5.5 Silent no-op and hygiene lints — S (03·5b, 02·10)

Fail when a project declares netclass membership patterns the DRC path in use
ignores — design rules less strict in practice than the manifest says. A
genericity lint on gate titles and messages (a gate once claimed "four copper
layers" while checking whatever was declared).

*Done when* a board cannot rely on a rule that is judging nothing.

---

## Sequencing against the queue (boards 09–32)

Phases 0–2 pay off on every remaining board and should land before board 09
starts. Phase 3 is driven by what the queue needs next — the back half of the
bench is exactly the set of boards that will hit today's gaps hardest.

| Upcoming boards | Character | Must have landed |
|---|---|---|
| 09–12 | Precision analog / instrumentation (thermocouple DAQ, USB audio, 4–20 mA, load cell) | P0–P2 · 3.7 (.ac) · 3.5 · 3.3 · 3.6 (for 10) |
| 13–16 | MCU / FPGA digital (RP2040, SDIO, RMII, PMOD) | 3.8 · 3.5 · 4.4 |
| 17–20 | Power conversion (5 A buck, BLDC, PoE, MPPT) | 3.2 · 3.3 · 3.4 · 3.7 |
| 21–24 | RF (BLE, GNSS, sub-GHz, SDR IF) | 3.6 · 3.1 · 5.4 (for 24) |
| 25–29 | High-speed (USB3, GbE, HDMI, DDR3, serializer) | 3.6 · 3.8 · 5.4 |
| 30–32 | Dense / mixed-signal | 1.5 · 4.3 · everything above |

Recommended order of releases: **0 → 1 → 2 → 3.1+3.2 → 3.3–3.9 → 4 → 5**,
with 4.2 (lifecycle) pulled early if a board enters part selection before
Phase 4 — it is cheap and prevents scrapped selection cycles. Phase 5 items
interleave; 5.4 must precede board 24.

---

## Deliberately not in the plan

- **Automatic remediation.** Board 01: every refusal that forced a look
  surfaced a real defect. The toolkit measures; it never repairs a design.
  (The Phase 1 transforms operate on router *output* into fresh candidates —
  the authoritative board stays untouched.)
- **Looser defaults.** No request in eight files asks for one; two gates that
  needed changing were wrong in reasoning, not strictness.
- **Multi-manufacturer abstraction.** Explicitly unwanted; `profiles/jlcpcb/`
  is organisation, not indirection.
- **Owning an EM solver, or backend dispatch before a backend exists.** 5.4
  defines the seam only.
- **Tier 2/3 extraction beyond 3.5–3.6, and MCU/FPGA digital simulation.**
  Nothing in boards 01–08 can judge them yet; the queue will say when.

---

## Traceability: every request → a work package

Items marked *fixed* were closed during boards 01–02 (per their own records)
and are not re-planned.

| Req | Item | → WP |
|---|---|---|
| 01·1 | Claim policy for unsupported claims | 2.2 |
| 01·2 | Policy state on every result | 2.5 |
| 01·3 | Required domains in release profile | 2.5 |
| 01·4 | Thermal module and gates | 3.3 |
| 01·5 | Power integrity (plane DC, decoupling, PDN) | 3.4 |
| 01·6 | Part lifecycle vs frozen snapshot | 4.2 |
| 01·7 | Placement checks before routing | 1.5 |
| 01·8 | Gates declare their class | 0.5 |
| 01·9 | Sim: isource, .ac, currents, regulator class, sweep | 3.7 |
| 01·10 | Netlist topology API | 3.9 |
| 01·11 | Datasheet graph digitisation | 5.3 |
| 01·12 | Device parameters with knowledge level | 2.6 |
| 01·13 | Physical inputs reachable from validation | 3.1 |
| 01·14 | Assembly and DFA | 4.3 |
| 02·1 | Analytic extraction beyond DC resistance | 3.5 |
| 02·2 | Post-layout re-run of pre-layout scenario | 3.8 |
| 02·3 | Assembly process compatibility | 4.3 |
| 02·4 | Lifecycle and availability as claims | 4.2 |
| 02·5 | Board-facing claim harness | 2.3 · 2.2 |
| 02·6 | Canonical serialisation, tidy, deterministic export | 1.2 |
| 02·7 | Closure staleness distinguishes what changed | 0.1 |
| 02·8 | Closure mismatch names the member | 0.1 |
| 02·9 | Orientation: lower the barrier | 4.1 |
| 02·10 | toolkit_identity git failure; layer-count hygiene; physical-test declaration; external preview dependency | 0.6 · 5.5 · 2.1 · 2.4 |
| 02·fixed | 2-layer physical stackup; gates with alternatives | fixed @ 3516aa6 |
| 03·1 | Machine-readable manifest schema | 0.2 · 0.4 |
| 03·2 | Thermal (ambient, θJA validity, geometry model) | 3.3 · 2.6 |
| 03·3 | fab_format silently skips orientation | 0.3 |
| 03·4 | Reference orientation derivation | 4.1 |
| 03·5a | Router ignores --clearance | 1.3 · 1.4 |
| 03·5b | Netclass patterns silently unenforced | 5.5 |
| 03·5c | Placement copper-free cycle | 1.5 |
| 03·6 | Fast board-integrity preflight; bench lock | 0.5 |
| 03·7 | Requirement kinds, methods, claim join | 2.1 |
| 03·8 | Evidence document integrity | 2.7 |
| 03·9 | Current source; inductor initial condition | 3.7 |
| 03·10 | Loop-inductance extraction | 3.5 |
| 03·11 | Via-to-mask process limit in catalog | 3.1 |
| 04·A1 | Router lowers its own grading floor (T1) | 1.3 · 1.4 |
| 04·A2 | Toolkit-owned candidate search | 1.3 |
| 04·A3 | Post-router geometry repair | 1.2 |
| 04·A4 | KiCad object identity trap | 0.6 |
| 04·A5 | Save rewrites the project document | 1.6 |
| 04·A6 | Findings not addressable | 0.6 |
| 04·A7 | Footprint geometry for placement seeds | 1.5 |
| 04·A8 | Output path lands in repo root | 0.2 |
| 04·B1 | Wired path to existing extraction | 0.4 |
| 04·B2 | Pre/post-layout comparison | 3.8 |
| 04·B3 | DC power integrity | 3.4 |
| 04·B4 | Copper-aware thermal estimate | 3.3 |
| 04·B5 | Design-for-assembly checks | 4.3 |
| 04·B6 | External/manual release dependencies | 2.4 |
| 04·B7 | Verification-method classification | 2.1 |
| 04·B8 | Board-contract export for firmware | 4.4 |
| 04·C1 | Flow repeatability | 5.2 |
| 04·C2 | Omission-closure report | 2.7 |
| 04·C3 | Per-gate negative coverage | 5.1 + standing rule |
| 05·1 | Coupled-line differential model | 3.6 |
| 05·2 | Reactive interconnect models | 3.5 |
| 05·3 | Plane and multi-path DC; PDN quantities | 3.4 |
| 05·4 | Verification-method classification | 2.1 |
| 05·5 | External dependencies; policy states | 2.4 · 2.5 |
| 05·6 | Fabricator facts the catalog lacks | 3.1 |
| 05·7 | Rotation as a toolkit facility | 4.1 |
| 05·8 | Correlated uncertainty in matched groups | 3.8 |
| 05·9 | Defined seam for full-wave extraction | 5.4 |
| 06·A1 | Authored copper as verified input (T2) | 1.3 · 1.4 |
| 06·A2 | Safe removal helper | 1.1 |
| 06·A3 | One definition of "attached" | 1.2 |
| 06·A4 | Router report vs checker reconciliation | 1.3 |
| 06·A5 | Replay transforms without re-routing | 1.3 |
| 06·B1 | Pour-island reporting | 1.5 |
| 06·B2 | Reference continuity without timing framing | 3.8 |
| 06·B3 | Net-wide pad stitcher | 1.5 |
| 06·C1 | Traversals through pads | 3.4 |
| 06·C2 | Via barrel resistance model | 3.2 |
| 06·C3 | Tier-1 capacitance and inductance | 3.5 |
| 06·C4 | One registry-assembly entry point | 2.3 |
| 06·C5 | geom.configure trap | 0.6 |
| 06·C6 | More monotonic knowledge templates | 3.7 |
| 06·D1 | Conductor and via current capacity | 3.2 |
| 06·D2 | Thermal, toolkit-owned | 3.3 |
| 06·D3 | Voltage-dependent spacing basis | 3.1 |
| 06·E1 | Requirements register with enforced join | 2.1 |
| 06·E2 | Methods, physical tests, external deps | 2.1 · 2.4 |
| 06·E3 | Hole-wall plating in catalog | 3.1 |
| 07·1 | Tidy pass belongs to the toolkit | 1.2 |
| 07·2 | pcbnew binding hazards | 1.1 |
| 07·3 | Connectivity vs stale fill | 1.1 |
| 07·4 | Clearance oracle (slack) | 1.1 |
| 07·5 | Candidates judged by release gates | 0.5 |
| 07·6 | Router: pad clearance, pours-in-nets, fragments, project file | 1.3 · 1.4 |
| 07·7 | Gate measurements state how they count | 0.6 |
| 07·8 | Catalog knows the via-mask limits | 3.1 |
| 07·9 | Staged checking with library tables | 1.1 |
| 07·10 | open_nets API | 1.1 |
| 07·11 | min_segment stated once | 1.3 |
| 07·12 | Repair passes need a fixpoint | 1.2 |
| 07·13 | validate without build | 0.5 |
| 07·14 | Restore the board on any exit | 1.3 |
| 07·15 | Floors stated once; closure digest coverage; export flags | 1.3 · 0.1 · 0.2 |
| 08·1 | pcbqa.board safe mutation | 1.1 |
| 08·2 | pcbqa.route search loop | 1.3 |
| 08·3 | Conductor physics primitives | 3.2 |
| 08·4 | Extraction beyond resistance | 3.5 |
| 08·5 | Thermal | 3.3 |
| 08·6 | Physical stackup from approved catalog | 3.1 |
| 08·7 | Plated-hole wall thickness | 3.1 |
| 08·8 | Orientation registry in the toolkit | 4.1 |
| 08·9 | Build-time coherence; derived documents | 0.3 · 2.7 |
| 08·10 | Discoverability (gates --missing, module index) | 0.4 |
| 08·11 | DRC-with-project; placement pre-check; mask dam | 1.1 · 1.5 · 3.1 · 4.3 |
