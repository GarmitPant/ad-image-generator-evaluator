# 05 — Personal context bank: Garmit Pant

Context about the person the implementing agent is working with and for: what he brings, how
he works, what the project should showcase, and what must not be overclaimed. It is drawn from
the resume-workbench library (`library/project-bank.md`, `library/resume-applications-index.md`,
`library/project-source/llm-judge-harness/DESIGN.md`) as of 2026-09-26.

No contact details are included here, deliberately.

---

## 1. Who he is, briefly

- **Software Development Engineer at Amazon**, Bengaluru (May 2025–present). Before that SDE at
  **MathWorks**, Hyderabad (Jul 2023–Aug 2024) and an intern there (2022).
- **B.Tech, Computer Science and Applied Mathematics, IIIT Delhi** (2019–2023), CGPA 8.6.
- Total professional tenure is **~2.4 years**. The G2 AI Engineer JD asks for 3+. The hackathon
  is his chance to show scope and judgment that read above his years.
- Languages: **Python**, Java, C++. Frameworks: FastAPI, Spring Boot, React, LangChain.
- **Claude Code is a daily tool** (confirmed). He has also used Kiro CLI at Amazon. He authored
  `AGENTS.md` files and agent-friendly docs to modernise legacy codebases for coding agents.

## 2. Experience that bears directly on this project

### Amazon — LLM-as-judge evaluation harness ("Gavel"), Alexa for Shopping
The closest thing in his history to this problem's evaluator. **He owned the harness and the
judge prompts.** Design facts (from his design doc):
- **Rubric as contract**: a judge is a manifest (YAML) plus prose. The harness derives the output
  schema, validation model, CSV columns and score composition from that one file. A new rubric
  needs zero code changes.
- **Score composition is data, not model output**: the model never emits the overall score; a
  declared "ladder" composes dimension scores in code. Motivated by a real prompt carrying two
  contradictory scoring rules.
- **Structured output at the API boundary** via forced tool choice on Bedrock's Converse API.
- **Mechanical verification**: each judgment carries one evidence quote, verified by
  substring match against the source; every number in the insights report is computed in code.
- **Three terminal states** `ok` / `degraded` / `failed`; degraded rows are excluded from
  headline metrics and counted beside them.
- **Crash-safe runner**: append-only JSONL, a single writer thread, resume as a set difference on
  `(case_id, prompt_hash, model_version)`.
- **Calibration design**: held-out gold set; exact and within-one agreement; quadratic-weighted
  kappa for ordinal scores, Cohen's kappa for nominal classes; **sampling flip rate** (noise
  floor) reported separately from **perturbation flip rate**.
- **Outcomes he reports**: turn failure rate **~25% → <1%**; judge-measured response accuracy
  **87% → 99%**; evaluation-to-root-cause time **~1 day → <2 hours**. The harness *surfaced*
  hallucinations and skill-prompt defects; the team *fixed* them.

### MathWorks — vision foundation models
- Built and validated a **video object detection and tracking pipeline** on **Grounding-DINO**
  (open-vocabulary detection), **SAM** (segmentation) and **DeAOT** (tracking), in Python;
  **+8%** tracking accuracy. This is exactly the detect → segment → compare toolchain the
  product-fidelity metric uses.
- **U-Net** segmentation on hyperspectral imagery, **74% → 96%** accuracy through
  hyperparameter tuning and pre/post-processing.
- **Parallelised Python pipeline** for atmospheric correction of ~650 GB of satellite imagery, 4×
  faster.
- Worked **directly with an automotive enterprise customer** to turn business requirements into
  features and architecture.

### Amazon — agentic systems (context, less central here)
- **Alexa for Shopping** agentic subscription management (129M+ MAU): MCP tools over 30+ backends,
  layered intent disambiguation, 20+ agentic actions; he owned the vertical from concept to
  rollout.
- **Multi-Agent Operations Platform**: orchestration engine and agent scaffold (22 agents, 29
  skills, 2 teams, ~740 engineer-hours/year saved), orchestrator–worker DAG dispatch.

## 3. How his Gavel principles map onto this project

The agent should build these in from the start. They are what makes the submission his, and
they are what he can defend fluently in the follow-up interview.

| Gavel principle | Here |
|---|---|
| Rubric as contract | The market registry + creative brief compile into **both** the generation prompt and the context checklist. One source, no drift |
| Composition is data | `PASS = gates ∧ text ∧ product ∧ context`, computed in `compose.py`, unit-tested as a truth table. The judge never outputs an overall verdict |
| Structured output at the boundary | The judge answers through a JSON schema or tool call. Image models don't support structured output, so analysis goes to a text/vision model |
| Evidence verified mechanically | Image analogue of the substring check: **two independent readers must agree** (judge vs OCR on text; judge vs Grounding DINO on product presence). Disagreement → `degraded` |
| ok / degraded / failed | Same states, same rule: headline metrics exclude degraded rows and report their count |
| Append-only JSONL, resume by hash | Run log keyed by `(request_id, prompt_hash, model_version)`; re-runs skip done work |
| Calibration with flip rates | Human labels + agreement/kappa; repeat the judge 3× on a sample for the flip-rate noise floor; constructed negatives play the role of perturbations |

## 4. What the project should showcase (G2 context)

**G2** is a software-review marketplace (it has "joined forces with" Capterra, Software Advice
and GetApp, per the JD; 6M verified reviews). It sells marketing and **advertising** products to
software vendors, which is where display-ad generation fits. The **AI Engineer (Bengaluru,
on-site)** JD emphasises production AI features built with frontier models, "Validate solutions
against functional requirements using both traditional QA methods, **evals, and tracing** to
ensure quality is **measurable and reproducible**", and
**agent-first** development with coding agents like Claude Code or Codex. Its "stand out" list
includes **using AI models to generate content for consumption by end users**, **multimodal
AI**, and **developing evals against agents**.

So the submission should make three things obvious:
1. **Evals are the product.** The evaluator is rigorous, measured against human labels, and
   inside the generation loop.
2. **Reproducibility.** Offline tests, recorded judge responses, hashed prompts, versioned
   registry, a cost/latency ledger.
3. **Agent-first engineering, directed by a human.** The spec-first workflow (this folder →
   `AGENTS.md` → milestone logs) is the disclosure *and* a demonstration of the JD's
   "agent-first ways of working".

## 5. Honesty rules: what must not be overclaimed

His resume library runs on strict do-not-claim rules. They carry into the write-up and the
interview:
- **Do not say the Gavel judge was "calibrated"** or quote a judge-vs-human agreement number for
  it. The calibration was *designed*, not run. The 87% → 99% figure is judge-measured and must
  always be called "judged". (If the write-up mentions Gavel, keep to its architecture.)
- **No prior production image-generation work** is in his history. MathWorks was image
  *understanding* (detection, segmentation, tracking), not generation. Frame it that way.
- **No prior Gemini API work** is in the library (his LLM work is Claude via Bedrock). The
  Gemini client is new code, and that is fine.
- **For this project's own numbers**: report counts beside percentages; label the 20-image set
  as smoke-scale; state when thresholds were tuned and on what; never present evaluator
  agreement measured on the tuning set as held-out.
- **Coding-agent disclosure is mandatory and must be accurate**: what the agent wrote, what he
  specified, what he changed.

## 6. How to work with him

- **He decides scope and architecture; the agent proposes.** For any design change, propose
  with the alternative and the trade-off, then record the outcome in `docs/decisions.md`.
- **Plain, direct language.** Short sentences. No hype. Say what was measured and what was not.
- **Ask before spending money.** Every paid API call goes through the cost ledger. Bulk runs
  (golden set, ablations) need a go-ahead with an estimate attached.
- **Secrets**: keys live in `.env` (gitignored). Never print a key, never commit one.
- **Tests before claims.** Nothing is "done" until a test shows it. Evaluator tests must run
  offline from a clean clone.
- **Log as you go.** At the end of each milestone, append to `docs/agent-collaboration.md`:
  the instruction received, what was built, what he changed, and why. This becomes the
  disclosure section; reconstructing it at the end is how disclosures go wrong.
- **Time-box.** The event is 5–8 hours. Follow the build order in `02` §8 and cut from the
  bottom, never the tests, labels or write-up.

## 7. Interview angles to prepare (after the build)

- **Why deterministic metrics first?** Every model judgment is a claim; OCR and detection are
  measurements. The judge is used only where no measurement exists, and it is cross-checked.
- **Why AND and not an average?** A beautiful background cannot buy back a wrong product.
- **How do you know the evaluator works?** Constructed negatives with known verdicts, human
  labels, agreement and kappa, flip-rate noise floor, counts. Plus what it still gets wrong.
- **What would you do with more time?** A larger labelled set, a judge-model comparison, a
  learned threshold per market, ad-effectiveness signals (CTR literature), holiday-aware seasons.
- **Link to Gavel**: the same ideas (rubric as contract, composition as data, verified evidence,
  degraded state), carried from text judging at Amazon to image judging here.
