FROM debian:bookworm-slim
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      ca-certificates make gcc-arm-none-eabi libnewlib-arm-none-eabi \
      qemu-system-arm gdb-multiarch python3 \
 && rm -rf /var/lib/apt/lists/* \
 && useradd --create-home --uid 1000 builder
USER builder
WORKDIR /home/builder/project
COPY --chown=builder:builder . .
CMD ["bash"]
