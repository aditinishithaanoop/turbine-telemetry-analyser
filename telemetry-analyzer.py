"""
Turbine Telemetry Anomaly Detector
- Reads teemetry_data.csv and flags turbines requiring urgent maintenance
- Anomaly rules:
    = Rule 1: Avg temperature across readings > 85.0 °C
    = Rule 2: Any vibration reading > 15.0 mm/s (spikes)
    
- A sample of telemetry_data.csv has been used. To use your own data,
  place it in the same folder and pass it via the --input flag
  
- Usage:
    python telemetry_analyzer.py [--input PATH] [--output PATH] [--format csv|json]
    
- Exit codes:
    0 - successful run, no anomalies found.
    1 - turbines flagged (anomalies found)
    2 - input file not found or unreadable
    3 - input file malformed/ missing required columns
"""

import argparse
import json
import logging 
import os
import sys
from datetime import datetime, timezone

import pandas as pd

TEMP_THRESHOLD = 85.0
VIB_THRESHOLD = 15.0

COLS_REQUIRED = {"turbine_id", "temperature_c", "vibration_mm_s"}

# A basic logger 
logging.basicConfig(
    level= logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt= "%Y-%m-%dT%H:%M:%SZ",
    handlers = [logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

# Load and validate csv data
def get_csv(path: str) -> pd.DataFrame:
    
    if not os.path.isfile(path):
        log.error("Input file not found: %s", path)
        sys.exit(2)
        
    try:
        df = pd.read_csv(path)
    except Exception as exc:
        log.error("failed to read csv: %s", exc)
        sys.exit(2)
        
    missing = COLS_REQUIRED - set(df.columns)
    if missing:
        log.error("Required columns missing: %s", missing)
        sys.exit(3)
        
    # Numeric values only - invalid values become NaN
    for col in ("temperature_c", "vibration_mm_s"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
        
    null_counts = df[["temperature_c", "vibration_mm_s"]].isnull().sum()
    if null_counts.any():
        log.warning("Non-numeric values found - temperature_c: %d,vibration_mm_s: %d",
                    null_counts["temperature_c"], 
                    null_counts["vibration_mm_s"])
        df = df.dropna(subset=["temperature_c", "vibration_mm_s"])
    return df

def analyse(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    
    # Returns 2 DataFrames:
    # per_turbine - 1 row per turbine with calculated metrics
    # anomalies - subset of per_turbine that breaches at least 1 rule
    
    per_turbine = (
        df.groupby("turbine_id")
        .agg(
            readings = ("temperature_c", "count"),
            avg_temp = ("temperature_c", "mean"),
            max_temp = ("temperature_c", "max"),
            max_vib = ("vibration_mm_s", "max"),
            vib_spike_count = ("vibration_mm_s", lambda x: (x>VIB_THRESHOLD).sum()),           
        )
        .round(2)
        .reset_index()
    )
    
    per_turbine["rule_temp_breach"] = per_turbine["avg_temp"] > TEMP_THRESHOLD
    per_turbine["rule_vib_breach"] = per_turbine["vib_spike_count"] > 0
    
    per_turbine["urgent_maintenance"] = ( per_turbine["rule_temp_breach"] | 
                                         per_turbine["rule_vib_breach"] )
    anomalies = per_turbine[per_turbine["urgent_maintenance"]].copy()
    return per_turbine, anomalies

def print_report(per_turbine: pd.DataFrame, anomalies: pd.DataFrame) -> None:
    # Print a readable summary 
    separator = "-" * 62

    print(f"\n{separator}")
    print("TURBINE ANOMALY REPORT")
    print(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"Thresholds: \n Avg Temp > {TEMP_THRESHOLD}°C \n Vib spike > {VIB_THRESHOLD} mm/s")
    print(separator)
    
    print(f"\n{'TURBINE':<10} {'AVG TEMP':>11} {'MAX VIB':>11} {'SPIKES':>10}  RULES TRIGGERED")
    for _, row in per_turbine.sort_values("turbine_id").iterrows():
        rules = []
        if row["rule_temp_breach"]:
            rules.append(f"Avg temp above threshold")
        if row["rule_vib_breach"]:
            rules.append(f"vibrations spiked above threshold")
            
        rule_str = ", ".join(rules) if rules else "-"
        print(
            f"{row['turbine_id']:<10} {row['avg_temp']:>8.2f}°C"
            f"  {row['max_vib']:>7.1f} mm/s"
            f" {row['vib_spike_count']:>7}     {rule_str}"
        )
        
    print(f"\n{separator}")
    if anomalies.empty:
        print("No turbines require urgent maintenance.")
    else:
        print(f"URGENT MAINTENANCE REQUIRED - {len(anomalies)} turbine(s):")
        for tid in sorted(anomalies["turbine_id"]):
            print(f" - {tid}")
    print(f"{separator}\n")
        
def write_output(per_turbine: pd.DataFrame, anomalies: pd.DataFrame, path: str, fmt: str) -> None:
    # Write metrics and flagged IDs to a file
    
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    
    if fmt == "json":
        content = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "thresholds": {
                "avg_temp_c": TEMP_THRESHOLD,
                "vib_mm_s": VIB_THRESHOLD,
            },
            "turbines":per_turbine.to_dict(orient="records"),
            "flagged_turbine_ids": sorted(anomalies["turbine_id"].tolist()),
            "urgent_maintenance_required": not anomalies.empty,
        }
        with open(path, "w") as fh:
            json.dump(content, fh, indent = 2, default = str)
    else:
        per_turbine.to_csv(path, index = False)
        
    log.info("Report written to: %s", path)
    
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description = "Analyse turbine telemetry and flag anomalies"
    )
    parser.add_argument(
        "--input", "-i",
        default = os.environ.get("TELEMETRY_INPUT", "telemetry_data.csv"),
        help = "Path to the input csv (default: telemetry_data.csv or $TELEMETRY_INPUT)",
    )
    parser.add_argument(
        "--output", "-o",
        default = os.environ.get("TELEMETRY_OUTPUT", ""),
        help = "Optional path to write results file ($TELEMETRY_OUTPUT)",
    )
    parser.add_argument(
        "--format", "-f",
        choices=["csv", "json"],
        default = os.environ.get("TELEMETRY_FORMAT", "json"),
        help = "Output file format: csv or json (default: json)",
    )
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    log.info("Loading telemetry data from: %s", args.input)
    df = get_csv(args.input)
    log.info("Loaded %d readings across %d turbines", len(df), df["turbine_id"].nunique())
    
    per_turbine, anomalies = analyse(df)
    print_report(per_turbine, anomalies)
    
    if args.output:
        write_output(per_turbine, anomalies, args.output, args.format)
        
    sys.exit(1 if not anomalies.empty else 0)
    
if __name__ == "__main__":
    main()