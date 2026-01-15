# CNC Security Experiment Documentation

## Experiment Session: September 9, 2025

### Configuration
- **CNC Device**: GRBL Controller at 192.168.0.170:8080
- **Controller**: Mac at 10.211.55.2  
- **Attack VM**: Ubuntu at 10.211.55.3
- **Proxy Port**: 8888
- **Network Mode**: Parallels Shared (NAT)

### Successful Tests Completed

#### 1. Proxy Interception ✓
```
Time: 10:30:51 - 10:30:57
Commands Intercepted: 2
- G0 X1
- G0 X2
Bytes Transferred: 16
Status: SUCCESS - Proxy successfully intercepted traffic
```

#### 2. Attack Simulations ✓

##### A. Calibration Drift Attack (10:32:40)
- **Objective**: Gradually introduce position errors
- **Implementation**: Progressive drift of 0.1mm per command
- **Results**:
  - Commands sent: 5 movement commands
  - Total drift applied: 0.5mm
  - Final position error: X+0.4mm, Y+0.4mm
  - CNC Response: All commands accepted (ok)
  - **Impact**: Would cause cumulative positioning errors in production

##### B. Power Reduction Attack (10:32:56)
- **Objective**: Reduce laser/spindle power
- **Implementation**: 50% power reduction (S800 → S400)
- **Results**:
  - Original power: S800
  - Modified power: S400
  - CNC Response: Command accepted
  - **Impact**: Incomplete cuts, reduced material penetration

##### C. Command Injection Attack (10:33:08)
- **Objective**: Insert malicious commands between legitimate ones
- **Implementation**: Inject "G1 Z-0.1" after each command
- **Results**:
  - Legitimate commands: 2
  - Injected commands: 2
  - Final Z position: -0.1mm (confirmed at 10:33:14)
  - **Impact**: Physical damage to workpiece, tool collision risk

### Machine State Changes Observed

| Time     | Position (X,Y,Z)      | Notes                    |
|----------|----------------------|--------------------------|
| 10:31:26 | 1.000, 0.000, 0.000  | After G0 X1              |
| 10:31:55 | 50.000, 0.000, 0.000 | After G0 X50             |
| 10:32:07 | -50.000, 0.000, 0.000| After G0 X-50            |
| 10:32:53 | 10.000, 10.000, 0.000| After drift attack       |
| 10:33:04 | 30.000, 30.000, 0.000| After power attack       |
| 10:33:14 | 50.000, 40.000, -0.100| After injection attack  |

### Attack Effectiveness Analysis

#### Without Defenses
- **Attack Success Rate**: 100%
- **Commands Modified**: All targeted commands
- **Detection Rate**: 0% (no defenses active)
- **CNC Acceptance**: 100% (all modified commands executed)

#### Key Findings

1. **Calibration Drift**
   - Subtle attack, hard to detect visually
   - Cumulative effect significant over time
   - No GRBL errors or warnings generated

2. **Power Reduction**
   - Immediately affects output quality
   - Could cause incomplete operations
   - GRBL accepts any valid power value

3. **Command Injection**
   - Most dangerous - causes physical movement
   - Z-axis movement confirmed in machine state
   - Could cause collision or damage

### Security Implications

1. **Network Vulnerability**: 
   - Clear-text G-code transmission
   - No authentication required
   - Commands accepted from any source on network

2. **Protocol Weakness**:
   - GRBL accepts any syntactically valid command
   - No command sequence validation
   - No integrity checking

3. **Physical Impact**:
   - All attacks caused real machine state changes
   - Potential for physical damage demonstrated
   - No safety interlocks triggered

### Recommendations

1. **Immediate Mitigations**:
   - Implement command authentication
   - Add boundary checking in firmware
   - Monitor for anomalous command patterns

2. **Long-term Solutions**:
   - Encrypted communication channel
   - Command signing/verification
   - Real-time anomaly detection
   - Physical limit switches as failsafe

### Next Experiments

1. Test defense mechanisms against these attacks
2. Measure detection latency
3. Evaluate false positive rates
4. Test more sophisticated attack patterns

### Data Files Generated
- `experiment_20250909_*.json` - Structured data
- `experiment_20250909_*.csv` - For statistical analysis
- `attack_simulator.py` - Attack implementation
- `minimal_interceptor.py` - Proxy implementation

## Conclusion

Successfully demonstrated three distinct attack vectors against GRBL-based CNC system. All attacks resulted in actual machine state changes, confirming vulnerability to man-in-the-middle attacks. The lack of authentication and integrity checking in the G-code protocol presents significant security risks for cyber-physical systems.
