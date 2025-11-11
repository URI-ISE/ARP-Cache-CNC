# Architecture Overview

## Manufacturing Systems Security Research Framework

This document provides a comprehensive overview of the system architecture, including network topology, software components, and data flow.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Network Topology](#network-topology)
3. [Software Architecture](#software-architecture)
4. [Attack Framework](#attack-framework)
5. [Defense Framework](#defense-framework)
6. [Data Pipeline](#data-pipeline)

---

## System Overview

The Manufacturing Systems Security Framework is designed as a modular, containerized research platform that enables reproducible experimentation on cyber-physical security vulnerabilities in industrial control systems.

### Key Design Principles

1. **Isolation**: All experiments run in containerized environments to prevent unintended network interference
2. **Reproducibility**: Configuration-as-code approach ensures experiments can be replicated
3. **Modularity**: Attack and defense mechanisms are independent modules that can be combined
4. **Observability**: Comprehensive logging and monitoring at all levels
5. **Safety**: Hardware testing includes safeguards to prevent physical damage

---

## Network Topology

### Docker Network Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Host Machine                          │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │          Docker Network: 10.9.0.0/24               │ │
│  │                                                    │ │
│  │  ┌──────────────┐    ┌──────────────┐            │ │
│  │  │   HostA      │    │   HostB      │            │ │
│  │  │  10.9.0.5    │◄──►│  10.9.0.6    │            │ │
│  │  │              │    │              │            │ │
│  │  │ (Victim/     │    │ (Victim/     │            │ │
│  │  │  Controller) │    │  CNC Target) │            │ │
│  │  └──────────────┘    └──────────────┘            │ │
│  │         ▲                   ▲                     │ │
│  │         │                   │                     │ │
│  │         │ ARP Poisoning     │                     │ │
│  │         │                   │                     │ │
│  │    ┌────┴───────────────────┴────┐               │ │
│  │    │        HostM                │               │ │
│  │    │      10.9.0.105             │               │ │
│  │    │                             │               │ │
│  │    │   (Attacker/Researcher)     │               │ │
│  │    │   - ARP Spoofing            │               │ │
│  │    │   - Packet Capture          │               │ │
│  │    │   - G-code MITM             │               │ │
│  │    └─────────────────────────────┘               │ │
│  │              │                                    │ │
│  └──────────────┼────────────────────────────────────┘ │
│                 │                                      │
│                 │ Port Mapping                         │
│                 ▼                                      │
│         Host: 8050 (Dashboard)                        │
│         Host: 8888 (Proxy)                            │
└─────────────────────────────────────────────────────────┘
```

### Physical Hardware Integration (Optional)

```
┌──────────────────────────────────────────────────────┐
│               Physical Network Layer                  │
│                                                       │
│  ┌─────────────┐         ┌──────────────┐          │
│  │   Mac/PC    │         │  GRBL CNC    │          │
│  │ 10.211.55.2 │◄───────►│192.168.0.170 │          │
│  │             │         │              │          │
│  └─────────────┘         └──────────────┘          │
│         ▲                        ▲                   │
│         │                        │                   │
│         │   ARP MITM Attack      │                   │
│         │                        │                   │
│    ┌────┴────────────────────────┴────┐             │
│    │     Attack VM (Ubuntu)           │             │
│    │       10.211.55.3                │             │
│    │                                  │             │
│    │  Runs G-code Proxy on Port 8888 │             │
│    └──────────────────────────────────┘             │
└──────────────────────────────────────────────────────┘
```

---

## Software Architecture

### Component Diagram

```
┌────────────────────────────────────────────────────────────┐
│                    Research Framework                       │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌─────────────────────────────────────────────────────┐  │
│  │           Experiment Orchestration Layer            │  │
│  │  - Scenario Manager                                 │  │
│  │  - Configuration Management                         │  │
│  │  - Experiment Lifecycle Control                     │  │
│  └─────────────────────────────────────────────────────┘  │
│                          │                                 │
│       ┌──────────────────┼──────────────────┐            │
│       ▼                  ▼                  ▼             │
│  ┌─────────┐      ┌─────────┐      ┌─────────┐          │
│  │ Attack  │      │ Defense │      │  Data   │          │
│  │ Modules │      │ Modules │      │ Logging │          │
│  └─────────┘      └─────────┘      └─────────┘          │
│       │                │                  │               │
│       └────────────────┼──────────────────┘               │
│                        ▼                                   │
│  ┌─────────────────────────────────────────────────────┐  │
│  │          Network Interception Layer                 │  │
│  │  - ARP Spoofing (dsniff/arpspoof)                   │  │
│  │  - Packet Capture (tcpdump/scapy)                   │  │
│  │  - G-code Proxy (custom Python)                     │  │
│  └─────────────────────────────────────────────────────┘  │
│                          │                                 │
│                          ▼                                 │
│  ┌─────────────────────────────────────────────────────┐  │
│  │               Target Systems                        │  │
│  │  - Docker Containers (HostA, HostB)                 │  │
│  │  - Physical GRBL Controller (optional)              │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### Module Hierarchy

```
scenarios/
├── research_framework.py       # Main orchestration
│   └── ResearchExperimentFramework
│       ├── configure_experiment()
│       ├── run_baseline_measurement()
│       ├── execute_attack_scenarios()
│       └── analyze_results()
│
├── research_scenarios.py       # Scenario definitions
│   ├── ResearchScenarioManager
│   └── StatisticalDataLogger
│
├── attack_modules/
│   ├── gcode_proxy.py         # MITM proxy
│   │   └── GRBLProxy
│   ├── attack_simulator.py    # Attack simulations
│   │   └── GCodeAttackSimulator
│   └── attack_simulator_advanced.py
│
└── defense_modules/
    └── prevention_modules.py   # Defense mechanisms
        ├── DefenseSystem
        ├── AuthenticationModule
        ├── EncryptionModule
        ├── AnomalyDetectionModule
        └── IntegrityVerificationModule
```

---

## Attack Framework

### Attack Taxonomy

#### 1. Network-Level Attacks
- **ARP Cache Poisoning**: Redirect traffic through attacker machine
- **Packet Sniffing**: Passive monitoring of G-code commands
- **Traffic Analysis**: Pattern recognition in command streams

#### 2. Protocol-Level Attacks
- **Command Interception**: Capture G-code in transit
- **Command Modification**: Alter parameters mid-stream
- **Command Injection**: Insert malicious commands
- **Command Suppression**: Drop legitimate commands

#### 3. Application-Level Attacks
- **Calibration Drift**: Gradual position errors
- **Power Manipulation**: Modify spindle/laser power
- **Speed Alteration**: Change feed rates
- **Tool Path Deviation**: Alter machining trajectory

### Attack Execution Pipeline

```
1. Network Setup
   └─► Enable IP forwarding on attacker
   └─► Configure iptables rules

2. ARP Poisoning
   └─► Spoof ARP replies to victim hosts
   └─► Maintain poisoned ARP cache

3. Traffic Interception
   └─► Capture packets on attacker interface
   └─► Forward traffic to maintain connectivity

4. G-code Analysis
   └─► Parse G-code commands from packets
   └─► Identify vulnerable operations

5. Attack Injection
   └─► Modify commands based on attack type
   └─► Forward modified commands to target

6. Data Collection
   └─► Log all commands (original & modified)
   └─► Record machine responses
   └─► Capture timing information
```

---

## Defense Framework

### Defense Layers

#### Layer 1: Network Isolation
- VLAN segmentation
- Firewall rules
- Network access control

#### Layer 2: Authentication
- HMAC-based command signing
- Nonce-based replay protection
- Time-window validation

#### Layer 3: Encryption
- AES-256 command encryption
- Secure key exchange
- Per-session encryption keys

#### Layer 4: Anomaly Detection
- Statistical behavior modeling
- Command sequence validation
- Threshold-based alerting

#### Layer 5: Integrity Verification
- Checksum validation
- Command hash verification
- End-to-end integrity checks

---

## Data Pipeline

### Data Flow Architecture

```
┌─────────────┐
│  Experiment │
│   Begins    │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│ Configuration Load  │
│  - Network params   │
│  - Attack types     │
│  - Duration         │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Baseline Collection │
│  - Normal behavior  │
│  - Performance data │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Attack Execution   │
│  - Real-time log    │
│  - Packet capture   │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│   Data Storage      │
│  - JSON files       │
│  - CSV exports      │
│  - PCAP captures    │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Post-Processing    │
│  - Aggregation      │
│  - Statistical calc │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Visualization      │
│  - Graphs           │
│  - Dashboard        │
│  - Reports          │
└─────────────────────┘
```

### Data Storage Structure

```
data/
├── archived_experiments/
│   ├── experiment_YYYYMMDD_HHMMSS.json
│   ├── experiment_YYYYMMDD_HHMMSS.csv
│   ├── attack_data_YYYYMMDD_HHMMSS.json
│   └── attack_stats_YYYYMMDD_HHMMSS.json
│
├── baseline/
│   ├── baseline_network_metrics.json
│   └── baseline_performance.csv
│
└── captures/
    └── capture_TIMESTAMP.pcap
```

---

## Technology Stack

### Infrastructure
- **Docker**: Container orchestration
- **Docker Compose**: Multi-container management
- **Linux (Ubuntu)**: Base OS for containers

### Networking
- **dsniff/arpspoof**: ARP poisoning
- **tcpdump**: Packet capture
- **scapy**: Packet crafting and analysis
- **iptables**: Traffic filtering and routing

### Programming Languages
- **Python 3.8+**: Primary development language
- **Bash**: Infrastructure scripting

### Python Libraries
- **Socket**: Low-level networking
- **Threading**: Concurrent operations
- **Scapy**: Packet manipulation
- **Pandas**: Data analysis
- **Matplotlib/Seaborn**: Visualization
- **Dash/Plotly**: Interactive dashboards
- **Cryptography**: Security implementations

### Data Formats
- **JSON**: Structured experiment data
- **CSV**: Tabular analysis data
- **PCAP**: Network capture files
- **Markdown**: Documentation

---

## Security Considerations

### Research Ethics
- All testing must be conducted in isolated environments
- Obtain proper authorization before hardware testing
- Document all experiments for reproducibility
- Follow responsible disclosure practices

### System Hardening
- Containers run with minimal required privileges
- Network isolation prevents external interference
- Sensitive data is not stored in containers
- Regular security updates for base images

---

**Document Version**: 1.0.0  
**Last Updated**: November 10, 2025  
**Authors**: Research Team
