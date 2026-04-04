---
name: marc-6xx-synthesizer
description: Generates final MARC 21 subject strings ($a, $x, $z, $y) for topical, geographic, and name subjects. Uses LCGFT (655) for genre/form instead of $v subdivisions per current LC practice (H 1075, 2026).
---

# MARC 21 Subject Access Synthesizer

Generates properly formatted MARC 21 subject access fields (6XX) for catalog records following Library of Congress Subject Cataloging Manual guidelines, specifically **H 1075 (Subdivisions)**.

## Critical: LCGFT Implementation (2026)

**Effective February 2, 2026**, LC ceased adding form subdivisions ($v) to subject heading strings and expanded LCGFT use. This change applies to descriptions created in the Marva BIBFRAME editor. LC has no plan to retroactively convert existing records, and other institutions are not required to follow this practice.

Instead of $v subdivisions:
1. Use **LCGFT** in **655 fields** to express genre/form
2. Include **$0 URIs** when available for linked data

### Assigning LCGFT Terms (J 110)

**1. General rule:** Assign genre/form terms only as they **come readily to mind** after an initial review of the resource. Take the intent of the resource into account and display good judgment.

**2. Cataloging treatment:** Assign terms that correspond to the cataloging treatment:
- Continuing resource (periodical, series, collected set) → terms for the resource **as a whole**
- Single analytic → terms for the **single part**
- Text + commentary → assign terms for the text, the commentary, or both

**3. Specificity:** Assign terms **as specific as** the genres and forms exemplified. Use the BT/NT hierarchy in LCGFT to find the closest match. Assign a broader term when:
- No precise term can be established
- Several terms are needed (e.g., "Science fiction" + "Romance fiction" + "Novels" for a sci-fi romance novel)
- Special instructions require it

For **compilations** with a predominant genre that also include other forms, it is permissible to assign both a broader and a narrower term (e.g., "Limericks" + "Humorous poetry" for a collection mostly of limericks but also other humorous poetry).

**4. Number of terms:** Varies with the resource. Sometimes one is sufficient; sometimes a complement is necessary. **Do not assign a genre/form term to works that do not have an identifiable genre or form** (e.g., a historical study is not assigned LCGFT terms).

For resources with **separate parts** (e.g., text + DVD), also assign separate terms for parts if judged significant.

**5. No subdivisions (J 110 sec. 7):** LCGFT terms are **never subdivided** — not topically, geographically, chronologically, or by form.

**6. Objectivity:** Avoid assigning terms that express personal value judgments.

### 655 Field Coding (J 105)

```
655 #7 $a[Term].$2lcgft
```
- First indicator: **blank**
- Second indicator: **7** (source specified in $2)
- **$a** ends with a period or closing parenthesis
- **$2 lcgft** at the end of each field
- **$0** URI (optional): `$0 http://id.loc.gov/authorities/genreForms/gf...`
- **$3** for terms applying to parts of a resource: `655 #7 $3 volume 3: $a Biographies. $2 lcgft`
- Place 655 fields **after** all subject heading fields (6XX) and **before** genre/form terms from other vocabularies

### Before/After Examples

```
Current practice (old → new):

650 #0 $aWomen human rights workers$vDiaries.
→ 650 #0 $aWomen human rights workers.$0 [URI]
  655 #7 $aDiaries.$2lcgft$0 http://id.loc.gov/authorities/genreForms/gf2014026085

650 #0 $aStock quotations$vHandbooks, manuals, etc.
→ 650 #0 $aStock quotations.
  655 #7 $aHandbooks and manuals.$2lcgft

650 #0 $aDogs$vJuvenile literature.
→ 650 #0 $aDogs.
  655 #7 $aInformational works.$2lcgft
```

## Supported Field Types

| Tag | Description | Source | Example |
|-----|-------------|--------|---------|
| 600 | Personal Name Subject | LCNAF | Books ABOUT Shakespeare |
| 610 | Corporate Name Subject | LCNAF | Books ABOUT Library of Congress |
| 611 | Meeting Name Subject | LCNAF | Books ABOUT a conference |
| 630 | Uniform Title Subject | LCNAF | Books ABOUT a specific work |
| 650 | Topical Subject | LCSH | Companion planting |
| 651 | Geographic Subject | LCSH | United States—History |
| 655 | Genre/Form | LCGFT | Essays |

### Tag Selection for Named Entities (H 405)

Named entities are classified into two groups for authority file placement:
- **Group 1 (Name authority file):** Persons (100/600), corporate bodies (110/610), meetings (111/611), uniform titles (130/630), jurisdictions (151/651)
- **Group 2 (Subject authority file):** Geographic features, structures, events without formal names, etc. — established as 150/650 or 151/651

Common Group 1 entities: persons, biblical/fictitious/legendary characters, corporate bodies, schools, libraries, hospitals, churches, theaters, museums, ships, festivals, athletic contests, motion pictures, TV/radio programs, web sites.

Common Group 2 entities: buildings/structures, parks (geographic), historic sites, roads, bridges, tunnels, archaeological sites, awards, tribes (ethnic groups), families.

## Types of Subdivisions (H 1075 sec. C)

### C.1. Topical Subdivisions ($x)

Limit the concept to a subtopic. Examples:
- `Helicopters--Flight testing`
- `Mental health--Nutritional aspects`
- `Construction industry--Management--Employee participation`

### C.2. Geographic Subdivisions ($z)

Indicate geographic area where topic is located or from. Only use when heading is **authorized for geographic subdivision**. Examples:
- `Railroads$zFrance$xMaintenance and repair`
- `Church and state$zFrance$xHistory`

### C.3. Chronological Subdivisions ($y)

Indicate time periods. Usually follow `--History` subdivision, except for inherently historical topics. Examples:
- `Women--History--To 500`
- `Russia--Social conditions--1801-1917` (inherently historical, no --History needed)
- `French poetry--19th century` (literary period)

### C.4. Form Subdivisions ($v) — DEPRECATED

**LC Practice (2026):** Do NOT use form subdivisions. Use LCGFT instead.

Form subdivisions indicate what the item IS. When you would have used $v, instead:
1. Remove the $v subdivision from the subject string
2. Add a 655 field with the appropriate LCGFT term
3. Map old form terms to appropriate LCGFT equivalents

## Order of Subdivisions (H 1075 sec. D)

### D.1. [Place]--[Topic] Headings (651)

Used for aspects of a place (history, politics, economics, civilization, social conditions).

**Standard order:**
```
651 #0 $a[place]$x[topic]$y[chronological period].
655 #7 $a[form].$2lcgft
```

**Examples:**
```
651 #0 $aUnited States$xSocial conditions$y1980-

651 #0 $aGreat Britain$xKings and rulers$xTravel$zCanada.
655 #7 $aIllustrated works.$2lcgft
```

### D.2. [Topic]--[Place] Headings (650)

Used for topical headings authorized for geographic subdivision.

**Standard order (geography after main heading):**
```
650 #0 $a[topic]$z[place]$x[topic]$y[chronological period].
655 #7 $a[form].$2lcgft
```

**Standard order (geography after topical subdivision):**
```
650 #0 $a[topic]$x[topic]$z[place]$y[chronological period].
655 #7 $a[form].$2lcgft
```

**Examples:**
```
650 #0 $aRailroads$zFrance$xMaintenance and repair$xHistory$y19th century.
655 #7 $aIllustrated works.$2lcgft

650 #0 $aTuberculosis$xPatients$xHospital care$zMaryland$zBaltimore$xHistory$y20th century.
655 #7 $aBibliographies.$2lcgft
```

## Order and Meaning (H 1075 sec. E)

**The order of subdivisions affects meaning.** Test by reading elements in reverse order.

| Subject String | Meaning |
|----------------|---------|
| `Science$xHistory` + `655 Periodicals` | A periodical on the history of science |
| `Science$xPeriodicals$xHistory` | A history of periodicals in science |
| `Hospitals$xAdministration$xData processing$xEvaluation` | Evaluation of data processing in hospital administration |
| `Hospitals$xAdministration$xEvaluation$xData processing` | Data processing for evaluation of hospital administration |

## When Form Terms Become Topical ($x instead of $v)

Code a normally-form term as **$x** when the work is **ABOUT** that form, not an example of it:

```
Title: A bibliography of test study materials
OLD:  650 #0 $aExaminations$xStudy guides$vBibliography.
NEW:  650 #0 $aExaminations$xStudy guides.
      655 #7 $aBibliographies.$2lcgft
[The work is a bibliography ABOUT study guides, not a study guide itself.
"Study guides" is coded $x because it's what the bibliography is about.]

Title: Metals handbook comprehensive index
OLD:  650 #0 $aMetals$xHandbooks, manuals, etc.$vIndexes.
NEW:  650 #0 $aMetals$xHandbooks, manuals, etc.
      655 #7 $aIndexes.$2lcgft
[The work is an index TO handbooks, not a handbook itself.
"Handbooks, manuals, etc." is coded $x.]
```

## Geographic Subdivision Rules (H 830)

### Indirect Method (General Rule)
When a heading is authorized for geographic subdivision (*(May Subd Geog)*), use the **indirect method**: interpose the country name between the heading and the subordinate locality.

```
650 #0 $aMusic$zSwitzerland$zGeneva.
650 #0 $aArt$zFrance$zParis.
```

### Two-Level Maximum
Include no more than **two levels** of geographic subdivision. Use the country (or first-order division for US/UK/Canada) as the collecting level.

```
CORRECT:   650 #0 $aLaw$zSpain$zPamplona.
INCORRECT: 650 #0 $aLaw$zSpain$zNavarre$zPamplona.
```

### Exceptions: US, Canada, Great Britain (H 830 sec. C.5.a)
Do NOT interpose the country name for first-order divisions of these three countries:

| Country | First-order Division | Example |
|---------|---------------------|---------|
| United States | States | `$zCalifornia$zSan Francisco` (not `$zUnited States$z...`) |
| Canada | Provinces | `$zOntario$zToronto` (not `$zCanada$z...`) |
| Great Britain | Constituent countries | `$zEngland$zLondon` (not `$zGreat Britain$z...`) |

### Other Exceptions
- **Regions larger than countries:** Use directly (e.g., `$zRocky Mountains`, `$zEurope`)
- **Washington (D.C.) and Jerusalem:** Assign directly after topics, no country interposed
- **Inverted region headings:** Use directly (e.g., `$zItaly, Southern` not `$zItaly$zItaly, Southern`)
- **Latest name/sovereignty:** Always use current names and sovereignties

### Qualifier Deletion (H 830 sec. C.6)
Delete the country/state from a locality's qualifier when it duplicates the interposed subdivision:
```
Paris (France)   → $zFrance$zParis          [delete "(France)"]
Seattle (Wash.)  → $zWashington (State)$zSeattle  [delete "(Wash.)"]
```

## Subdivisions Further Subdivided by Place (H 860)

When combining a heading with both a topical subdivision and a geographic subdivision, place the $z after the **last subdivision that is authorized for further subdivision by place**.

```
--Finance                           → NOT (May Subd Geog)
--Finance--Law and legislation      → (May Subd Geog)
--Services for                      → (May Subd Geog)

650 #0 $aMedical colleges$zCalifornia$xFinance.
650 #0 $aMedical colleges$xFinance$xLaw and legislation$zCalifornia.
```

This determines the two possible orders in D.2:
- `$a[topic]$z[place]$x[topic]...` — when the main heading is authorized for geographic subdivision
- `$a[topic]$x[topic]$z[place]...` — when only the topical subdivision is authorized for further place subdivision

## Subfield Order Summary

### Topical Subjects (650)
```
$a Main heading → $z Geographic → $x Topical → $y Chronological
```
(Form now in separate 655 field)

### Geographic Subjects (651)
```
$a Place → $x Topical → $y Chronological
```
(Additional $z only if topic involves travel/relations to another place)

**Form of geographic name in $a (H 690):** Use the established form from the authority file. For non-jurisdictional features, the heading is formulated with the distinctive portion first:
- Inverted English names: `Erie, Lake` / `Fuji, Mount (Japan)` / `Forth, Firth of (Scotland)`
- Translated foreign names: `Jiloca River (Spain)` (from Río Jiloca) / `Cévennes Mountains (France)` (from Les Cévennes)
- Qualifiers per H 810 indicate location: `Yellow River (China)` / `El Capitan (Calif.)`
- See the **lc-authority** skill (H 690 section) for full formulation rules

### Name Subjects (600, 610, 611)
```
$a Name → $b Numeration → $c Titles → $d Dates → $n Number → $q Fuller form → $t Title → $x Topical → $y Chronological
```

### Uniform Title Subjects (630)
```
$a Title → $p Part → $l Language → $x Topical → $y Chronological
```

### Genre/Form (655)
```
$a Term.$2lcgft
```


## Indicator Reference

### 600 (Personal Name)
- First indicator: 0=Forename, 1=Surname, 3=Family name
- Second indicator: 0=LCSH

### 610 (Corporate Name)
- First indicator: 1=Jurisdiction, 2=Direct order
- Second indicator: 0=LCSH

### 611 (Meeting Name)
- First indicator: 0=Inverted, 1=Jurisdiction, 2=Direct order
- Second indicator: 0=LCSH

### 630 (Uniform Title)
- First indicator: Number of nonfiling characters (0-9)
- Second indicator: 0=LCSH

### 650 (Topical)
- First indicator: (blank)=No info, 0=No level, 1=Primary, 2=Secondary
- Second indicator: 0=LCSH

### 651 (Geographic)
- First indicator: (blank)
- Second indicator: 0=LCSH

### 655 (Genre/Form)
- First indicator: (blank)
- Second indicator: 7 (source in $2)

## Integration with lc-authority Skill

The synthesizer integrates with the lc-authority skill for validated headings:

```python
import sys
sys.path.append("path/to/lc-authority/scripts")
from lcnaf_api import check_name_authority
from marc_synthesizer import MARCSynthesizer

# Look up name in LCNAF
result = check_name_authority("William Shakespeare")

# Generate MARC field from LCNAF result
marc_field = MARCSynthesizer.from_lcnaf(
    result,
    subdivisions={'x': 'Criticism and interpretation'}
)
# Output: 600 10 $aShakespeare, William,$d1564-1616$xCriticism and interpretation.
```

## Complete Cataloging Example

**Title:** A children's illustrated guide to the history of railroads in France

**Old practice (pre-2026):**
```
650 #0 $aRailroads$zFrance$xHistory$vJuvenile literature$vPictorial works.
```

**Current LC practice (2026):**
```
650 #0 $aRailroads$zFrance$xHistory.
655 #7 $aIllustrated works.$2lcgft
655 #7 $aInformational works.$2lcgft
```

## Quality Checklist

### Subject Headings (6XX)
- [ ] Correct tag for entity type (600/610/611/630/650/651)?
- [ ] First indicator correct for name entry type?
- [ ] Second indicator "0" for LCSH?
- [ ] Subdivisions in correct order ($a → $z → $x → $y)?
- [ ] No $v form subdivisions in subject strings?
- [ ] Subdivision order expresses intended meaning (test by reading in reverse)?
- [ ] "About" forms coded as $x, not $v?
- [ ] For names: authorized LCNAF form used with dates?

### Genre/Form (655) — J 110 / J 105
- [ ] LCGFT terms assigned only as they come **readily to mind**?
- [ ] Terms **as specific as** the genres/forms exemplified?
- [ ] No LCGFT term assigned for works with **no identifiable genre/form**?
- [ ] LCGFT terms are **NOT subdivided** (no $x, $z, $y, $v)?
- [ ] 655 coding: ind1=blank, ind2=7, $a ends with period, $2 lcgft?
- [ ] 655 fields placed **after** all subject heading fields?
- [ ] $3 used for terms applying to **parts** of a resource?
- [ ] For compilations: broader+narrower terms both assigned if appropriate?

## References

- **H 690** - Formulating Geographic Headings (form of name for 651 $a)
- **H 810** - Geographic Heading Qualifiers
- **H 830** - Geographic Subdivisions
- **H 860** - Subdivisions Further Subdivided by Place
- **H 1075** - Subdivisions (Subject Headings Manual)
- **H 1095** - Free-Floating Subdivisions
- **H 620** - Chronological Subdivisions
- **J 110** - Assigning Genre/Form Terms (LCGFT Manual)
- **J 105** - MARC Coding of LC Genre/Form Terms
- **J 107** - MARC Authority Records for LC Genre/Form Terms
