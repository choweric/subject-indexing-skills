---
name: lcsh-quantitative-filtering
description: Applies the LCSH 20% Rule and the Rule of Three to a list of identified concepts. Use when a user has a list of topics and needs to know which ones merit authorized headings according to SHM H 180.
---

# LCSH Quantitative Rule Validator (SHM H 180)

Apply these rules to filter and prioritize subject headings from a conceptual analysis.

## Step 1: The 20% Rule (H 180 sec. D)

**General Rule:** Assign headings only for topics that comprise at least 20% of the work.

**Exceptions:**
- **Named Entities (sec. N.3):** Assign headings for persons, families, corporate bodies, events, buildings, named products, etc., that are *critical to the subject of the work as a whole*, even if discussion of them does not form 20% of the work.
- **Separate Parts:** For works with distinct parts (e.g., text + bibliography, book + accompanying disc), assign separate headings for parts that are ≥20% AND judged significant.

**Do NOT assign headings for:**
- Topics in works of very general or amorphous nature (general periodicals, essay collections with no theme)
- Texts of sacred works or belles lettres with no identifiable theme (cf. H 1775 sec. 3.c.)

## Step 2: Number and Order of Headings (H 180 sec. F; H 80)

| Guideline | Rule |
|-----------|------|
| Minimum | 1 heading may be sufficient |
| Typical maximum | 6 headings |
| LC practice maximum | 10 headings |
| Order | Assign in order of **predominance** (see below) |

### Ordering by Predominance (H 80)

1. **General rule:** Assign the heading for the **predominant topic** as the first subject heading. If the predominant topic cannot be represented by a single heading, assign as the first and second headings the two headings that, taken together, express it. If one of the two more closely approximates the class number, assign it first.
2. **Biography:** For works of individual biography, assign as the **first** subject heading the **name of the biographee**.
3. **Two equally important topics:** Assign heading(s) for the second topic immediately after heading(s) for the first, before any secondary topics.
4. **Secondary topics:** Assign headings for secondary topics, and headings to complete standard arrays, in **any order** following the heading(s) for the major topic(s).

Note: LC does not apply the MARC 21 provision for primary/secondary descriptors in the first indicator of 650 fields.

## Step 2b: Cataloging Treatment (H 180 sec. E)

Assign headings that correspond to the **cataloging treatment** of the work:
- **Collected sets** (periodicals, series, multipart items): assign headings for the general contents of the set as a whole.
- **Single analytics** (one part of a multipart set): assign headings for the specific contents of the analytic item.
- **Text + commentary:** assign headings based on the descriptive treatment (cf. H 1435).
- Assign headings based on **analysis of the contents** of the work. Subject headings do not need to be justified by descriptive cataloging notes.

## Step 3: Specificity (H 180 sec. G)

Assign headings that are **as specific as the topics they cover**.

- Specificity is **relative** to the work, not inherent to the heading
- Example: "Psychology" is specific when applied to an introductory psychology textbook
- Follow the **hierarchical reference structure** (BT/NT in the subject authority file, cf. H 370) to find the closest match between topic and available headings
- Only assign a broader heading when: (a) no precise heading can be established, (b) an array of headings is needed to express the topic, or (c) the SHM contains special instructions to do so
- If a needed heading is neither established nor can be approximated, it may be appropriate to propose a new heading (cf. H 187)

## Step 4: Depth of Indexing (H 180 sec. H)

**Do NOT** assign headings for subtopics that are normally subsumed under an assigned broader heading.

**Example:**
```
Title: Beginning gymnastics
CORRECT:   650 0 $aGymnastics.
INCORRECT: Also adding headings for parallel bars, balance beam,
           vaulting horse, tumbling (these are subsumed)
```

## Step 5: Rule of Three (H 180 sec. K)

When a general topic includes more than three subtopics in its scope:

| Subtopics Discussed | Action |
|---------------------|--------|
| 2-3 subtopics | Assign specific headings for each subtopic |
| 4+ subtopics | Assign the **broad heading** instead |

**Example (2-3 subtopics):**
```
Title: South Carolina fruit tree survey: peaches-apples
650 0 $aPeach $zSouth Carolina.
650 0 $aApples $zSouth Carolina.
655 7 $aStatistics. $2lcgft
```

## Step 6: Rule of Four Exception (H 180 sec. L)

**Exception:** If a heading covers a **very broad range** where each subtopic forms only a small portion of that range, assign headings for four subtopics instead of the broad heading.

**Example:** For a work discussing four American literary authors, assign a heading for each author rather than "American literature--History and criticism" (which covers ALL American authors).

**LC practice:** Do not exceed four subtopics under any circumstances.

## Step 7: Two or Three Related Headings (H 180 sec. J)

If a **single heading exists** (or can be established) that represents the two or three topics discussed, and includes no other topics, assign the ONE heading instead of multiple narrower headings.

**Example:**
```
Title: In praise of single parents: mothers and fathers embracing the challenge
CORRECT:   650 0 $aSingle parents $zUnited States.
INCORRECT: 650 0 $aSingle mothers $zUnited States.
           650 0 $aSingle fathers $zUnited States.
```

## Step 8: General Topic with Subtopic (H 180 sec. I)

If a work discusses a **general topic with emphasis on a particular subtopic**, assign headings for BOTH, provided the subtopic treatment is ≥20%.

**Example:**
```
Title: Revolutions yesterday and today
[Survey of revolutions with emphasis on Cuban Revolution of 1959]
650 0 $aRevolutions $xHistory.
651 0 $aCuba $xHistory $yRevolution, 1959.
```

## Step 9: Multi-element Topics (H 180 sec. M)

For **complex compound topics** where a single heading neither exists nor can be practically constructed, assign multiple headings to bring out separate aspects.

**Example:**
```
Title: Cancer morbidity and mortality among Danish brewery workers
650 0 $aCancer $zDenmark.
650 0 $aCancer $xMortality $zDenmark.
650 0 $aBrewery workers $xDiseases $zDenmark.
650 0 $aBrewery workers $xMortality $zDenmark.
```

## Step 10: Additional Aspects (H 180 sec. N)

Bring out important additional aspects in assigned headings:

| Aspect | Guidance | Reference |
|--------|----------|-----------|
| **Place** | Geographic location, setting, origin | H 690 - H 910 |
| **Time** | Chronological aspects where LCSH allows | H 620 |
| **Named Entities** | Persons, events, buildings, etc. (can bypass 20% rule if critical) | H 430, H 405 |
| **Form/Genre** | Use LCGFT terms instead of form subdivisions | See below |

## Step 11: Concepts in Titles (H 180 sec. O)

Titles and subtitles sometimes state the subject matter in the author's/publisher's own words. Bring out each topic of **subject retrieval value** identified in the title/subtitle and discussed in the work. Apply judgment:

- If the title is **misleading, euphemistic, or cryptic**, do not use it as a guide to contents.
- If the title is **general** but the work is on a more specific topic, assign heading(s) for the **specific topic**.
- If many topics are listed on the title page (like a table of contents), **treat them as a table of contents** and apply the Rule of Three/Four.
- If a topic in the title is one that LC policy does not express in subject headings, do not bring it out.

## Step 12: Objectivity (H 180 sec. Q)

**Avoid assigning headings that label topics or express personal value judgments.** Headings should not reflect a cataloger's opinion about the contents. Consider the **intent of the author or publisher** and assign headings for that orientation without being judgmental. Follow stated intentions regarding readership, audience level, treatment as fact or fiction, etc.

## Step 13: LCGFT Assignment (J 110; H 180 sec. D, N.4; H 1075 sec. C.4)

**LC practice (effective Feb 2, 2026):** LC catalogers no longer use form subdivisions ($v). Instead, assign **LCGFT** terms in 655 fields.

### J 110 Assignment Rules

1. **General rule:** Assign LCGFT terms only as they **come readily to mind** after initial review. Take the resource's intent into account. Use good judgment when assigning terms from multiple hierarchy levels.

2. **Specificity:** Assign terms **as specific as** the genres/forms exemplified. Use the BT/NT hierarchy in LCGFT authority records. Assign a broader term when: (a) no precise term exists, (b) several terms are needed (e.g., "Science fiction" + "Romance fiction" + "Novels"), or (c) special instructions require it. For **compilations** with a predominant genre, both broader and narrower terms may be assigned.

3. **Number of terms:** Varies. Sometimes one is sufficient; sometimes a complement is necessary. **Do not assign LCGFT to works with no identifiable genre or form** (e.g., a general historical study).

4. **Separate parts:** For resources with distinct parts (text + DVD, etc.), assign separate terms for parts if judged significant.

5. **No subdivisions:** LCGFT terms are **never subdivided** — not topically, geographically, chronologically, or by form.

6. **Objectivity:** Do not assign terms that express personal value judgments.

### Examples
```
Title: Beginning gymnastics
650 0 $aGymnastics.
655 7 $aInstructional and educational works. $2lcgft

Title: A butterfly in winter : a novel
655 7 $aRomance fiction. $2lcgft
655 7 $aNovels. $2lcgft

Title: American crucible : race and nation in the twentieth century
[Historical study — no identifiable genre/form. No 655 assigned.]

Title: Children's illustrated guide to railroads in France
650 0 $aRailroads $zFrance.
655 7 $aIllustrated works. $2lcgft
655 7 $aInformational works. $2lcgft
```

## Decision Flowchart

```
Identified Concept
        │
        ▼
   Is it ≥20% of work?
        │
    ┌───┴───┐
   YES      NO
    │        │
    │        ▼
    │   Is it a Named Entity
    │   critical to the work?
    │        │
    │    ┌───┴───┐
    │   YES      NO
    │    │       │
    │    │       ▼
    │    │   DO NOT ASSIGN
    │    │
    ▼    ▼
  CANDIDATE HEADING
        │
        ▼
  Apply Rule of Three/Four
        │
        ▼
  Check for encompassing heading (sec. J)
        │
        ▼
  Apply specificity check
        │
        ▼
  Add place/time/form aspects
        │
        ▼
  Order by predominance (H 80)
        │
        ▼
  Add LCGFT 655
        │
        ▼
  FINAL HEADING(S)
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Too many headings (>10) | Move up hierarchy to broader terms; apply Rule of Three |
| Overlapping subtopics | Check if one heading encompasses the others (sec. J) |
| Compound topic with no heading | Use multi-element approach (sec. M) |
| Subtopics subsumed by broader | Remove subtopic headings; keep only the broader heading |
| Form subdivision needed | Use LCGFT 655 field instead of $v |
| Misleading title | Do not use title as guide; analyze actual contents (sec. O) |
| No precise heading exists | Use broader heading, or propose a new heading (cf. H 187) |
