# Deployment Checklist

Use this checklist when setting up the project in a new environment or preparing for experiments.

## Pre-Deployment

### Environment Verification
- [ ] Docker installed (version 20.10+)
- [ ] Docker Compose available (v2.0+)
- [ ] Python 3.8+ installed
- [ ] Git installed
- [ ] Minimum 10GB disk space available
- [ ] System meets hardware requirements

### Network Preparation
- [ ] Isolated network available for testing
- [ ] No production systems on test network
- [ ] Physical safety measures in place (for hardware testing)
- [ ] Firewall rules configured (if applicable)

### Documentation Review
- [ ] Read README.md
- [ ] Review GETTING_STARTED.md
- [ ] Understand ARCHITECTURE.md
- [ ] Review safety guidelines

## Installation

### Initial Setup
- [ ] Clone repository
- [ ] Run `setup.sh` or manual setup
- [ ] Verify virtual environment created
- [ ] Install Python dependencies
- [ ] Create required directories

### Docker Infrastructure
- [ ] Navigate to `infrastructure/docker`
- [ ] Pull Docker images: `docker compose pull`
- [ ] Start containers: `docker compose up -d`
- [ ] Verify all containers running: `docker ps`
- [ ] Check container logs: `docker compose logs`

### Container Verification
- [ ] Access HostA: `docker exec -it A-10.9.0.5 /bin/bash`
- [ ] Access HostB: `docker exec -it B-10.9.0.6 /bin/bash`
- [ ] Access HostM: `docker exec -it M-10.9.0.105 /bin/bash`
- [ ] Test connectivity: `ping 10.9.0.5` from HostM
- [ ] Verify ARP cache: `arp -n` from each container

## Configuration

### Network Configuration
- [ ] Verify IP forwarding enabled on HostM
- [ ] Check iptables rules configured
- [ ] Verify network interface names
- [ ] Test inter-container communication

### Environment Variables (Optional)
- [ ] Set CNC_IP (if testing with hardware)
- [ ] Set CNC_PORT
- [ ] Set PROXY_PORT
- [ ] Set DATA_DIR

### Volume Permissions
- [ ] Verify write access to `infrastructure/volumes/`
- [ ] Verify write access to `data/`
- [ ] Check log directory exists: `infrastructure/volumes/logs/`

## Pre-Experiment

### Baseline Testing
- [ ] Run baseline network measurement
- [ ] Verify packet capture works
- [ ] Test ARP spoofing without G-code
- [ ] Document baseline performance

### Safety Checks (for hardware testing)
- [ ] Physical emergency stop accessible
- [ ] Workspace clear of hazards
- [ ] Visual monitoring setup
- [ ] Backup safety measures in place
- [ ] CNC machine in safe position

### Data Preparation
- [ ] Clear old experiment data (or archive)
- [ ] Verify disk space for captures
- [ ] Test data logging functionality
- [ ] Backup important existing data

## Experiment Execution

### Pre-Run
- [ ] Review experiment protocol
- [ ] Configure attack parameters
- [ ] Set duration and intensity
- [ ] Prepare monitoring tools
- [ ] Note start time

### During Experiment
- [ ] Monitor container health
- [ ] Watch for errors in logs
- [ ] Verify data collection
- [ ] Monitor disk space
- [ ] Document observations

### Post-Experiment
- [ ] Stop attack processes gracefully
- [ ] Save all log files
- [ ] Export data to archive
- [ ] Generate initial analysis
- [ ] Document findings

## Post-Deployment

### Cleanup
- [ ] Stop Docker containers: `docker compose down`
- [ ] Remove temporary files
- [ ] Archive experiment data
- [ ] Clear packet captures (or archive)
- [ ] Reset any modified configurations

### Data Management
- [ ] Move data to archived_experiments/
- [ ] Generate experiment report
- [ ] Update CHANGELOG.md (if applicable)
- [ ] Commit code changes to git
- [ ] Tag experiment version

### Maintenance
- [ ] Review system logs
- [ ] Check for security updates
- [ ] Update Docker images if needed
- [ ] Backup critical data
- [ ] Document lessons learned

## Troubleshooting Checklist

### If containers won't start:
- [ ] Check Docker daemon status
- [ ] Review container logs
- [ ] Verify port availability
- [ ] Check disk space
- [ ] Remove old containers: `docker compose down -v`

### If ARP poisoning fails:
- [ ] Verify privileged mode enabled
- [ ] Check IP forwarding: `cat /proc/sys/net/ipv4/ip_forward`
- [ ] Verify arpspoof installed
- [ ] Check network interface name
- [ ] Review container capabilities

### If G-code attacks fail:
- [ ] Verify CNC connectivity
- [ ] Check proxy configuration
- [ ] Test direct connection first
- [ ] Review firewall rules
- [ ] Check command syntax

### If data collection fails:
- [ ] Verify write permissions
- [ ] Check disk space
- [ ] Test logging manually
- [ ] Review file paths
- [ ] Check volume mounts

## Security Checklist

### Before Sharing/Publishing
- [ ] Remove any sensitive data
- [ ] Anonymize experiment results
- [ ] Review commit history
- [ ] Check for credentials in code
- [ ] Verify .gitignore coverage
- [ ] Update documentation
- [ ] Add proper attribution

### Ongoing Security
- [ ] Keep Docker images updated
- [ ] Review security advisories
- [ ] Monitor container activity
- [ ] Audit access logs
- [ ] Follow responsible disclosure

## Collaboration Checklist

### Before Adding Collaborators
- [ ] Review CONTRIBUTING.md with team
- [ ] Set up communication channels
- [ ] Define roles and responsibilities
- [ ] Establish data sharing protocols
- [ ] Agree on experiment protocols

### Version Control
- [ ] Create develop branch
- [ ] Set up branch protection
- [ ] Define merge procedures
- [ ] Document workflow
- [ ] Set up code review process

## Publication Checklist

### Before Publishing Results
- [ ] Verify all experiments reproducible
- [ ] Complete data documentation
- [ ] Update citation information
- [ ] Review ethical considerations
- [ ] Get institutional approval
- [ ] Prepare supplementary materials

---

## Quick Reference

**Start Everything:**
```bash
cd infrastructure/docker && docker compose up -d
```

**Stop Everything:**
```bash
cd infrastructure/docker && docker compose down
```

**View Status:**
```bash
docker ps && docker compose logs -f
```

**Emergency Stop:**
```bash
docker compose down && pkill -f arpspoof
```

---

**Last Updated**: November 10, 2025  
**Version**: 1.0.0
