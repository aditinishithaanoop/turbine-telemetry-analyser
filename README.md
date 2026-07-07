# Turbine Telemetry Analyzer

Analyze IoT telemetry data from wind turbines and automatically detect anomalies requiring urgent maintenance.

## Overview

**Turbine Telemetry Analyzer** reads CSV data containing temperature and vibration readings from wind turbines and applies intelligent anomaly detection rules to flag turbines that require maintenance. The tool processes telemetry data, calculates key metrics, and outputs detailed reports in multiple formats.

### Key Features

- ✅ **Automated Anomaly Detection** – Flags turbines exceeding temperature and vibration thresholds
- ✅ **Multiple Output Formats** – Generate reports in CSV or JSON
- ✅ **Docker Ready** – Containerized for easy deployment in cloud environments
- ✅ **Configurable Thresholds** – Customize detection rules for your infrastructure
- ✅ **Comprehensive Logging** – Track processing steps and identify data quality issues
- ✅ **Exit Codes** – Scriptable integration with CI/CD and monitoring systems

## Requirements

### Input Data Format

Your CSV file must contain the following columns:

| Column | Type | Description |
|--------|------|-------------|
| `turbine_id` | string | Unique identifier for the turbine |
| `temperature_c` | float | Temperature reading in Celsius |
| `vibration_mm_s` | float | Vibration reading in mm/s |

Additional columns are allowed and will be ignored.

### Detection Rules

A turbine is flagged for urgent maintenance if **either** of these conditions is met:

- **Rule 1 (Temperature)**: Average temperature across all readings > **85.0°C**
- **Rule 2 (Vibration)**: Any single vibration reading > **15.0 mm/s** (spike detected)

## Installation

### Prerequisites

- Python 3.10+
- `pandas==2.2.3`

### Local Setup

1. Clone the repository:
```bash
git clone https://github.com/aditinishithaanoop/turbine-telemetry-analyser.git
cd turbine-telemetry-analyser
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Command Line

```bash
python telemetry-analyzer.py [--input PATH] [--output PATH] [--format csv|json]
```

#### Options

- `--input, -i` – Path to input CSV file (default: `telemetry_data.csv` or `$TELEMETRY_INPUT`)
- `--output, -o` – Optional path to write results file (default: none, or `$TELEMETRY_OUTPUT`)
- `--format, -f` – Output file format: `csv` or `json` (default: `json`)

#### Examples

**Analyze default data and print report:**
```bash
python telemetry-analyzer.py
```

**Analyze custom data and save JSON report:**
```bash
python telemetry-analyzer.py --input data/turbines.csv --output results/report.json --format json
```

**Analyze custom data and save CSV report:**
```bash
python telemetry-analyzer.py --input data/turbines.csv --output results/metrics.csv --format csv
```

**Use environment variables:**
```bash
export TELEMETRY_INPUT=data/my_turbines.csv
export TELEMETRY_OUTPUT=results/report.json
export TELEMETRY_FORMAT=json
python telemetry-analyzer.py
```

### Exit Codes

The script returns exit codes for integration with monitoring and CI/CD systems:

| Exit Code | Meaning |
|-----------|---------|
| `0` | ✅ Successful run, no anomalies found |
| `1` | ⚠️ Turbines flagged (anomalies detected, maintenance required) |
| `2` | ❌ Input file not found or unreadable |
| `3` | ❌ Input file malformed or missing required columns |

### Docker

#### Build the Image

```bash
docker build -t telemetry-analyzer .
```

#### Run with Default Settings

```bash
docker run --rm \
  -v /path/to/data:/data \
  telemetry-analyzer
```

#### Run with Custom Configuration

```bash
docker run --rm \
  -v /path/to/data:/data \
  -e TELEMETRY_INPUT=/data/my_file.csv \
  -e TELEMETRY_OUTPUT=/data/report.json \
  -e TELEMETRY_FORMAT=json \
  telemetry-analyzer
```

#### Docker Environment Variables

- `TELEMETRY_INPUT` – Path to CSV file inside container (default: `/data/telemetry_data.csv`)
- `TELEMETRY_OUTPUT` – Path to write results (leave empty to skip, default: empty)
- `TELEMETRY_FORMAT` – Output format: `json` or `csv` (default: `json`)

## Output

### Console Report

The tool prints a formatted table summarizing all turbines:

```
--------------------------------------------------------------
TURBINE ANOMALY REPORT
Generated: 2026-07-07 14:30:45 UTC
Thresholds:
  Avg Temp > 85.0°C
  Vib spike > 15.0 mm/s
--------------------------------------------------------------

TURBINE     AVG TEMP      MAX VIB  SPIKES  RULES TRIGGERED
T001          82.50°C      12.3 mm/s       -
T002          88.75°C      18.5 mm/s       Avg temp above threshold, vibrations spiked above threshold
T003          75.20°C       8.1 mm/s       -

--------------------------------------------------------------
URGENT MAINTENANCE REQUIRED - 1 turbine(s):
 - T002
--------------------------------------------------------------
```

### JSON Output Format

```json
{
  "generated_at": "2026-07-07T14:30:45.123456+00:00",
  "thresholds": {
    "avg_temp_c": 85.0,
    "vib_mm_s": 15.0
  },
  "turbines": [
    {
      "turbine_id": "T001",
      "readings": 120,
      "avg_temp": 82.50,
      "max_temp": 89.20,
      "max_vib": 12.3,
      "vib_spike_count": 0,
      "rule_temp_breach": false,
      "rule_vib_breach": false,
      "urgent_maintenance": false
    }
  ],
  "flagged_turbine_ids": ["T002"],
  "urgent_maintenance_required": true
}
```

### CSV Output Format

When using `--format csv`, a CSV file is written containing one row per turbine with all calculated metrics.

## Data Processing

1. **Load & Validate** – Reads CSV, checks for required columns
2. **Clean Data** – Converts values to numeric, removes invalid/missing data rows
3. **Group by Turbine** – Aggregates readings by `turbine_id`
4. **Calculate Metrics** – Computes averages, max values, spike counts
5. **Apply Rules** – Evaluates each detection rule
6. **Flag Anomalies** – Identifies turbines requiring maintenance
7. **Generate Report** – Outputs results in specified format

## Development

### Project Structure

```
.
├── telemetry-analyzer.py    # Main analyzer script
├── requirements.txt         # Python dependencies
├── Dockerfile              # Container configuration
├── telemetry_data.csv      # Sample data
└── README.md              # This file
```

### Technologies

- **Python 3.12** – Primary language
- **Pandas 2.2.3** – Data processing and aggregation
- **Docker** – Containerization for cloud deployment

## Troubleshooting

### File Not Found (Exit Code 2)

**Error:** `Input file not found: path/to/file.csv`

**Solution:** Verify the file path is correct and accessible:
```bash
ls -la path/to/file.csv
python telemetry-analyzer.py --input path/to/file.csv
```

### Missing Columns (Exit Code 3)

**Error:** `Required columns missing: {'temperature_c', 'vibration_mm_s'}`

**Solution:** Verify your CSV has the required columns with exact names (case-sensitive):
```bash
head -1 your_file.csv
```

### Non-Numeric Data

**Warning:** `Non-numeric values found - temperature_c: 5, vibration_mm_s: 2`

**Solution:** Clean your data. Invalid values are automatically coerced to NaN and those rows are removed.

## Example Workflow

```bash
# 1. Prepare your data
cp your_turbine_data.csv telemetry_data.csv

# 2. Run analysis
python telemetry-analyzer.py --output results/report.json

# 3. Check exit code
echo $?  # 0=OK, 1=anomalies found

# 4. Review report
cat results/report.json | jq .flagged_turbine_ids
```

## License

This project is provided as-is. See LICENSE file for details.

## Support

For issues, questions, or suggestions, please open an issue on GitHub.
