---
name: strategic-intelligence
description: 'Use for competitive and economic intelligence, tech watch and strategic analysis of a product: positioning, benchmarks, opportunities, risks, build/buy decisions.'
---

# Strategic intelligence and analysis

A method for turning public information into decisions about a software product or project. It follows the intelligence cycle, the French economic intelligence approach (watch, protection, influence), source grading from the NATO Admiralty system, structured analytic techniques, and the classic strategy frameworks.

## 1. Legal and ethical boundaries
- Open sources only: public websites, documentation, release notes, public repositories, package registries, job ads, conference talks, patents, filings, press, public social posts, app store listings.
- No intrusion: no access to systems, accounts or data you are not authorised to use, no credential guessing, no scraping that breaks terms of service or bypasses access controls, no pretexting or social engineering. In France, unauthorised access to an information system is a criminal offence (Code penal art. 323-1) and trade secrets are protected (law 2018-670).
- Personal data: collect only what the question needs, respect GDPR, never build profiles of private individuals.
- Every claim in a deliverable is traceable to a source with date of access.

## 2. Intelligence cycle
1. Needs: write the decision to support and three to five key intelligence questions (KIQ). Set scope (market, geography, time horizon) and deadline. "Knowing everything about everything" means knowing nothing; prioritise.
2. Collection: plan sources per question, diversify them, log each item with URL, date and grade (section 3). Start with what the organisation already knows.
3. Processing and analysis: deduplicate, grade, structure, apply the techniques in sections 4 and 5. Separate facts, inferences and assumptions.
4. Dissemination: right information, right person, right time. Use the templates in section 7, stating confidence levels.
5. Feedback: ask whether the brief answered the decision, then adjust the needs.

### French economic intelligence (IE) pillars
- Veille (watch and anticipation): continuous, organised monitoring of competitors, technology, regulation, standards, tenders and suppliers. Decide who collects, who analyses, who receives what and how often.
- Protection (economic security): protect your own strategic information while you collect others'. Classify sensitive assets (source code, roadmap, customer data, credentials), limit what is published in repos, talks and job ads, and check supplier dependence.
- Influence: legal action on the environment, such as contributing to standards and open source, publishing technical content, joining professional bodies, answering public consultations. Never disinformation.
Public guidance: SISSE practical sheets and Diagseco self-assessment, IHEDN training on economic intelligence.

## 3. Source evaluation (Admiralty / NATO system)
Grade reliability of the source and credibility of the information separately, then combine (for example B2).

| Source reliability | | Information credibility | |
|---|---|---|---|
| A | Completely reliable | 1 | Confirmed by other independent sources |
| B | Usually reliable | 2 | Probably true |
| C | Fairly reliable | 3 | Possibly true |
| D | Not usually reliable | 4 | Doubtful |
| E | Unreliable | 5 | Improbable |
| F | Cannot be judged | 6 | Truth cannot be judged |

Official documentation and filings are usually A or B; vendor marketing is C at best on performance claims. A key judgment should rest on at least two independent sources graded 1 or 2.

## 4. Structured analytic techniques
- Key assumptions check (early, and again before finalising): write the current analytic line, list every stated and unstated premise, challenge why each must be true, keep only those that must hold and note what would invalidate them.
- Analysis of competing hypotheses (ACH): list all reasonable hypotheses, build a matrix of evidence against hypotheses, mark each cell consistent, inconsistent or neutral, and favour the hypothesis with the least evidence against it. Look for disconfirming evidence, not confirming. Name indicators that would change the conclusion.
- Express confidence in words with a consistent scale (almost certain, likely, roughly even, unlikely, remote) and say what drives it.

## 5. Strategic frameworks and when to use them
| Framework | Use it when | Output |
|---|---|---|
| PESTEL | Scanning the macro environment (political, economic, social, technological, environmental, legal), e.g. regulation affecting a product | Ranked list of external drivers |
| Porter's five forces | Judging how attractive a market segment is (rivalry, new entrants, substitutes, buyer power, supplier power) | Force ratings and profit pressure |
| SWOT then TOWS | Summarising internal strengths and weaknesses against external opportunities and threats, then deriving SO, ST, WO, WT strategies | Strategy options, not just lists |
| Value chain | Finding where the product creates or loses value (build, distribute, support) | Cost and differentiation levers |
| VRIO | Testing whether a capability is a lasting advantage (valuable, rare, inimitable, organised) | Sustained, temporary or no advantage |
| BCG matrix | Allocating effort across several products or modules by market growth and share | Invest, maintain, harvest, drop |
| Ansoff matrix | Choosing a growth path: market penetration, market development, product development, diversification | Growth options with risk level |
| Blue Ocean, strategy canvas and ERRC grid | Escaping head-to-head feature competition; plot competitors' value curves and decide what to eliminate, reduce, raise, create | New value curve |
| McKinsey 7S | Checking whether the organisation can execute (strategy, structure, systems, shared values, style, staff, skills) | Alignment gaps |
| Three Horizons | Balancing the current core (H1), emerging bets (H2) and future options (H3) in a roadmap | Portfolio of initiatives by horizon |
| Wardley mapping | Tech strategy: place components of the user need on a map by visibility and evolution (genesis, custom, product, commodity) to decide build, buy or use a utility | Map with movements and plays |
| TAM, SAM, SOM | Sizing an opportunity: total market, serviceable part, share realistically obtainable; do both top-down and bottom-up and reconcile | Market size range with assumptions |
| Competitor benchmark grid | Comparing named alternatives on weighted criteria | Scored grid and gaps |
| Technology radar | Tracking tools, platforms, languages and techniques; rings adopt, trial, assess, hold | Radar with movement since last edition |

Combine sparingly: usually PESTEL and five forces for the outside, value chain or VRIO for the inside, then SWOT/TOWS to decide.

## 6. Software-specific signals to watch
Release cadence and changelogs, public roadmaps, repository activity (commits, contributors, issue response time), package download trends, dependency and licence changes, security advisories, pricing pages, job ads (hint at stack and priorities), standards and regulation drafts, app store ratings and reviews, conference talks, patents.

## 7. Templates

### 7.1 Executive brief (SCQA, one page)
```
# Brief: <topic>          Date: <date>   Confidence: <level>
Decision supported: <one sentence>
Situation: <what is known and stable>
Complication: <what changed or threatens>
Question: <the question the reader has>
Answer: <recommendation in two sentences>
Three supporting points (MECE):
1. <point> (sources S-01, S-04)
2. <point>
3. <point>
Key assumptions and what would change our view: <list>
Next steps: <action, owner, date>
```

### 7.2 Competitor profile
```
Name:            Category:          Last updated:
Offer and positioning:
Target customers and segments:
Pricing model:
Technology and architecture (public signals):
Release cadence and recent moves:
Strengths / weaknesses:
Likely next moves (with confidence):
Threat level to us: <high | medium | low> and why
Sources (with Admiralty grade):
```

### 7.3 Benchmark grid
| Criterion | Weight | Us | Competitor A | Competitor B | Source |
|---|---|---|---|---|---|
| | | 1 to 5 | | | |
| Weighted total | 100 % | | | | |

### 7.4 Opportunity and risk matrix
| Item | Type (opportunity or risk) | Likelihood 1 to 5 | Impact 1 to 5 | Score | Time horizon | Response | Owner | Indicator to watch |
|---|---|---|---|---|---|---|---|---|

### 7.5 Source log
| ID | Date accessed | URL or reference | Type | Reliability A to F | Credibility 1 to 6 | Notes |
|---|---|---|---|---|---|---|

## 8. Quality checks before release
- Each key judgment traces to graded sources; nothing rests on a single F or 6 item.
- Facts, inferences and assumptions are labelled.
- At least one alternative hypothesis was considered and the reason for rejecting it is stated.
- Nothing was collected through intrusion or deception, and no sensitive internal information is exposed in the deliverable.
- The brief answers the stated decision on the first page.

### Keeping the watch files alive
- Raw sources stay unchanged in their own folder; syntheses live apart and cite them.
- A useful answer or comparison produced on request is filed as a note, so it does not stay buried in a conversation.
- Every few weeks, review the watch files: contradictions between notes, claims superseded by a newer source, notes
  nothing links to, topics mentioned without their own note, missing cross references. Log what was changed and why.

## Sources
- French government IE reference guide: https://www.documentation-administrative.gouv.fr/adm-01859868v1/document
- SISSE: https://www.entreprises.gouv.fr/service-de-linformation-strategique-et-de-la-securite-economiques-sisse
- Economic security practical sheets (DGE/SISSE): https://www.entreprises.gouv.fr/files/files/Publications/2026/guides/la-securite-economique-au-quotidien-en-29-fiches.pdf
- IHEDN: https://ihedn.fr/
- NATO STANAG 2511 reliability and credibility: https://eturwg.c4i.gmu.edu/?q=node%2F128
- Admiralty code: https://en.wikipedia.org/wiki/Admiralty_code
- CIA Tradecraft Primer (structured analytic techniques): https://www.cia.gov/resources/csi/books-monographs/a-tradecraft-primer
- ACH (Pherson): https://pherson.org/wp-content/uploads/2013/06/Improving-Intelligence-Analysis-with-ACH.pdf
- Porter, The five competitive forces that shape strategy (HBR): https://hbr.org/2008/01/the-five-competitive-forces-that-shape-strategy
- McKinsey Three Horizons: https://www.mckinsey.com/capabilities/strategy-and-corporate-finance/our-insights/enduring-ideas-the-three-horizons-of-growth
- McKinsey 7-S: https://www.mckinsey.org/capabilities/strategy-and-corporate-finance/our-insights/enduring-ideas-the-7-s-framework
- Blue Ocean ERRC grid: https://www.blueoceanstrategy.com/tools/errc-grid/
- Wardley evolution stages: https://www.wardleymaps.com/glossary/evolution-stages
- Thoughtworks Technology Radar: https://www.thoughtworks.com/en-us/radar and https://www.thoughtworks.com/en-us/insights/blog/build-your-own-technology-radar
