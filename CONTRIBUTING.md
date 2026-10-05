# Branch and Commit Message Guide

Every team member follows these rules so the Git history stays easy to read and every change can
be traced to a person, a component and a feature.

## Branch names

```text
<YourName>-<COMPONENT>/<Feature>
```

| Part | What to write | Example |
|---|---|---|
| `YourName` | Your first name | `Salma` |
| `COMPONENT` | The code of the component you are working on (see the table below) | `SSK` |
| `Feature` | What the branch adds or changes, with words joined and no spaces | `Normalization` |

**Example:** `Salma-SSK/Normalization`

### Component codes

| Code | Component |
|---|---|
| `C01` | C01 Industry Skill Extraction |
| `C02` | C02 Student Skill Profile |
| `C03` | C03 Skill Gap Analysis and Career Readiness |
| `C04` | C04 Learning Skill Tree |
| `SSK` | Shared Skill Knowledge service |
| `AUTH` | Auth Service |
| `FE` | Frontend (web app) |
| `INFRA` | Infrastructure: Docker Compose, API gateway, database setup |

### More examples

```text
Salma-SSK/Normalization
Akalanka-AUTH/PasswordReset
Akalanka-FE/HomePage
Akalanka-INFRA/ApiGateway
```

## Commit messages

```text
<type>:<short description>
```

| Type | Use it for | Example |
|---|---|---|
| `feat` | A new feature | `feat:Implement the SSK schema` |
| `fix` | A bug fix | `fix:Implement the SSK schema fix` |
| `docs` | Documentation only (READMEs, guides, comments) | `docs:Implement the SSK schema docs` |

Write the description:

- starting with a verb, such as Implement, Add, Fix or Update
- short enough to fit on one line
- about **one** change; if a commit does two unrelated things, split it into two commits

## Day-to-day workflow

```bash
# 1. Start from the latest main
git checkout main
git pull

# 2. Create your branch
git checkout -b Salma-SSK/Normalization

# 3. Commit your work
git add .
git commit -m "feat:Implement the SSK schema"

# 4. Push the branch to GitHub
git push -u origin Salma-SSK/Normalization
```

Then open a pull request on GitHub to merge the branch into `main`.
