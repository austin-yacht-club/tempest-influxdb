# Tempest Weather Station InfluxDB Publisher

A standalone service that receives TCP/UDP data from a local Tempest weather station and writes it directly to InfluxDB.

## Overview

This publisher listens for TCP length-prefixed messages or UDP broadcasts from Tempest weather stations and writes comprehensive weather data to InfluxDB, including wind, temperature, humidity, pressure, precipitation, and lightning information.

## Features

- **Direct InfluxDB Integration**: Writes weather data directly to InfluxDB 2.x
- **Comprehensive Weather Data**: Wind speed/direction, temperature, humidity, pressure, precipitation, lightning
- **Multiple Data Sources**: Supports observation (`obs_st`), rapid wind (`rapid_wind`), and hub status messages
- **TCP and UDP Support**: TCP (default) for reliability, UDP for backward compatibility
- **Automatic Parsing**: Parses Tempest message formats automatically
- **Robust Error Handling**: Continues operating even with intermittent data issues
- **Docker Support**: Containerized for easy deployment
- **Configurable**: Customizable ports, publish intervals, InfluxDB settings

## InfluxDB Schema

Data is written to a single measurement with tags and fields.

### Tags

| Tag | Description |
|-----|-------------|
| `sensor` | Always `tempest-weather-station` |
| `source` | Message type: `obs_st`, `rapid_wind`, `hub_status`, or `status` |
| `device_sn` | Tempest device serial number |
| `hub_sn` | Tempest hub serial number |

### Fields (obs_st)

| Field | Units | Description |
|-------|-------|-------------|
| `wind_lull_kt` | knots | Wind lull speed |
| `wind_avg_kt` | knots | Average wind speed |
| `wind_gust_kt` | knots | Wind gust speed |
| `wind_direction` | degrees | Wind direction |
| `wind_sample_interval` | seconds | Wind sample interval |
| `pressure_hpa` | hPa | Barometric pressure |
| `pressure_inhg` | inHg | Barometric pressure |
| `temperature_c` | °C | Air temperature |
| `temperature_f` | °F | Air temperature |
| `humidity` | % | Relative humidity |
| `illuminance_lux` | lux | Illuminance |
| `uv_index` | index | UV index |
| `solar_radiation_wm2` | W/m² | Solar radiation |
| `rain_since_report_mm` | mm | Rain since last report |
| `rain_daily_mm` | mm | Daily rainfall |
| `lightning_distance_km` | km | Lightning distance |
| `lightning_count` | count | Lightning strike count |
| `battery_v` | volts | Battery voltage |
| `report_interval_min` | minutes | Report interval |

### Fields (rapid_wind)

| Field | Units | Description |
|-------|-------|-------------|
| `wind_instant_kt` | knots | Instant wind speed |
| `wind_direction_instant` | degrees | Instant wind direction |

### Fields (hub_status)

| Field | Units | Description |
|-------|-------|-------------|
| `hub_uptime_s` | seconds | Hub uptime |
| `hub_rssi` | dBm | Signal strength |
| `hub_firmware` | string | Firmware version |

## Installation

### Docker (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd tempest-influxdb

# Build the container
docker build -t tempest-influxdb .

# Run with required InfluxDB configuration
docker run --network host \
  -e INFLUXDB_URL=http://localhost:8086 \
  -e INFLUXDB_TOKEN=your-influxdb-token \
  -e INFLUXDB_ORG=home \
  -e INFLUXDB_BUCKET=tempest \
  tempest-influxdb
```

### Docker Compose

```bash
# Set your InfluxDB token
export INFLUXDB_TOKEN=your-influxdb-token

# Run with default settings (TCP, connects to existing InfluxDB)
docker-compose up -d tempest-publisher

# Run full stack with bundled InfluxDB
docker-compose --profile full-stack up -d

# Run with UDP mode
docker-compose --profile udp up -d tempest-publisher-udp
```

### Direct Python

```bash
# Install dependencies
pip install -r requirements.txt

# Run the publisher
python3 main.py \
  --influxdb-url http://localhost:8086 \
  --influxdb-token your-token \
  --influxdb-org home \
  --influxdb-bucket tempest
```

## Usage

### Basic Usage

```bash
# Run with default settings (TCP protocol)
python3 main.py --influxdb-token your-token

# Run with debug output
python3 main.py --influxdb-token your-token --debug

# Use UDP protocol instead of TCP
python3 main.py --influxdb-token your-token --protocol udp

# Use custom TCP port
python3 main.py --influxdb-token your-token --tcp-port 50223

# Set custom publish interval (seconds)
python3 main.py --influxdb-token your-token --publish-interval 30
```

### Docker Usage

```bash
# Basic deployment
docker run --network host \
  -e INFLUXDB_TOKEN=your-token \
  tempest-influxdb

# Full configuration
docker run --network host \
  -e TEMPEST_PROTOCOL=tcp \
  -e TEMPEST_TCP_PORT=50222 \
  -e TEMPEST_PUBLISH_INTERVAL=60 \
  -e TEMPEST_DEBUG=true \
  -e INFLUXDB_URL=http://influxdb:8086 \
  -e INFLUXDB_TOKEN=your-token \
  -e INFLUXDB_ORG=home \
  -e INFLUXDB_BUCKET=tempest \
  -e INFLUXDB_MEASUREMENT=weather \
  tempest-influxdb

# With UDP protocol
docker run --network host \
  -e TEMPEST_PROTOCOL=udp \
  -e INFLUXDB_TOKEN=your-token \
  tempest-influxdb
```

## Configuration

All configuration options can be set via **environment variables** or **command-line arguments**. Command-line arguments take precedence.

### Tempest Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TEMPEST_PROTOCOL` | Protocol: `tcp` or `udp` | `tcp` |
| `TEMPEST_TCP_PORT` | TCP port for messages | `50222` |
| `TEMPEST_UDP_PORT` | UDP port for broadcasts | `50222` |
| `TEMPEST_PUBLISH_INTERVAL` | Publish interval (seconds) | `60` |
| `TEMPEST_DEBUG` | Enable debug output | `false` |
| `TEMPEST_NO_FIREWALL` | Skip firewall warnings | `false` |

### InfluxDB Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `INFLUXDB_URL` | InfluxDB server URL | `http://localhost:8086` |
| `INFLUXDB_TOKEN` | Authentication token | (required) |
| `INFLUXDB_ORG` | Organization name | `home` |
| `INFLUXDB_BUCKET` | Bucket name | `tempest` |
| `INFLUXDB_MEASUREMENT` | Measurement name | `weather` |

### Command Line Arguments

```
Network Options:
  --protocol {tcp,udp}     Protocol to use (default: tcp)
  --tcp-port PORT          TCP port (default: 50222)
  --udp-port PORT          UDP port (default: 50222)
  --publish-interval SECS  Publish interval (default: 60)
  --debug                  Enable debug output
  --no-firewall           Skip firewall warnings

InfluxDB Options:
  --influxdb-url URL       InfluxDB URL (default: http://localhost:8086)
  --influxdb-token TOKEN   InfluxDB token (required)
  --influxdb-org ORG       Organization (default: home)
  --influxdb-bucket BUCKET Bucket name (default: tempest)
  --influxdb-measurement   Measurement name (default: weather)
```

## InfluxDB Setup

### Creating a Bucket and Token

1. Access InfluxDB UI (usually at `http://localhost:8086`)
2. Create a new bucket named `tempest`
3. Create an API token with write access to the bucket
4. Use the token in your configuration

### Example Flux Query

```flux
from(bucket: "tempest")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "weather")
  |> filter(fn: (r) => r.source == "obs_st")
  |> filter(fn: (r) => r._field == "temperature_c" or r._field == "humidity")
```

### Grafana Dashboard

You can visualize the data in Grafana by connecting it to your InfluxDB instance and querying the `tempest` bucket.

## Network Requirements

### Port Access

The publisher requires access to port 50222 (default) to receive Tempest data:

- **TCP Mode (default)**: Listens for incoming TCP connections with length-prefixed JSON messages
- **UDP Mode**: Listens for UDP broadcasts from Tempest stations

### Firewall Configuration

If you encounter connectivity issues:

```bash
# Allow TCP port 50222
sudo iptables -I INPUT -p tcp --dport 50222 -j ACCEPT

# Allow UDP port 50222 (if using UDP mode)
sudo iptables -I INPUT -p udp --dport 50222 -j ACCEPT
```

## Troubleshooting

### No Data Received

1. **Check Network**: Ensure Tempest station and publisher are on same network
2. **Verify Protocol**: Make sure you're using the correct protocol (TCP/UDP)
3. **Firewall Issues**: Check if the port is accessible
4. **Port Conflicts**: Try a different port

### InfluxDB Connection Issues

1. **Check URL**: Verify the InfluxDB URL is correct
2. **Check Token**: Ensure the token has write permissions
3. **Check Bucket**: Verify the bucket exists
4. **Check Network**: Ensure InfluxDB is reachable

### Debug Mode

Enable debug output for detailed information:

```bash
python3 main.py --debug --influxdb-token your-token
```

This shows:
- Listener status
- Received message types
- Parsing information
- Write confirmations

## Message Types

### obs_st (Observation Station)
- Comprehensive weather observations
- Updated every few minutes
- Includes wind, temperature, humidity, pressure, precipitation, lightning

### rapid_wind
- High-frequency wind updates
- Updated every few seconds
- Includes instant wind speed and direction

### hub_status
- Hub system information
- Includes firmware, uptime, signal strength

## Publishing Throttling

The publisher implements throttling to prevent excessive writes:

- **Configurable Interval**: Set via `--publish-interval` (default: 60 seconds)
- **Per-Message Type**: Each message type is throttled independently
- **Latest Data**: The most recent data is always written (not averaged)

## Development

### Building from Source

```bash
git clone <repository>
cd tempest-influxdb
docker build -t tempest-influxdb .
```

### Testing

```bash
# Test with debug output
python3 main.py --debug --influxdb-token your-token

# Test with custom settings
python3 main.py \
  --protocol udp \
  --udp-port 50223 \
  --publish-interval 10 \
  --debug \
  --influxdb-token your-token
```

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request
