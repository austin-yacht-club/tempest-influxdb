FROM python:3.11-slim

# Install system dependencies for network access
RUN apt-get update && apt-get install -y \
    iputils-ping \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt /app/
RUN pip3 install --no-cache-dir -r /app/requirements.txt

# Copy source code
COPY main.py /app/

# Set the working directory
WORKDIR /app

# Make the main script executable
RUN chmod +x main.py

# Set default environment variables for Tempest
ENV TEMPEST_PROTOCOL=tcp
ENV TEMPEST_TCP_PORT=50222
ENV TEMPEST_UDP_PORT=50222
ENV TEMPEST_PUBLISH_INTERVAL=60
ENV TEMPEST_DEBUG=false

# Set default environment variables for InfluxDB
ENV INFLUXDB_URL=http://localhost:8086
ENV INFLUXDB_ORG=home
ENV INFLUXDB_BUCKET=tempest
ENV INFLUXDB_MEASUREMENT=weather
# INFLUXDB_TOKEN must be provided at runtime

# Create entrypoint script
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
# Tempest defaults\n\
PROTOCOL="${TEMPEST_PROTOCOL:-tcp}"\n\
TCP_PORT="${TEMPEST_TCP_PORT:-50222}"\n\
UDP_PORT="${TEMPEST_UDP_PORT:-50222}"\n\
PUBLISH_INTERVAL="${TEMPEST_PUBLISH_INTERVAL:-60}"\n\
DEBUG="${TEMPEST_DEBUG:-false}"\n\
\n\
# InfluxDB defaults\n\
INFLUX_URL="${INFLUXDB_URL:-http://localhost:8086}"\n\
INFLUX_ORG="${INFLUXDB_ORG:-home}"\n\
INFLUX_BUCKET="${INFLUXDB_BUCKET:-tempest}"\n\
INFLUX_MEASUREMENT="${INFLUXDB_MEASUREMENT:-weather}"\n\
\n\
echo "Tempest Weather Station InfluxDB Publisher Starting..."\n\
echo "Protocol: ${PROTOCOL^^}"\n\
if [ "$PROTOCOL" = "tcp" ]; then\n\
    echo "TCP Port: $TCP_PORT"\n\
else\n\
    echo "UDP Port: $UDP_PORT"\n\
fi\n\
echo "Publish Interval: $PUBLISH_INTERVAL seconds"\n\
echo "Debug Mode: $DEBUG"\n\
echo ""\n\
echo "InfluxDB Configuration:"\n\
echo "  URL: $INFLUX_URL"\n\
echo "  Organization: $INFLUX_ORG"\n\
echo "  Bucket: $INFLUX_BUCKET"\n\
echo "  Measurement: $INFLUX_MEASUREMENT"\n\
echo ""\n\
\n\
# Check for required token\n\
if [ -z "$INFLUXDB_TOKEN" ]; then\n\
    echo "ERROR: INFLUXDB_TOKEN environment variable is required"\n\
    exit 1\n\
fi\n\
\n\
# Build command line arguments\n\
ARGS=("--protocol" "$PROTOCOL" "--publish-interval" "$PUBLISH_INTERVAL")\n\
ARGS+=("--influxdb-url" "$INFLUX_URL")\n\
ARGS+=("--influxdb-token" "$INFLUXDB_TOKEN")\n\
ARGS+=("--influxdb-org" "$INFLUX_ORG")\n\
ARGS+=("--influxdb-bucket" "$INFLUX_BUCKET")\n\
ARGS+=("--influxdb-measurement" "$INFLUX_MEASUREMENT")\n\
\n\
if [ "$PROTOCOL" = "tcp" ]; then\n\
    ARGS+=("--tcp-port" "$TCP_PORT")\n\
else\n\
    ARGS+=("--udp-port" "$UDP_PORT")\n\
fi\n\
\n\
if [ "$DEBUG" = "true" ]; then\n\
    ARGS+=("--debug")\n\
fi\n\
\n\
# Add any additional arguments passed to the container\n\
ARGS+=("$@")\n\
\n\
# Run the Tempest publisher\n\
exec python3 /app/main.py "${ARGS[@]}"\n\
' > /app/entrypoint.sh

RUN chmod +x /app/entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Default command (can be overridden)
CMD []
