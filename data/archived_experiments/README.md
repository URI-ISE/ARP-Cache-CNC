# Archived Experimental Data

This directory contains historical experimental data from the Manufacturing Systems Security research project.

## Data Organization

### Experiment Files
- `experiment_YYYYMMDD_HHMMSS.json` - Complete experiment records with configuration and results
- `experiment_YYYYMMDD_HHMMSS.csv` - Tabular data for statistical analysis

### Attack Data Files
- `attack_data_YYYYMMDD_HHMMSS.json` - Detailed attack execution logs
- `attack_stats_YYYYMMDD_HHMMSS.json` - Statistical summaries of attack outcomes

### Attack Command Files
- `attack_commands_YYYYMMDD_HHMMSS.csv` - G-code command modifications during attacks

## Experiment Timeline

### September 2025 Experiments
The initial series of experiments validated the ARP poisoning infrastructure and demonstrated successful G-code MITM attacks against GRBL CNC systems.

**Key Findings:**
- 100% attack success rate without defenses
- 0% detection rate (no defenses active)
- All modified commands accepted by GRBL controller
- Confirmed physical machine state changes

**Attack Types Validated:**
1. Calibration drift attacks (cumulative position errors)
2. Power reduction attacks (50% power modification)
3. Command injection attacks (Z-axis movement injection)

### Experiment Configurations

**Network Setup:**
- CNC Device: GRBL Controller at 192.168.0.170:8080
- Controller: Mac at 10.211.55.2
- Attack VM: Ubuntu at 10.211.55.3
- Proxy Port: 8888
- Network Mode: Parallels Shared (NAT)

## Data Format Specifications

### JSON Experiment Files
```json
{
  "experiment_id": "20250915_095416",
  "configuration": {
    "cnc_ip": "192.168.0.170",
    "cnc_port": 8080,
    "proxy_port": 8888,
    "attack_types": ["calibration_drift", "power_reduction"]
  },
  "results": {
    "commands_intercepted": 13,
    "commands_modified": 5,
    "attack_success_rate": 1.0,
    "detection_rate": 0.0
  }
}
```

### CSV Data Files
Columns typically include:
- timestamp
- command_type
- original_command
- modified_command
- cnc_response
- position_x, position_y, position_z
- attack_type

## Usage Guidelines

### Reading Data
```python
import pandas as pd
import json

# Load experiment data
with open('experiment_20250915_095416.json', 'r') as f:
    experiment = json.load(f)

# Load CSV data
df = pd.read_csv('experiment_20250915_095416.csv')
```

### Analysis Scripts
See `analysis/` directory for pre-built scripts to analyze archived data:
- `generate_report.py` - Generate comprehensive reports
- `visualize_attacks.py` - Create attack visualization plots
- `statistical_analysis.py` - Perform statistical tests

## Data Retention Policy

- **Active experiments**: Kept in `data/archived_experiments/`
- **Baseline data**: Preserved in `data/baseline/`
- **Raw captures**: PCAP files stored separately (not in git)

## Privacy and Security

All data in this archive is from controlled laboratory experiments. No production system data or sensitive information is included.

## Citation

When using this data in publications, please cite the parent project and specify the experiment date range used in your analysis.

---

**Archive Status**: Active  
**Last Updated**: November 10, 2025  
**Total Experiments**: Multiple sessions from September 2025
