# Scripts Directory

Utility and orchestration scripts for the Manufacturing Systems Security Framework.

## Available Scripts

### complete_experiment.py
Orchestrates complete experimental workflows including:
- Environment setup
- Baseline measurements
- Attack execution
- Data collection
- Result analysis

**Usage:**
```bash
python3 complete_experiment.py --config experiment_config.json
```

## Creating New Scripts

When adding new scripts to this directory:

1. **Use descriptive names**: `verb_noun.py` (e.g., `analyze_results.py`)
2. **Include shebang**: `#!/usr/bin/env python3`
3. **Add docstrings**: Document purpose, usage, and arguments
4. **Handle errors**: Use try/except for robustness
5. **Accept arguments**: Use argparse for CLI options
6. **Log actions**: Print informative messages

### Script Template

```python
#!/usr/bin/env python3
"""
Script Name - Brief Description

Detailed description of what this script does.

Usage:
    python3 script_name.py --arg value
"""

import argparse
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description='Script description')
    parser.add_argument('--arg', help='Argument description')
    args = parser.parse_args()
    
    # Script logic here
    print(f"[*] Starting operation...")
    
    try:
        # Your code
        pass
    except Exception as e:
        print(f"[!] Error: {e}")
        sys.exit(1)
    
    print(f"[+] Operation complete")

if __name__ == '__main__':
    main()
```

## Common Script Patterns

### Data Processing
- Input: Raw experiment data
- Processing: Analysis, filtering, aggregation
- Output: Processed results, reports

### Automation
- Setup: Configure environment
- Execution: Run experiments
- Cleanup: Restore state

### Visualization
- Load: Read experiment data
- Plot: Generate visualizations
- Save: Export charts and reports

---

**Last Updated**: November 10, 2025
