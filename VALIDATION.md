# Release preparation checks

Checked on 2026-10-11:

- Eight Python unittest cases passed, including schema rejection, C-string escaping, generator write failures, exact result matching, real subprocess timeout handling and rejection of early process exits.
- `Tools/generated_main.c` was regenerated successfully from the example configuration.
- Native GCC `-fsyntax-only -std=gnu11` accepted the kernel source subset, ARM_CM3 port, startup/UART sources and each of the eight timeline scenarios, the priority demo, the timeline demo and the generated application.
- The public PDF has nine pages, no original names/student identifiers in extracted text or metadata, and an unchanged report body after its replacement cover. The replacement cover was rendered and visually checked.
- A pattern scan of publication files found no original student identifiers or common private-key/GitHub/GitLab/AWS credential patterns. This is a pattern-based check, not a guarantee that no secret of any kind exists.

Still required before public release:

- Run the actual ARM build and QEMU regression suite. Native syntax checks do not validate ARM code generation, linking, timing or scheduler runtime behavior.
- Build and run the Docker image in an environment with Docker installed.
- Review the initial Git staging list. This downloaded folder has no original Git history.
- Confirm the right to publish the coursework and retain applicable copyright notices.

GitHub Actions contains the ARM build and QEMU checks, including the normal and generated demos. Initially push to a private repository and review all CI results before changing visibility. No upstream revision or passing firmware result is claimed without verification.
