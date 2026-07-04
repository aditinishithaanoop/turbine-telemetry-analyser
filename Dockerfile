# Dockerfile - Turbine Telemetry Analyzer

# Build:
#  docker build -t telemetry-analyzer .

#Run (mount a directory containing telemetry_data.csv):
#   docker run --rm \
#       -v /path/to/data:/data \
#       telemetry-analyzer

# Override input/output/format via environment variables:
#   docker run --rm \
#       -v /path/to/data:/data \
#       -e TELEMETRY_INPUT=/data/my_file.csv \
#       -e TELEMETRY_OUTPUT=/data/report.json \
#       -e TELEMETRY_FORMAT=json \
#       telemetry-analyzer

FROM python:3.12-slim
LABEL description="Turbine telemetry anomaly detector"

# Non-root user - required for most cloud runtimes (GCP Cloud Run, ECS, etc.)
RUN groupadd --gid 1001 appuser && \
    useradd --uid 1001 --gid appuser --no-create-home appuser
WORKDIR /app

# Dependencies - install before copying source
# to ensure layer is cached on rebuilds when only the script changes
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Application source
COPY telemetry-analyzer.py .

# Default env vars - overridable at runtime
# TELEMETRY_INPUT : path to csv inside container
# TELEMETRY_OUTPUT : leave blank to skip writing a file
# TELEMETRY_FORMAT : json | csv
ENV TELEMETRY_INPUT=/data/telemetry_data.csv \
    TELEMETRY_OUTPUT="" \
    TELEMETRY_FORMAT=json

# Data volume - mount your local directory here
VOLUME ["/data"]
USER appuser

# Exit code 0 = all clear
# Exit code 1 = anomalies found (set by script)
# Exit code 2 = file/IO error
# Exit code 3 = schema error
ENTRYPOINT ["python", "telemetry-analyzer.py"]
