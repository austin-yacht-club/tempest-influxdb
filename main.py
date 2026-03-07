#!/usr/bin/env python3

"""
Tempest Weather Station InfluxDB Publisher
==========================================

Receives TCP length-prefixed messages or UDP broadcasts from a local Tempest 
weather station and publishes the data directly to InfluxDB.

Default protocol is TCP with length-prefixed JSON messages for improved reliability.
UDP broadcast mode is also supported for backward compatibility.
"""

import argparse
import logging
import json
import os
import socket
import threading
import time
from datetime import datetime, timezone

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS


# Tempest network configuration
UDP_PORT = 50222
TCP_PORT = 50222
DEFAULT_PROTOCOL = "tcp"

# InfluxDB defaults
DEFAULT_INFLUX_URL = "http://localhost:8086"
DEFAULT_INFLUX_BUCKET = "tempest"
DEFAULT_INFLUX_ORG = "home"
DEFAULT_INFLUX_MEASUREMENT = "weather"

# Global Tempest data storage
tempest_data_lock = threading.Lock()
latest_tempest_raw_by_type = {}
latest_tempest_parsed_by_type = {}

# Global publishing control
last_publish_times = {}
publish_interval = 60


# ---------------- Unit Conversion Functions ----------------
def c_to_f(c): 
    return None if c is None else (c * 9/5) + 32

def mps_to_kt(m): 
    return None if m is None else m * 1.943844

def hpa_to_inhg(h): 
    return None if h is None else h * 0.0295299830714

def mm_to_in(mm): 
    return None if mm is None else mm / 25.4


def get_timestamp(tempest_timestamp=None):
    """
    Get timestamp for InfluxDB.
    
    Args:
        tempest_timestamp: Optional Tempest timestamp (epoch seconds)
                          If None, uses current time
    
    Returns:
        datetime: UTC datetime object
    """
    if tempest_timestamp is not None:
        return datetime.fromtimestamp(tempest_timestamp, tz=timezone.utc)
    return datetime.now(timezone.utc)


# ---------------- Tempest Message Parsers ----------------
PRECIP_TYPES = {
    0: "none",
    1: "rain", 
    2: "hail",
    3: "snow",
}

def parse_obs_st(msg):
    """Parse Tempest device observation messages"""
    obs = msg.get("obs", [[]])[0] if msg.get("obs") else []
    if not obs:
        return {"type": "obs_st", "error": "empty obs"}

    return {
        "timestamp": obs[0],
        "wind": {
            "lull_mps": obs[1], "lull_kt": mps_to_kt(obs[1]),
            "avg_mps": obs[2],  "avg_kt": mps_to_kt(obs[2]),
            "gust_mps": obs[3], "gust_kt": mps_to_kt(obs[3]),
            "direction_deg": obs[4],
            "sample_interval_s": obs[5],
        },
        "pressure": {
            "hpa": obs[6],
            "inHg": hpa_to_inhg(obs[6]),
        },
        "temperature": {
            "c": obs[7],
            "f": c_to_f(obs[7]),
        },
        "humidity_percent": obs[8],
        "light": {
            "illuminance_lux": obs[9],
            "uv_index": obs[10],
            "solar_radiation_wm2": obs[11],
        },
        "rain": {
            "since_report_mm": obs[12],
            "since_report_in": mm_to_in(obs[12]),
            "precipitation_type": PRECIP_TYPES.get(obs[13], "unknown"),
            "local_day_mm": obs[18] if len(obs) > 18 else None,
            "local_day_in": mm_to_in(obs[18]) if len(obs) > 18 else None,
        },
        "lightning": {
            "avg_distance_km": obs[14],
            "strike_count": obs[15],
        },
        "battery_v": obs[16],
        "report_interval_min": obs[17],
        "meta": {
            "device_sn": msg.get("serial_number"),
            "hub_sn": msg.get("hub_sn"),
            "received_at": int(time.time()),
        },
    }

def parse_rapid_wind(msg):
    """Parse rapid wind messages for instant wind readings"""
    ob = msg.get("ob", [])
    if len(ob) < 3:
        return {"type": "rapid_wind", "error": "bad ob"}
    return {
        "timestamp": ob[0],
        "wind": {
            "instant_mps": ob[1],
            "instant_kt": mps_to_kt(ob[1]),
            "direction_deg": ob[2],
        },
        "meta": {
            "device_sn": msg.get("serial_number"),
            "hub_sn": msg.get("hub_sn"),
            "received_at": int(time.time()),
        },
    }

def parse_hub_status(msg):
    """Parse hub status messages"""
    return {
        "firmware": msg.get("firmware_revision"),
        "uptime_s": msg.get("uptime"),
        "rssi": msg.get("rssi"),
        "timestamp": msg.get("time"),
        "meta": {
            "hub_sn": msg.get("serial_number"),
            "received_at": int(time.time()),
        },
    }

# Message type parsers
TEMPEST_PARSERS = {
    "obs_st": parse_obs_st,
    "rapid_wind": parse_rapid_wind,
    "hub_status": parse_hub_status,
}


# ---------------- InfluxDB Writer ----------------
class InfluxDBWriter:
    """Handles writing Tempest data to InfluxDB"""
    
    def __init__(self, url, token, org, bucket, measurement, logger):
        self.url = url
        self.token = token
        self.org = org
        self.bucket = bucket
        self.measurement = measurement
        self.logger = logger
        self.client = None
        self.write_api = None
        self._connect()
    
    def _connect(self):
        """Establish connection to InfluxDB"""
        try:
            self.client = InfluxDBClient(
                url=self.url,
                token=self.token,
                org=self.org
            )
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            self.logger.info(f"Connected to InfluxDB at {self.url}")
            self.logger.info(f"  Organization: {self.org}")
            self.logger.info(f"  Bucket: {self.bucket}")
            self.logger.info(f"  Measurement: {self.measurement}")
        except Exception as e:
            self.logger.error(f"Failed to connect to InfluxDB: {e}")
            raise
    
    def close(self):
        """Close InfluxDB connection"""
        if self.client:
            self.client.close()
            self.logger.info("InfluxDB connection closed")
    
    def write_point(self, tags, fields, timestamp=None):
        """Write a single point to InfluxDB"""
        try:
            point = Point(self.measurement)
            
            for tag_key, tag_value in tags.items():
                if tag_value is not None:
                    point = point.tag(tag_key, str(tag_value))
            
            for field_key, field_value in fields.items():
                if field_value is not None:
                    point = point.field(field_key, field_value)
            
            if timestamp:
                point = point.time(timestamp, WritePrecision.S)
            
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            return True
        except Exception as e:
            self.logger.error(f"Failed to write to InfluxDB: {e}")
            return False
    
    def write_obs_st(self, obs, timestamp):
        """Write observation station data"""
        tags = {
            "sensor": "tempest-weather-station",
            "source": "obs_st",
            "device_sn": obs.get("meta", {}).get("device_sn"),
            "hub_sn": obs.get("meta", {}).get("hub_sn"),
        }
        
        fields = {
            "wind_lull_kt": obs["wind"]["lull_kt"],
            "wind_avg_kt": obs["wind"]["avg_kt"],
            "wind_gust_kt": obs["wind"]["gust_kt"],
            "wind_direction": obs["wind"]["direction_deg"],
            "wind_sample_interval": obs["wind"]["sample_interval_s"],
            "pressure_hpa": obs["pressure"]["hpa"],
            "pressure_inhg": obs["pressure"]["inHg"],
            "temperature_c": obs["temperature"]["c"],
            "temperature_f": obs["temperature"]["f"],
            "humidity": obs["humidity_percent"],
            "illuminance_lux": obs["light"]["illuminance_lux"],
            "uv_index": obs["light"]["uv_index"],
            "solar_radiation_wm2": obs["light"]["solar_radiation_wm2"],
            "rain_since_report_mm": obs["rain"]["since_report_mm"],
            "rain_daily_mm": obs["rain"]["local_day_mm"],
            "lightning_distance_km": obs["lightning"]["avg_distance_km"],
            "lightning_count": obs["lightning"]["strike_count"],
            "battery_v": obs["battery_v"],
            "report_interval_min": obs["report_interval_min"],
        }
        
        # Filter out None values
        fields = {k: v for k, v in fields.items() if v is not None}
        
        return self.write_point(tags, fields, timestamp)
    
    def write_rapid_wind(self, data, timestamp):
        """Write rapid wind data"""
        tags = {
            "sensor": "tempest-weather-station",
            "source": "rapid_wind",
            "device_sn": data.get("meta", {}).get("device_sn"),
            "hub_sn": data.get("meta", {}).get("hub_sn"),
        }
        
        fields = {
            "wind_instant_kt": data["wind"]["instant_kt"],
            "wind_direction_instant": data["wind"]["direction_deg"],
        }
        
        fields = {k: v for k, v in fields.items() if v is not None}
        
        return self.write_point(tags, fields, timestamp)
    
    def write_hub_status(self, data, timestamp):
        """Write hub status data"""
        tags = {
            "sensor": "tempest-weather-station",
            "source": "hub_status",
            "hub_sn": data.get("meta", {}).get("hub_sn"),
        }
        
        fields = {
            "hub_uptime_s": data["uptime_s"],
            "hub_rssi": data["rssi"],
        }
        
        if data.get("firmware"):
            fields["hub_firmware"] = data["firmware"]
        
        fields = {k: v for k, v in fields.items() if v is not None}
        
        return self.write_point(tags, fields, timestamp)
    
    def write_status(self, status, error=None):
        """Write plugin status"""
        tags = {
            "sensor": "tempest-weather-station",
            "source": "status",
        }
        
        fields = {
            "status": status,
        }
        
        if error:
            fields["error"] = str(error)
        
        return self.write_point(tags, fields)


# ---------------- UDP Listener ----------------
def tempest_udp_listener(logger, publish_callback, udp_port=UDP_PORT):
    """UDP listener thread for Tempest broadcasts"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("0.0.0.0", udp_port))
        
        logger.info(f"Tempest UDP listener started on port {udp_port}")
        
        while True:
            try:
                data, addr = sock.recvfrom(65535)
                msg = json.loads(data.decode("utf-8"))
                
                msg_type = msg.get("type", "unknown")
                
                logger.debug(f"Received {msg_type} message from {addr[0]}")
                
                with tempest_data_lock:
                    latest_tempest_raw_by_type[msg_type] = msg
                    
                    parser = TEMPEST_PARSERS.get(msg_type)
                    if parser:
                        try:
                            parsed_data = parser(msg)
                            latest_tempest_parsed_by_type[msg_type] = {
                                "type": msg_type,
                                "data": parsed_data
                            }
                            publish_callback(parsed_data, msg_type)
                        except Exception as e:
                            logger.error(f"Error parsing {msg_type} message: {e}")
                    else:
                        if msg_type in latest_tempest_parsed_by_type:
                            del latest_tempest_parsed_by_type[msg_type]
                        logger.debug(f"Received unknown message type: {msg_type}")
                            
            except json.JSONDecodeError:
                continue
            except Exception as e:
                logger.error(f"UDP listener error: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Failed to start Tempest UDP listener: {e}")


# ---------------- TCP Listener ----------------
def tempest_tcp_listener(logger, publish_callback, tcp_port=TCP_PORT):
    """TCP listener thread for Tempest length-prefixed messages"""
    try:
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind(("0.0.0.0", tcp_port))
        server_sock.listen(5)
        
        logger.info(f"Tempest TCP listener started on port {tcp_port}")
        logger.info("Waiting for TCP connections with length-prefixed JSON messages...")
        
        while True:
            try:
                client_sock, addr = server_sock.accept()
                logger.info(f"Accepted TCP connection from {addr[0]}:{addr[1]}")
                
                client_sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                client_sock.settimeout(None)
                
                client_thread = threading.Thread(
                    target=handle_tcp_client,
                    args=(client_sock, addr, logger, publish_callback),
                    daemon=True
                )
                client_thread.start()
                
            except Exception as e:
                logger.error(f"TCP listener error: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Failed to start Tempest TCP listener: {e}")


def handle_tcp_client(client_sock, addr, logger, publish_callback):
    """Handle messages from a TCP client connection"""
    logger.info(f"Starting persistent TCP connection handler for {addr[0]}:{addr[1]}")
    
    try:
        while True:
            try:
                length_data = recv_exactly(client_sock, 4, logger, addr)
                if not length_data:
                    logger.info(f"Connection closed by {addr[0]}:{addr[1]}")
                    break
                    
                msg_length = int.from_bytes(length_data, byteorder='big')
                
                if msg_length <= 0 or msg_length > 65535:
                    logger.warning(f"Invalid message length: {msg_length} from {addr[0]} - skipping message")
                    continue
                
                msg_data = recv_exactly(client_sock, msg_length, logger, addr)
                if not msg_data:
                    logger.info(f"Connection closed by {addr[0]}:{addr[1]} while reading message")
                    break
                    
                try:
                    msg = json.loads(msg_data.decode("utf-8"))
                    msg_type = msg.get("type", "unknown")
                    
                    logger.debug(f"Received {msg_type} TCP message from {addr[0]} ({msg_length} bytes)")
                    
                    with tempest_data_lock:
                        latest_tempest_raw_by_type[msg_type] = msg
                        
                        parser = TEMPEST_PARSERS.get(msg_type)
                        if parser:
                            try:
                                parsed_data = parser(msg)
                                latest_tempest_parsed_by_type[msg_type] = {
                                    "type": msg_type,
                                    "data": parsed_data
                                }
                                publish_callback(parsed_data, msg_type)
                            except Exception as e:
                                logger.error(f"Error parsing {msg_type} message: {e}")
                        else:
                            if msg_type in latest_tempest_parsed_by_type:
                                del latest_tempest_parsed_by_type[msg_type]
                            logger.debug(f"Received unknown message type: {msg_type}")
                            
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON from {addr[0]}: {e} - skipping message")
                    continue
                except Exception as e:
                    logger.error(f"Error processing TCP message from {addr[0]}: {e} - skipping message")
                    continue
                    
            except socket.error as e:
                logger.info(f"TCP connection to {addr[0]}:{addr[1]} lost: {e}")
                break
            except Exception as e:
                logger.error(f"Unexpected error in TCP client handler for {addr[0]}: {e}")
                continue
                
    except Exception as e:
        logger.info(f"TCP client {addr[0]}:{addr[1]} disconnected: {e}")
    finally:
        try:
            client_sock.close()
            logger.info(f"Closed TCP connection to {addr[0]}:{addr[1]}")
        except:
            pass


def recv_exactly(sock, num_bytes, logger, addr=None):
    """Receive exactly num_bytes from socket"""
    data = b""
    addr_str = f" from {addr[0]}" if addr else ""
    
    while len(data) < num_bytes:
        try:
            chunk = sock.recv(num_bytes - len(data))
            if not chunk:
                logger.debug(f"Connection closed{addr_str} while receiving {num_bytes} bytes")
                return None
            data += chunk
        except socket.timeout:
            logger.warning(f"TCP receive timeout{addr_str}")
            return None
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError) as e:
            logger.info(f"TCP connection reset{addr_str}: {e}")
            return None
        except Exception as e:
            logger.error(f"TCP receive error{addr_str}: {e}")
            return None
    return data


# ---------------- Command Line Arguments ----------------
def parse_args():
    """Parse command line arguments with environment variable support"""
    def env_bool(env_var):
        val = os.getenv(env_var, "").lower()
        return val in ("true", "1", "yes", "on")
    
    # Network defaults
    default_protocol = os.getenv("TEMPEST_PROTOCOL", DEFAULT_PROTOCOL).lower()
    default_tcp_port = int(os.getenv("TEMPEST_TCP_PORT", TCP_PORT))
    default_udp_port = int(os.getenv("TEMPEST_UDP_PORT", UDP_PORT))
    default_debug = env_bool("TEMPEST_DEBUG")
    default_publish_interval = int(os.getenv("TEMPEST_PUBLISH_INTERVAL", "60"))
    default_no_firewall = env_bool("TEMPEST_NO_FIREWALL")
    
    # InfluxDB defaults
    default_influx_url = os.getenv("INFLUXDB_URL", DEFAULT_INFLUX_URL)
    default_influx_token = os.getenv("INFLUXDB_TOKEN", "")
    default_influx_org = os.getenv("INFLUXDB_ORG", DEFAULT_INFLUX_ORG)
    default_influx_bucket = os.getenv("INFLUXDB_BUCKET", DEFAULT_INFLUX_BUCKET)
    default_influx_measurement = os.getenv("INFLUXDB_MEASUREMENT", DEFAULT_INFLUX_MEASUREMENT)
    
    parser = argparse.ArgumentParser(
        description="Tempest Weather Station InfluxDB Publisher - sends Tempest data to InfluxDB",
        epilog="All arguments can be set via environment variables: TEMPEST_*, INFLUXDB_*"
    )
    
    # Network arguments
    parser.add_argument(
        "--protocol",
        choices=["tcp", "udp"],
        default=default_protocol,
        help=f"Protocol to use for receiving data (default: {DEFAULT_PROTOCOL})"
    )
    parser.add_argument(
        "--tcp-port", 
        type=int,
        default=default_tcp_port,
        help=f"TCP port to listen on (default: {TCP_PORT})"
    )
    parser.add_argument(
        "--udp-port", 
        type=int,
        default=default_udp_port, 
        help=f"UDP port to listen for broadcasts (default: {UDP_PORT})"
    )
    parser.add_argument(
        "--debug", 
        action="store_true", 
        default=default_debug,
        help="Enable debug output"
    )
    parser.add_argument(
        "--publish-interval", 
        type=int, 
        default=default_publish_interval, 
        help="Minimum interval between data publications in seconds (default: 60)"
    )
    parser.add_argument(
        "--no-firewall", 
        action="store_true",
        default=default_no_firewall, 
        help="Skip firewall setup warnings"
    )
    
    # InfluxDB arguments
    parser.add_argument(
        "--influxdb-url",
        default=default_influx_url,
        help=f"InfluxDB URL (default: {DEFAULT_INFLUX_URL})"
    )
    parser.add_argument(
        "--influxdb-token",
        default=default_influx_token,
        help="InfluxDB authentication token (required)"
    )
    parser.add_argument(
        "--influxdb-org",
        default=default_influx_org,
        help=f"InfluxDB organization (default: {DEFAULT_INFLUX_ORG})"
    )
    parser.add_argument(
        "--influxdb-bucket",
        default=default_influx_bucket,
        help=f"InfluxDB bucket (default: {DEFAULT_INFLUX_BUCKET})"
    )
    parser.add_argument(
        "--influxdb-measurement",
        default=default_influx_measurement,
        help=f"InfluxDB measurement name (default: {DEFAULT_INFLUX_MEASUREMENT})"
    )
    
    return parser.parse_args()


# ---------------- Main Function ----------------
def main():
    """Main function"""
    global publish_interval
    
    args = parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    publish_interval = args.publish_interval
    
    logger.info("Starting Tempest Weather Station InfluxDB Publisher")
    logger.info("=" * 60)
    
    # Validate InfluxDB token
    if not args.influxdb_token:
        logger.error("InfluxDB token is required. Set INFLUXDB_TOKEN or use --influxdb-token")
        return 1
    
    # Show configuration
    logger.info(f"Protocol: {args.protocol.upper()}")
    if args.protocol == "tcp":
        logger.info(f"TCP Port: {args.tcp_port}")
    else:
        logger.info(f"UDP Port: {args.udp_port}")
    logger.info(f"Publish Interval: {args.publish_interval} seconds")
    logger.info(f"Debug Mode: {args.debug}")
    logger.info("")
    logger.info("InfluxDB Configuration:")
    logger.info(f"  URL: {args.influxdb_url}")
    logger.info(f"  Organization: {args.influxdb_org}")
    logger.info(f"  Bucket: {args.influxdb_bucket}")
    logger.info(f"  Measurement: {args.influxdb_measurement}")
    logger.info("")
    
    # Check port accessibility
    if not args.no_firewall:
        port_to_check = args.tcp_port if args.protocol == "tcp" else args.udp_port
        logger.info(f"Checking {args.protocol.upper()} port accessibility...")
        try:
            if args.protocol == "tcp":
                test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            else:
                test_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            test_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            test_sock.bind(("0.0.0.0", port_to_check))
            test_sock.close()
            logger.info(f"{args.protocol.upper()} port {port_to_check} is accessible")
        except Exception as e:
            logger.warning(f"{args.protocol.upper()} port {port_to_check} binding failed: {e}")
    
    # Initialize InfluxDB writer
    try:
        influx_writer = InfluxDBWriter(
            url=args.influxdb_url,
            token=args.influxdb_token,
            org=args.influxdb_org,
            bucket=args.influxdb_bucket,
            measurement=args.influxdb_measurement,
            logger=logger
        )
    except Exception as e:
        logger.error(f"Failed to initialize InfluxDB writer: {e}")
        return 1
    
    # Define publishing function
    def publish_tempest_data(parsed_data, msg_type, force=False):
        """Publish Tempest data to InfluxDB"""
        global last_publish_times, publish_interval
        
        if not force:
            current_time = time.time()
            last_publish = last_publish_times.get(msg_type, 0)
            time_elapsed = current_time - last_publish
            
            if time_elapsed < publish_interval:
                logger.debug(f"Skipping {msg_type} publish - only {time_elapsed:.1f}s elapsed (need {publish_interval}s)")
                return
            
            last_publish_times[msg_type] = current_time
        
        try:
            if msg_type == "obs_st" and "error" not in parsed_data:
                obs = parsed_data
                timestamp = get_timestamp(obs.get("timestamp"))
                
                if influx_writer.write_obs_st(obs, timestamp):
                    logger.info(f"Published obs_st: Wind {obs['wind']['avg_kt']:.1f} kt @ {obs['wind']['direction_deg']:.0f} deg, "
                               f"Temp {obs['temperature']['c']:.1f} C, RH {obs['humidity_percent']:.0f}%")
                
            elif msg_type == "rapid_wind" and "error" not in parsed_data:
                wind = parsed_data["wind"]
                timestamp = get_timestamp(parsed_data.get("timestamp"))
                
                if influx_writer.write_rapid_wind(parsed_data, timestamp):
                    logger.info(f"Published rapid_wind: {wind['instant_kt']:.1f} kt @ {wind['direction_deg']:.0f} deg")
                
            elif msg_type == "hub_status" and "error" not in parsed_data:
                timestamp = get_timestamp(parsed_data.get("timestamp"))
                
                if influx_writer.write_hub_status(parsed_data, timestamp):
                    logger.info(f"Published hub_status: firmware={parsed_data['firmware']}, "
                               f"uptime={parsed_data['uptime_s']}s, RSSI={parsed_data['rssi']}dBm")
                
        except Exception as e:
            logger.error(f"Error publishing Tempest data: {e}")
            influx_writer.write_status(0, error=str(e))
    
    # Start appropriate listener thread
    if args.protocol == "tcp":
        logger.info("Starting Tempest TCP listener thread...")
        listener_thread = threading.Thread(
            target=tempest_tcp_listener, 
            args=(logger, publish_tempest_data, args.tcp_port),
            daemon=True
        )
        wait_msg = "Waiting for Tempest TCP connections..."
    else:
        logger.info("Starting Tempest UDP listener thread...")
        listener_thread = threading.Thread(
            target=tempest_udp_listener, 
            args=(logger, publish_tempest_data, args.udp_port),
            daemon=True
        )
        wait_msg = "Waiting for Tempest UDP broadcasts..."
    
    listener_thread.start()
    
    logger.info(wait_msg)
    time.sleep(5)
    
    with tempest_data_lock:
        if latest_tempest_raw_by_type:
            logger.info(f"Tempest station detected! Received {len(latest_tempest_raw_by_type)} message types:")
            for msg_type in latest_tempest_raw_by_type.keys():
                logger.info(f"   - {msg_type}")
        else:
            logger.warning("No Tempest data received yet")
            logger.info("Troubleshooting:")
            if args.protocol == "tcp":
                logger.info("   1. Check that Tempest hub is configured to send TCP data")
                logger.info(f"   2. Check firewall settings for TCP port {args.tcp_port}")
            else:
                logger.info("   1. Check that Tempest hub is on the same network")
                logger.info(f"   2. Check firewall settings for UDP port {args.udp_port}")
    
    logger.info("")
    logger.info("Tempest InfluxDB publisher is running")
    logger.info("Press Ctrl+C to stop")
    logger.info("")
    
    try:
        while True:
            time.sleep(60)
            
            with tempest_data_lock:
                if latest_tempest_raw_by_type:
                    logger.info(f"Status: Active, {len(latest_tempest_raw_by_type)} message types received")
                else:
                    logger.warning("Status: No data received from Tempest station")
                    
    except KeyboardInterrupt:
        logger.info("Tempest publisher stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise
    finally:
        logger.info("Cleaning up...")
        influx_writer.write_status(0)
        influx_writer.close()
    
    return 0


if __name__ == "__main__":
    exit(main())
