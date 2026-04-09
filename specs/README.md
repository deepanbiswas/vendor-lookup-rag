# Spec-driven development (SDD)

Specs live here as **reviewable documents** before and during implementation. Tests should trace to them.

## Workflow

1. **Draft** or extend the product spec (`vendor-lookup-agent-specifications.md`) with context, requirements, and scenarios.
2. **Review** the spec; agree on acceptance criteria.
3. **Red** — write failing tests that encode the acceptance criteria (TDD).
4. **Green** — implement until tests pass.
5. **Refactor** — keep tests green; update the spec if reality diverges.

## Linking tests to specs

Use the pytest marker `@pytest.mark.spec("specs/…#anchor")` so failures point back to the agreed behavior.

## Naming

- Primary document: `vendor-lookup-agent-specifications.md`. Add sections or scenario anchors (`#s1-…`) as the system grows.
- Optional extra files: `NNN-short-title.md` only if a topic deserves a separate long-lived document (e.g. a major subsystem).
