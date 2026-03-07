# Tempest InfluxDB TODO

## Current Status: Ready for Testing

The Tempest Weather Station InfluxDB Publisher has been converted from Waggle to direct InfluxDB integration.

## Recent Changes

- Replaced Waggle dependency with direct InfluxDB integration
- Updated all documentation and configuration files
- Removed SAGE/Waggle-specific deployment files

## Completed Tasks

- Removed Waggle/PyWaggle dependency
- Added influxdb-client dependency
- Created InfluxDBWriter class for database operations
- Converted all publish calls to InfluxDB point writes
- Updated Dockerfile to use python:3.11-slim base image
- Added InfluxDB environment variables and CLI arguments
- Updated docker-compose.yml with InfluxDB configuration
- Added optional bundled InfluxDB service in docker-compose
- Updated README.md with InfluxDB usage instructions
- Updated DEVELOPMENT.md for InfluxDB workflow
- Updated check-syntax.sh for influxdb-client imports
- Removed sage.yaml, plugin-tempest.yaml, sage-generated.yaml

## InfluxDB Schema

### Tags
- `sensor`: tempest-weather-station
- `source`: obs_st, rapid_wind, hub_status, status
- `device_sn`: Tempest device serial number
- `hub_sn`: Tempest hub serial number

### Fields (obs_st)
- wind_lull_kt, wind_avg_kt, wind_gust_kt
- wind_direction, wind_sample_interval
- pressure_hpa, pressure_inhg
- temperature_c, temperature_f
- humidity
- illuminance_lux, uv_index, solar_radiation_wm2
- rain_since_report_mm, rain_daily_mm
- lightning_distance_km, lightning_count
- battery_v, report_interval_min

### Fields (rapid_wind)
- wind_instant_kt, wind_direction_instant

### Fields (hub_status)
- hub_uptime_s, hub_rssi, hub_firmware

## Testing Checklist

- [ ] Test connection to InfluxDB
- [ ] Verify data writes with obs_st messages
- [ ] Verify data writes with rapid_wind messages
- [ ] Verify data writes with hub_status messages
- [ ] Test publish interval throttling
- [ ] Test TCP listener
- [ ] Test UDP listener
- [ ] Test Docker container
- [ ] Verify Grafana visualization

## Future Enhancements (Optional)

### Potential Improvements
- [ ] Add data aggregation/averaging option
- [ ] Add Prometheus metrics endpoint
- [ ] Create unit tests for parsers
- [ ] Add integration tests
- [ ] Implement configuration file support (YAML/JSON)
- [ ] Add support for multiple Tempest stations
- [ ] Create Grafana dashboard templates
- [ ] Add data validation and quality checks
- [ ] Add InfluxDB connection retry logic

### Documentation Enhancements
- [ ] Add architecture diagram
- [ ] Create deployment guide for various platforms
- [ ] Add troubleshooting flowchart
- [ ] Add example Flux queries
- [ ] Create Grafana dashboard JSON

## Deployment Notes

- Requires InfluxDB 2.x (not compatible with 1.x)
- INFLUXDB_TOKEN environment variable is required
- Bucket must exist before starting publisher
- Use docker-compose --profile full-stack for bundled InfluxDB
- Default publish interval: 60 seconds
- TCP protocol is default, UDP available with --protocol udp

## Configuration

### Required
- INFLUXDB_TOKEN: Authentication token with write access

### Optional (with defaults)
- INFLUXDB_URL: http://localhost:8086
- INFLUXDB_ORG: home
- INFLUXDB_BUCKET: tempest
- INFLUXDB_MEASUREMENT: weather
- TEMPEST_PROTOCOL: tcp
- TEMPEST_TCP_PORT: 50222
- TEMPEST_UDP_PORT: 50222
- TEMPEST_PUBLISH_INTERVAL: 60
- TEMPEST_DEBUG: false
