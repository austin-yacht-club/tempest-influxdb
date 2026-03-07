# Tempest InfluxDB Change Log

## 2026-03-07 - Major Refactor: Replace Waggle with Direct InfluxDB

### Breaking Change: Remove Waggle Dependency, Add Direct InfluxDB Support

**What was changed**:
- Completely removed Waggle/PyWaggle dependency
- Added direct InfluxDB 2.x integration using `influxdb-client`
- Removed all SAGE/Waggle-specific deployment configurations
- Updated all documentation for InfluxDB usage

**Technical Details**:

**Code Changes**:
- Replaced `from waggle.plugin import Plugin` with `influxdb_client` imports
- Created new `InfluxDBWriter` class for managing InfluxDB connections
- Replaced all `plugin.publish()` calls with InfluxDB point writes
- Changed timestamp handling from nanoseconds to datetime objects
- Added InfluxDB connection configuration (URL, token, org, bucket, measurement)

**Dependency Changes**:
- Removed: `pywaggle>=0.50.0`
- Added: `influxdb-client>=1.36.0`

**Configuration Changes**:
- Added new environment variables: `INFLUXDB_URL`, `INFLUXDB_TOKEN`, `INFLUXDB_ORG`, `INFLUXDB_BUCKET`, `INFLUXDB_MEASUREMENT`
- Added corresponding command-line arguments
- `INFLUXDB_TOKEN` is now required

**Files Modified**:
- `main.py` - Complete rewrite of publishing logic
- `requirements.txt` - Changed dependency from pywaggle to influxdb-client
- `Dockerfile` - Changed base image from `waggle/plugin-base:1.1.1-base` to `python:3.11-slim`
- `docker-compose.yml` - Added InfluxDB configuration, optional bundled InfluxDB service
- `README.md` - Comprehensive rewrite for InfluxDB usage
- `DEVELOPMENT.md` - Updated for InfluxDB workflow
- `check-syntax.sh` - Updated import checks for influxdb-client

**Files Removed**:
- `sage.yaml` - SAGE metadata (no longer applicable)
- `plugin-tempest.yaml` - sesctl deployment config (no longer applicable)
- `sage-generated.yaml` - Generated plugin metadata (no longer applicable)

**InfluxDB Schema**:
Data is now written to a single measurement with tags and fields:
- Tags: `sensor`, `source`, `device_sn`, `hub_sn`
- Fields: All weather data as numeric fields (temperature_c, wind_avg_kt, humidity, etc.)

**Benefits**:
- Direct database writes without middleware
- Simpler deployment (no Waggle infrastructure required)
- Standard InfluxDB tooling (Grafana, Chronograf, etc.)
- Portable to any environment with InfluxDB

**Migration Notes**:
- Existing Waggle deployments will need to be migrated
- InfluxDB 2.x is required (not compatible with InfluxDB 1.x)
- An InfluxDB token with write permissions is required
- The bucket must exist before running the publisher

---

## Previous Changes (Waggle Era)

Historical changes from the Waggle-based version are preserved below for reference.
These changes applied to the previous Waggle-based implementation.

### 2025-10-12 - TCP Protocol Support
- Added TCP protocol support with length-prefixed messages as default
- UDP mode available for backward compatibility

### 2025-10-12 - Multi-Architecture Docker Builds
- Added GitHub Actions workflow for amd64/arm64 builds

### 2025-10-11 - Initial Implementation
- Implemented Tempest UDP listener
- Added Waggle publishing with comprehensive metadata
- Implemented publish interval throttling
