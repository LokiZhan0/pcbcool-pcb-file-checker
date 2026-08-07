FROM python:3.12-slim

LABEL org.opencontainers.image.title="PCBCool PCB File Checker" \
      org.opencontainers.image.description="Checks PCB packages for common Gerber, drill, BOM, and placement files." \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.vendor="PCBCool" \
      org.opencontainers.image.url="https://pcbcool.com/" \
      org.opencontainers.image.licenses="MIT"

WORKDIR /app
COPY pcb_file_checker.py /app/pcb_file_checker.py

RUN useradd --create-home --uid 10001 pcbcheck \
    && chmod 0555 /app/pcb_file_checker.py

USER pcbcheck

ENTRYPOINT ["python", "/app/pcb_file_checker.py"]
CMD ["/data"]
