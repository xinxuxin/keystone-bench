# Security

Keystone ships data, prompts and a small evaluation library. It has one runtime dependency and executes no
model output. The two things worth reporting:

- **A defect that could expose HealthBench prose.** The repository stores span references, never source text.
  If you find a released file that contains verbatim benchmark prose, report it privately rather than in an issue.
- **A vulnerability in the library or the release builder** (`tools/build_release.py`, `keystone/`).

Use GitHub's private vulnerability reporting on this repository (Security → Report a vulnerability).
Please do not open a public issue for either case.

Everything else, including questions about the data, belongs in a normal issue.
