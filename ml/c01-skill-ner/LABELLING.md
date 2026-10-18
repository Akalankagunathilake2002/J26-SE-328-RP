# Labelling guide: skills in topjobs ads

You label the **test set**: 100 topjobs ads, picked at random. These labels are the answer key the
lexicon and the NER models are scored against, so label what the ad asks for, not what you think a
tool would find. The ads are never used for training.

## Setup (Label Studio)

1. `pip install label-studio` (in any Python environment), then `label-studio start`.
2. Create a project. Under **Labeling Interface → Code**, paste `configs/label_studio.xml`.
3. **Import** `data/topjobs_test/tasks.json`.
4. Label every task, then **Export → JSON** and save the file as
   `data/topjobs_test/labelled.json`. Don't edit the ad texts.

## What to label: one label, SKILL

Highlight every mention of something the employer wants the person to **know or be able to do**:

| Label it | Examples |
|---|---|
| Tools, software, technologies | `Python`, `MS Excel`, `Sage Payroll`, `SAP`, `AutoCAD` |
| Knowledge areas and methods | `labour law`, `HACCP`, `payroll`, `IFRS`, `agile`, `recruitment` |
| Abilities and tasks | `prepare monthly payroll`, `handle employee grievances`, `manage the recruitment process` |
| Soft skills | `communication skills`, `teamwork`, `leadership`, `attention to detail` |
| Languages | `English`, `Sinhala`, `Tamil` |

Don't label:

- **Qualifications:** degrees, diplomas, A/L, professional memberships (`Bachelor's degree in HR`, `CIMA`).
- **Experience:** `2 years of experience`, `senior level`.
- **Personal traits that are not skills:** age, gender, `below 40 years`, `pleasing personality`.
- **Benefits, salary, the company, the job title, contact or application details.**

## Where a span starts and ends

- **Leave out** words that only say how much or how well: `strong`, `excellent`, `good`, `sound`,
  `knowledge of`, `ability to`, `experience in`, `proficiency in`.
  - `Excellent communication skills` → `communication skills`
  - `Sound knowledge of labour law` → `labour law`
  - `Ability to work under pressure` → `work under pressure`
- **Keep** a task's verb and object together: `prepare monthly payroll`, not just `payroll`.
- **Split lists** into one span per item: `MS Word, Excel and PowerPoint` → `MS Word`, `Excel`,
  `PowerPoint`. If the items share a word (`written and spoken English`), label the whole phrase once.
- **One line at most:** a span never continues onto the next line.
- **OCR mistakes:** label the text as it is (`Microsoft fice`, `Linkedin`). Skip lines that are pure
  noise.
- **Not sure?** Leave it out, and note the task number. Be consistent rather than perfect.

## Time

Expect about 3–5 minutes per ad (5–8 hours in total). Labelling in several sittings is fine.
If someone else can label 20 of the same ads separately, we can report how far two people agree.
