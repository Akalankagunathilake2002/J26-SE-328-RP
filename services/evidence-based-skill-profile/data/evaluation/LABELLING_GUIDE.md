# Evidence-type labelling guide

These rules are used to label CV sentences in `evidence_labels.csv` (TAF tasks 6 and 10). Each row is
one CV sentence that contains at least one skill. The label says **how the sentence supports the
skill**, not whether the skill is real.

## Labels

| Label | Use when the sentence… | Examples |
|---|---|---|
| `project_demonstrated` | describes the person **doing** something with the skill: a task, duty, project or result, in any tense, including duty phrases without an action verb ("Responsible for…", "In charge of…") | "Converted VMWare to Hyper-V", "Compose service reports monthly", "In charge of company website management" |
| `cv_self_reported` | only **lists or claims** the skill or a quality, with no activity described: skill lists, "knowledge of", "proficient in", "experienced in", job-title lines, memberships, awards | "Python, Java, SQL", "Knowledge of Quickbooks", "SENIOR HR MANAGER", "Member of SHRM" |
| `academic_exposure` | says the skill was **learned**: a degree, major/minor, module, coursework, training course or programme | "Minor in Psychology", "Coursework in Network Monitoring", "KARTA Information Security Awareness" |
| `certificate_supported` | names a **certification or licence** | "PMP", "VMware Certified Professional", "CPR certified" |
| `unverified_mention` | only shows **interest** or very weak contact: "interested in", "want to learn", "familiar with" | "Interested in learning Kubernetes" |
| `skip` | is not about the person or is too broken to judge: company descriptions, fragments | "The Signature Group is a market leader…" |

## Deciding hard cases

1. **Action beats section.** A concrete task in the Summary is still `project_demonstrated`; a claim in
   Experience ("Extensive working knowledge of…") is still `cv_self_reported`.
2. **Adjective, not action.** "Organized HR Generalist effective at record maintenance" is a claim
   (`cv_self_reported`): "Organized" describes the person.
3. **Job titles alone** ("ASP.NET WEB DEVELOPER", "Company Name City, State HR Assistant") are
   `cv_self_reported`: a role is named, no activity is described.
4. **Certification vs course:** a named certification or licence is `certificate_supported`; a course
   or training without a certification is `academic_exposure`.
5. **Mixed sentences:** label the strongest evidence the sentence gives for its skills.
6. When unsure, write the reason in `note`.

## Checking

The labels were first suggested by the assistant and must be checked by the researcher. For each row,
read `sentence` (and `section`), then either leave `label` as it is or change it, and write `yes` in
`checked`. Rows with a `note` were doubtful and need most attention. Only the rows marked `train`
are used to train the model; rows marked `test` are only used to measure it, so do not change the
split after seeing results.

`rule_label` is what the v1 rules decided, for comparison only.
