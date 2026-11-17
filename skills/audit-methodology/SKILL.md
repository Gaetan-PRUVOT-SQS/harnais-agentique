---
name: audit-methodology
description: 'Use for an independent, evidence-based audit of a project, repository, CI/CD, workflow or dev environment: IIA, ISO 19011, ITAF, COBIT, rating and remediation plan.'
---

# Audit methodology

A risk-based, evidence-based method for auditing software projects, delivery workflows and development environments. It combines the IIA Global Internal Audit Standards (2024), ISO 19011:2018, ISACA ITAF (5th edition, 2026) and COBIT 2019, COSO internal control, and the structured problem solving and reporting practices used by strategy consultancies.

## 1. Charter and independence

- Read-only by default. The auditor never modifies the audited system: no commits, pushes, merges, config changes, issue or ticket edits, package installs inside the audited project, or reruns that alter shared state. Inspect the repo in place. Do not copy the project and do not use a scratch directory (`tests-locaux`). Reperformance uses the project's own test command.
- Any fix observed as necessary is written as a recommendation, never applied. If the requester later asks for remediation, that is a separate engagement done by someone other than the auditor.
- Objectivity: do not audit work you built or configured yourself. If unavoidable, disclose the impairment in the report (IIA Standard 2.3).
- Confidentiality: secrets, tokens and personal data seen during fieldwork are never copied into working papers or reports. Record their location and type only, and recommend rotation.
- Professional skepticism: a claim is not evidence. Prefer what you can reperform or inspect over what is stated.
- Fair presentation: report obstacles, scope limitations and disagreements with the auditee (ISO 19011 clause 4).

## 2. Engagement phases

### 2.1 Planning and risk-based scoping
1. Define the question in one sentence (what decision will this audit support).
2. Agree objectives, scope (systems, repos, period, branches, environments), exclusions and criteria (the standards and internal rules used as the yardstick).
3. Build a MECE issue tree: split the main question into sub-questions that do not overlap and together cover the whole. State an initial hypothesis per branch so fieldwork tests it instead of browsing.
4. Rate inherent risk per area (likelihood x impact, 1 to 5 each). Spend effort where risk is highest and keep a light check on the rest.
5. Write the audit programme: for each sub-question, the control or practice expected, the test step, the evidence needed and the sample.

### 2.2 Fieldwork and evidence collection
- Evidence types, from strongest to weakest: reperformance (rerun the project's own test command, in the project), inspection of system output (logs, CI runs, configs, git history), observation, inquiry (documentation or statements).
- Evidence must be sufficient, reliable, relevant and verifiable. Corroborate inquiry with at least one other type.
- Sampling: define the population (commits, PRs, pipeline runs, dependencies), the sampling unit and what counts as a deviation. For small populations (under 50) test all. Otherwise use random or systematic selection, typically 25 items for a recurring control, 40 or more for a high-risk one. Document the seed or selection method so the sample can be reproduced.
- Log every piece of evidence in the evidence log (section 6) at the time it is collected.

### 2.3 Testing of controls
- Design effectiveness: would the control, operated as described, prevent or detect the risk? Check by walkthrough and inspection of the configuration (for example, a branch protection rule requiring review and green checks).
- Operating effectiveness: did it actually operate throughout the period? Check by sample (for example, 25 merged PRs: how many were reviewed, how many merged with failing checks, how many bypassed protection).
- A control that is badly designed is not tested for operation. Report the design gap directly.

### 2.4 Findings (the 5 C's)
Every finding answers five questions:
- Condition: what was observed, with counts and evidence IDs.
- Criteria: what should be, with the exact reference (standard clause, internal rule, documented intent).
- Cause: why the gap exists. Ask "why" until you reach something the auditee can change (process, ownership, tooling, knowledge).
- Consequence: what can go wrong, stated in business terms (outage, data exposure, slower delivery, failed compliance).
- Corrective action: specific, owned, dated and verifiable.

Discuss draft findings with the auditee before the report. Record their response and agreed action plan.

## 3. Rating scales

### 3.1 Finding severity
| Rating | Definition | Expected response |
|---|---|---|
| Critical | Exploitable or already materialising risk to security, data, legal compliance or production availability. Key control absent. | Contain within 48 hours, fix within 2 weeks |
| High | Significant weakness in a key control or practice, likely to cause a material incident or block a release or certification. | Fix within 30 days |
| Medium | Control exists but is inconsistent or partly effective. Moderate impact or lower likelihood. | Fix within 90 days |
| Low | Minor gap, hygiene or efficiency issue. Limited impact. | Next planning cycle |
| Observation | No gap against criteria, improvement opportunity only. | Optional |

### 3.2 Overall audit rating
- Satisfactory: no critical or high findings.
- Needs improvement: no critical, at most two high findings.
- Unsatisfactory: any critical finding, or three or more high findings.

### 3.3 Maturity scale (0 to 5, aligned with COBIT 2019 capability levels and ISO/IEC 33020)
| Level | Name | Description |
|---|---|---|
| 0 | Absent | Practice not performed |
| 1 | Initial | Performed ad hoc, depends on individuals |
| 2 | Managed | Performed consistently on this project, basic records exist |
| 3 | Defined | Documented standard process, applied across projects |
| 4 | Measured | Process measured with metrics and thresholds, deviations acted on |
| 5 | Optimising | Continuous improvement driven by data and retrospectives |

A level is reached only when all practices of that level and the levels below are in place. Always state the target level next to the current level.

## 4. Audit domains for software development

### 4.1 Test process (ISTQB CTFL v4.0.1, ISO/IEC/IEEE 29119)
- Test planning, monitoring, analysis, design, implementation, execution and completion are visible in artefacts.
- Risk-based test approach, documented test techniques (equivalence partitions, boundary values, decision tables, state transitions).
- Unit, integration, end-to-end and regression levels exist and run in CI. Flaky tests are tracked, not silently retried or skipped.
- Coverage measured, with a threshold on changed lines. Defects classified and linked to tests that confirm the fix.
- Test completion report exists for releases (29119-3 information items).

### 4.2 Code quality (ISO/IEC 25010:2023)
- Characteristics: functional suitability, performance efficiency, compatibility, interaction capability, reliability, security, maintainability, flexibility, safety.
- Evidence: linter and static analysis results, complexity and duplication metrics, dependency age, error handling, logging, dead code, consistency of style.

### 4.3 Secure development (OWASP SAMM v2, NIST SP 800-218 SSDF, OWASP ASVS 5.0)
- SAMM functions: governance, design, implementation, verification, operations (score each practice 0 to 3).
- SSDF groups: prepare the organisation (PO), protect the software (PS), produce well-secured software (PW), respond to vulnerabilities (RV).
  Audit against SSDF v1.1 (SP 800-218, final); SP 800-218 Rev. 1 (v1.2) is still a draft and can only be cited as such.
- Mobile apps: OWASP MASVS v2 for requirements, MASTG v2 tests as evidence, MASWE IDs to label weaknesses.
- Checks: secrets in code or history, dependency vulnerability scanning, SAST, threat model for sensitive features, ASVS level chosen and verified, security contact or policy file.

### 4.4 CI/CD and supply chain (SLSA, OpenSSF Scorecard)
- Pipelines defined as code, reproducible builds, pinned actions and base images, least-privilege tokens, no secrets in logs.
- Branch protection, mandatory review, required status checks, signed tags or releases, provenance for artefacts.
- Dependency update process (automated PRs), lockfiles committed, SBOM available.
- SLSA v1.2: assess the Build track and, for source repositories, the Source track (change history, review, protected branches).

### 4.5 Repository hygiene and documentation
- README with purpose, setup and run instructions that work from a clean clone (reperform them).
- Licence, contributing guide, changelog, code owners, issue and PR templates.
- Commit history readable, conventional messages, no large binaries or generated files, .gitignore complete.
- Architecture decisions recorded for significant choices.

### 4.6 Delivery performance (DORA)
- Throughput: change lead time, deployment frequency, failed deployment recovery time.
- Instability: change fail rate, deployment rework rate.
- Measure per application over a stated period from git, CI and release data. Compare trends over time rather than ranking people.

### 4.7 Environment and tooling
- Tool versions pinned or documented, no conflicting duplicates on PATH, reproducible setup script.
- Access control and credentials storage, token scopes minimal, keys rotated.
- Disk, backups, update policy, monitoring of the environment itself.

## 5. Process and workflow assessments
For a workflow (for example, an automated feature pipeline or a release process), map the steps, then for each step record: input, owner, control, output, failure mode. Assess against COSO components (control environment, risk assessment, control activities, information and communication, monitoring). Look for missing handoffs, manual steps without checks, and loops without exit criteria.

## 5b. Red team, blue team and purple loop
Use when the audit includes adversarial security testing. Same independence and read-only rules apply to the audited production systems.

Rules of engagement (signed off before any test): targets limited to assets the owner controls (own repositories, local builds, local containers, test accounts). No third-party systems, no production data, no denial of service, no destructive or irreversible actions, no persistence left behind. Stop and report at once if a real compromise or exposed secret is found.

- Red team: build a threat model with STRIDE (spoofing, tampering, repudiation, information disclosure, denial of service, elevation of privilege) per component and trust boundary, map realistic attack paths to MITRE ATT&CK techniques, then test them against a local build (dependency and secret scanning, injection and auth tests, CI workflow abuse such as untrusted input in scripts or over-privileged tokens). Each result is written as a finding with the 5 C's and reproduction steps.
- Blue team: assess the controls that should have prevented or detected each attack (design and operating effectiveness), write the remediation plan, and after the fix retest with the original reproduction steps before closing.
- Purple loop: every red finding becomes a blue item in the remediation tracker with owner, due date and a verification test. The red side reruns the attack after the fix; the item closes only when the attack fails and detection, where expected, fires. Lessons feed the threat model for the next cycle.

## 6. Evidence log format
| ID | Date and time | Source (path, URL, command) | Type (reperformance, inspection, observation, inquiry) | Description | Sample ref | Hash or run ID | Related finding |
|---|---|---|---|---|---|---|---|
| E-001 | | | | | | | |

Store raw output under `evidence/` with the ID as the file name prefix. Never store secrets in it.

## 7. Report structure (pyramid principle)
Lead with the answer, then the supporting arguments, then the evidence. Frame the opening with SCQA (situation, complication, question, answer).

```
# Audit report: <subject>
Period: <dates>  Auditor: <name>  Report date: <date>  Version: <n>

## 1. Executive summary
Overall rating: <Satisfactory | Needs improvement | Unsatisfactory>
Situation: <one sentence>
Complication: <one sentence>
Question: <the audit question>
Answer: <the conclusion in two or three sentences>
Top three actions: <action, owner, date>

## 2. Scope, objectives, criteria and limitations
## 3. Key findings (grouped MECE by domain, highest severity first)
## 4. Maturity profile (current vs target per domain)
## 5. Recommendations (prioritised by impact and effort)
## 6. Management responses
## Appendix A: Evidence log
## Appendix B: Sampling details
## Appendix C: Methodology and rating scales
```

Prioritise recommendations on an impact versus effort grid: quick wins (high impact, low effort) first, then major projects, then fill-ins. Each recommendation carries an owner and a due date.

## 8. Templates

### 8.1 Finding record
```
ID: F-<nn>          Severity: <Critical|High|Medium|Low|Observation>
Domain: <section 4 domain>   Title: <short, factual>
Condition: <what was observed, counts, evidence IDs>
Criteria: <reference and clause>
Cause: <root cause>
Consequence: <business impact and likelihood>
Corrective action: <specific action>
Owner: <role or name>   Due date: <date>
Auditee response: <agreed | partially agreed | not agreed, with reason>
Verification method: <how closure will be tested>
```

### 8.2 Remediation tracker
| Finding | Severity | Action | Owner | Due date | Status (open, in progress, ready for verification, closed, risk accepted) | Verified by and date | Notes |
|---|---|---|---|---|---|---|---|
| F-01 | | | | | | | |

## 9. Follow-up
- Track every action in the remediation tracker. Review status at agreed intervals (monthly for high and critical).
- Closure requires retesting by the auditor with new evidence, not a statement that it is done.
- Overdue critical or high actions are escalated to the requester. A risk can only be accepted in writing by the person who owns it.
- Plan the next audit from residual risk and repeated root causes.

## 10. Quality assurance of the audit
Before issuing the report, check:
- Every finding has all five C's and at least one evidence ID that a second person could reproduce.
- Criteria are cited precisely; no finding rests on personal preference.
- Severity matches the scale definitions; the overall rating follows the rules in 3.2.
- Sample sizes and selection are documented.
- Scope limitations and independence impairments are disclosed.
- Nothing in the audited system was changed (compare git status, config hashes or timestamps before and after).
- Language is factual, neutral and short. No blame on individuals.
After each engagement, note what worked and what to change in this method.

## Sources
- IIA Global Internal Audit Standards 2024: https://www.theiia.org/en/standards/2024-standards/global-internal-audit-standards/
- ISO 19011:2018 auditing principles (ISO/IAF Auditing Practices Group): https://committee.iso.org/files/live/sites/tc176/files/documents/ISO%209001%20Auditing%20Practices%20Group%20docs/Auditing%20General/APG-ISO_19011_2018.pdf
- ISACA ITAF 5th edition (Feb 2026, free from ISACA): https://www.isaca.org/about-us/newsroom/press-releases/2026/isaca-launches-future-ready-it-audit-framework-update-to-strengthen-digital-trust
- COBIT 2019 capability assessment: https://www.isaca.org/resources/news-and-trends/industry-news/2020/effective-capability-and-maturity-assessment-using-cobit-2019
- COSO Internal Control, Integrated Framework: https://www.coso.org/_files/ugd/3059fc_b5232f85f48848a295cc6c168de82006.pdf
- PCAOB AS 2315 audit sampling: https://pcaobus.org/oversight/standards/auditing-standards/details/AS2315
- Five C's of findings (Chartered IIA): https://charterediia.org/content-hub/blogs/use-of-the-five-cs-in-communication/
- Deloitte Internal Audit 3.0: https://www.deloitte.com/us/en/services/audit-assurance/articles/internal-audit-3-0.html
- McKinsey seven-step problem solving: https://www.mckinsey.com/capabilities/strategy-and-corporate-finance/our-insights/how-to-master-the-seven-step-problem-solving-process
- ISO/IEC 25010:2023: https://www.iso.org/standard/78176.html
- ISO/IEC 33020: https://cdn.standards.iteh.ai/samples/78526/b1153a825ca94dad89ecd8d292ef4817/ISO-IEC-33020-2019.pdf
- ISTQB CTFL v4.0.1: https://istqb.org/certifications/certified-tester-foundation-level-ctfl-v4-0/
- DORA metrics: https://dora.dev/guides/dora-metrics/
- OWASP SAMM v2: https://owaspsamm.org/release-notes-v2/
- NIST SSDF SP 800-218 v1.1 (final): https://csrc.nist.gov/pubs/sp/800/218/final and Rev. 1 draft: https://csrc.nist.gov/pubs/sp/800/218/r1/ipd
- OWASP ASVS: https://devguide.owasp.org/en/08-culture-process/04-asvs/
- STRIDE (Microsoft threat modeling): https://learn.microsoft.com/en-us/azure/security/develop/threat-modeling-tool-threats
- MITRE ATT&CK: https://attack.mitre.org/
- SLSA v1.2: https://slsa.dev/spec/v1.2/  and OpenSSF Scorecard: https://github.com/ossf/scorecard
- OWASP MAS (MASVS, MASTG, MASWE): https://mas.owasp.org/
