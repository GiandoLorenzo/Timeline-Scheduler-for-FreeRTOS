# Linux build container

Run from the repository root:

```bash
docker build -f DOCKERFILE/Dockerfile -t freertos-timeline .
docker run --rm -it freertos-timeline bash
```

Then run `make -C Demo all` and `make -C Demo qemu_start` inside the container. Exit QEMU with Ctrl+A, then X.

The image runs as a non-root user and copies the project during the build. Rebuild after editing sources. It contains Python, the ARM toolchain, QEMU and GDB; no GitLab runner, tokens or runtime host mounts are required.

The base tag and Debian package repositories can change. For bit-for-bit reproducible builds, maintain a tested image digest and package snapshot; the current image prioritizes ease of setup. Docker isolation is not a guarantee against malicious code. Avoid privileged mode and Docker socket mounts.
