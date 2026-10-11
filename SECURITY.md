# Security scope

This repository is a teaching prototype for Cortex-M3/QEMU, not a supported production RTOS distribution. Only the provided GCC ARM_CM3 demonstration port is targeted by regression tests.

Do not feed unreviewed configurations into application builds or run untrusted pull requests on a runner with credentials or host access. The generator validates its schema and escapes strings, but application task code still needs review. Keep tokens, private keys, runner configuration and personal reports outside the repository.

Do not expose QEMU's GDB interface beyond localhost. Do not dynamically delete timeline tasks or register mutexes for forced semaphore release. The major-frame reset does not restore external resources or all application state.

The kernel is a modified development snapshot, not a verified copy of an upstream release. Before using another architecture, identify the upstream revision and review applicable [FreeRTOS security advisories](https://github.com/FreeRTOS/FreeRTOS-Kernel/security/advisories). In particular, [GHSA-vq2f-9qj3-jj2m](https://github.com/FreeRTOS/FreeRTOS-Kernel/security/advisories/GHSA-vq2f-9qj3-jj2m) affects ARMv8-M TrustZone secure contexts; the Cortex-M3 demos do not use those contexts. Bundling other ports does not establish that they are patched or safe.

For a suspected vulnerability, use GitHub's private vulnerability reporting if enabled by the repository owner. Do not post credentials or personal data in a public issue.
