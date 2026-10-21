# C02 → SSKS: suggested skill-list changes

These are changes C02 (Student Skill Profile) found while matching skills in student CVs. Nothing in
SSKS was edited. Please review and import what you accept. All IDs refer to the current SSKS seed
(`seed/import_ready/`).

| File | What it is | Rows |
|---|---|---|
| `new_skill_candidates.csv` | Skills SSKS does not have yet. Columns follow your candidate format (`entity_type`, `submitted_name`, `proposed_skill_type`, `proposed_skill_nature`, `source_component`, `source_reference`). | 11 |
| `alias_additions.csv` | Aliases students use that are missing, e.g. "JS" → JavaScript, "React.js" → React. | 76 |
| `alias_removals.csv` | Aliases that point to the wrong skill, with the correct skill where there is one. | 43 |

## The two kinds of removal

- **"Alias points to the wrong skill"**: e.g. "SQL" is an alias of *database management systems*,
  but SSKS also has *Structured query language SQL*.
- **"Possible duplicate skill"**: the alias is another skill's name, so the same skill exists twice
  (ESCO and O*NET), e.g. *Python (computer programming)* `SK-000591` and *Python* `SK-000899`.
  Merging these would fix the alias too.

## Once these are in SSKS

C02 removes the same entries from its own files. New skills keep their `C02-` ID in C02 until SSKS
gives them an `SK-` ID; after that, C02 automatically uses the SSKS skill instead.

Regenerate these files: `python -m scripts.export_for_ssks` (in `services/evidence-based-skill-profile/`).
