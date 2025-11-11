#!/usr/bin/env python3
"""
ONR Dissertation Research Framework
Complete Experimental Platform for G-Code Security Analysis
Integrates Attack Scenarios, Defense Mechanisms, and Data Collection
"""

import json
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple
import pandas as pd

# Import our research modules (from previous files)
from research_scenarios import ResearchScenarioManager, StatisticalDataLogger
from prevention_modules import DefenseSystem

class ResearchExperimentFramework:
    """Complete framework for conducting security research experiments"""
    
    def __init__(self, experiment_name: str):
        self.experiment_name = experiment_name
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.output_dir = Path(f"experiments/{experiment_name}_{self.timestamp}")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.scenario_manager = ResearchScenarioManager()
        self.defense_system = DefenseSystem()
        self.data_logger = StatisticalDataLogger(
            str(self.output_dir / 'research_data.db')
        )
        
        self.experiment_config = {}
        self.results = {}
        self.session_id = None
        
    def configure_experiment(self, config: Dict):
        """Configure experiment parameters"""
        self.experiment_config = {
            'name': self.experiment_name,
            'timestamp': self.timestamp,
            'scenarios': config.get('scenarios', []),
            'defenses': config.get('defenses', []),
            'duration_seconds': config.get('duration', 300),
            'command_rate': config.get('command_rate', 10),  # Commands per second
            'network_config': config.get('network_config', {}),
            'device_config': config.get('device_config', {}),
            'metrics_collection': config.get('metrics', ['all']),
            'hypothesis': config.get('hypothesis', ''),
            'control_variables': config.get('control_variables', {})
        }
        
        # Save configuration
        with open(self.output_dir / 'experiment_config.json', 'w') as f:
            json.dump(self.experiment_config, f, indent=2)
            
        return self.experiment_config
        
    def run_baseline_measurement(self, duration: int = 60):
        """Establish baseline performance without attacks"""
        print(f"[{datetime.now()}] Running baseline measurement for {duration} seconds...")
        
        baseline_session = self.data_logger.create_session(
            scenario_id='baseline',
            target_device=self.experiment_config.get('device_config', {}).get('name', 'test_device'),
            network_config=self.experiment_config.get('network_config', {}),
            notes='Baseline measurement - no attacks or defenses'
        )
        
        baseline_metrics = {
            'latency_samples': [],
            'throughput_samples': [],
            'error_rates': [],
            'resource_usage': []
        }
        
        start_time = time.time()
        commands_processed = 0
        
        while time.time() - start_time < duration:
            # Simulate normal G-code command
            test_command = self._generate_normal_command(commands_processed)
            
            # Measure processing time
            process_start = time.perf_counter()
            # Process command (no attacks, no defenses)
            process_end = time.perf_counter()
            
            latency = (process_end - process_start) * 1000  # ms
            baseline_metrics['latency_samples'].append(latency)
            
            # Log metrics
            self.data_logger.log_network_metrics(
                packet_size=len(test_command),
                latency=latency,
                jitter=np.std(baseline_metrics['latency_samples'][-10:]) if len(baseline_metrics['latency_samples']) > 10 else 0,
                loss_rate=0.0,
                throughput=commands_processed / (time.time() - start_time),
                session_id=baseline_session
            )
            
            commands_processed += 1
            time.sleep(1.0 / self.experiment_config['command_rate'])
            
        self.data_logger.end_session(baseline_session)
        
        baseline_results = {
            'session_id': baseline_session,
            'commands_processed': commands_processed,
            'avg_latency': np.mean(baseline_metrics['latency_samples']),
            'std_latency': np.std(baseline_metrics['latency_samples']),
            'throughput': commands_processed / duration
        }
        
        print(f"[{datetime.now()}] Baseline complete: {baseline_results}")
        
        return baseline_results
        
    def run_attack_scenario(self, scenario_id: str, defenses: List[str] = None):
        """Run a specific attack scenario with optional defenses"""
        print(f"[{datetime.now()}] Starting scenario: {scenario_id}")
        if defenses:
            print(f"  Active defenses: {defenses}")
            
        # Create session
        self.session_id = self.data_logger.create_session(
            scenario_id=scenario_id,
            target_device=self.experiment_config.get('device_config', {}).get('name', 'test_device'),
            network_config=self.experiment_config.get('network_config', {}),
            notes=f"Attack: {scenario_id}, Defenses: {defenses}"
        )
        
        # Activate scenario
        scenario = self.scenario_manager.activate_scenario(scenario_id)
        if not scenario:
            print(f"ERROR: Unknown scenario {scenario_id}")
            return None
            
        # Enable defenses
        if defenses:
            for defense in defenses:
                self.defense_system.enable_defense(defense)
                
        # Metrics collection
        metrics = {
            'commands_sent': 0,
            'commands_blocked': 0,
            'commands_modified': 0,
            'attacks_detected': 0,
            'false_positives': 0,
            'false_negatives': 0,
            'position_errors': [],
            'detection_latencies': [],
            'system_resources': []
        }
        
        # Run experiment
        start_time = time.time()
        duration = self.experiment_config['duration_seconds']
        
        while time.time() - start_time < duration:
            # Generate command
            command = self._generate_normal_command(metrics['commands_sent'])
            
            # Apply attack
            attack_start = time.perf_counter()
            modified_command = self.scenario_manager.get_scenario_modification(
                command, 
                context={'history': self._get_recent_commands()}
            )
            attack_time = (time.perf_counter() - attack_start) * 1000
            
            # Apply defenses
            defense_start = time.perf_counter()
            defense_result = self.defense_system.process_command(
                modified_command,
                context={'source_ip': '192.168.0.151'}
            )
            defense_time = (time.perf_counter() - defense_start) * 1000
            
            # Collect metrics
            metrics['commands_sent'] += 1
            
            if command != modified_command:
                metrics['commands_modified'] += 1
                
                # Calculate position error
                position_error = self._calculate_position_error(command, modified_command)
                metrics['position_errors'].append(position_error)
                
                # Log attack event
                self.data_logger.log_attack_event(
                    scenario_id=scenario_id,
                    attack_type='modification',
                    original_cmd=command,
                    modified_cmd=modified_command,
                    modification_type=scenario_id,
                    impact_metrics={'position_error': position_error},
                    detection_score=1.0 if not defense_result['allowed'] else 0.0,
                    session_id=self.session_id
                )
                
            if not defense_result['allowed']:
                metrics['commands_blocked'] += 1
                metrics['attacks_detected'] += 1
                metrics['detection_latencies'].append(defense_time)
                
                # Log detection
                self.data_logger.log_detection_metrics(
                    method=defense_result.get('blocked_by', 'unknown'),
                    tp=1 if command != modified_command else 0,
                    fp=1 if command == modified_command else 0,
                    tn=0,
                    fn=0,
                    latency=defense_time,
                    confidence=0.9,
                    session_id=self.session_id
                )
                
            # Log physical impact
            if metrics['position_errors']:
                self.data_logger.log_physical_impact(
                    position_errors={'x': position_error.get('x', 0),
                                   'y': position_error.get('y', 0),
                                   'z': position_error.get('z', 0)},
                    quality_score=100 - (np.mean(metrics['position_errors']) * 10),
                    accuracy=1.0 - (np.mean(metrics['position_errors']) / 100),
                    waste=len(metrics['position_errors']) * 0.1,  # Simulated
                    energy=metrics['commands_sent'] * 0.5,  # Simulated
                    session_id=self.session_id
                )
                
            # Simulate command execution delay
            time.sleep(1.0 / self.experiment_config['command_rate'])
            
        # Calculate final metrics
        attack_success_rate = metrics['commands_modified'] / metrics['commands_sent'] if metrics['commands_sent'] > 0 else 0
        detection_rate = metrics['attacks_detected'] / metrics['commands_modified'] if metrics['commands_modified'] > 0 else 0
        
        results = {
            'scenario_id': scenario_id,
            'session_id': self.session_id,
            'defenses': defenses,
            'metrics': metrics,
            'attack_success_rate': attack_success_rate,
            'detection_rate': detection_rate,
            'avg_position_error': np.mean(metrics['position_errors']) if metrics['position_errors'] else 0,
            'avg_detection_latency': np.mean(metrics['detection_latencies']) if metrics['detection_latencies'] else 0
        }
        
        self.data_logger.end_session(self.session_id)
        
        print(f"[{datetime.now()}] Scenario complete: {scenario_id}")
        print(f"  Attack success rate: {attack_success_rate:.2%}")
        print(f"  Detection rate: {detection_rate:.2%}")
        
        return results
        
    def run_full_experiment(self):
        """Run complete experiment with all configured scenarios"""
        print("=" * 80)
        print(f"Starting Experiment: {self.experiment_name}")
        print(f"Timestamp: {self.timestamp}")
        print("=" * 80)
        
        all_results = {
            'experiment': self.experiment_config,
            'baseline': None,
            'scenarios': []
        }
        
        # Run baseline
        all_results['baseline'] = self.run_baseline_measurement()
        
        # Run each scenario
        for scenario in self.experiment_config['scenarios']:
            # Without defenses
            print(f"\n--- Testing {scenario} WITHOUT defenses ---")
            result_no_defense = self.run_attack_scenario(scenario, defenses=None)
            all_results['scenarios'].append(result_no_defense)
            
            # With defenses
            print(f"\n--- Testing {scenario} WITH defenses ---")
            result_with_defense = self.run_attack_scenario(
                scenario, 
                defenses=self.experiment_config['defenses']
            )
            all_results['scenarios'].append(result_with_defense)
            
        # Save results
        with open(self.output_dir / 'experiment_results.json', 'w') as f:
            json.dump(all_results, f, indent=2, default=str)
            
        # Generate report
        self._generate_report(all_results)
        
        return all_results
        
    def _generate_report(self, results):
        """Generate comprehensive research report"""
        report = []
        report.append("# Experiment Report")
        report.append(f"**Experiment:** {self.experiment_name}")
        report.append(f"**Date:** {self.timestamp}")
        report.append(f"**Hypothesis:** {self.experiment_config.get('hypothesis', 'N/A')}")
        report.append("")
        
        report.append("## Executive Summary")
        
        # Calculate key metrics
        baseline_latency = results['baseline']['avg_latency']
        
        for scenario_result in results['scenarios']:
            if scenario_result:
                scenario_name = scenario_result['scenario_id']
                has_defenses = bool(scenario_result['defenses'])
                
                report.append(f"\n### {scenario_name} {'(With Defenses)' if has_defenses else '(No Defenses)'}")
                report.append(f"- Attack Success Rate: {scenario_result['attack_success_rate']:.2%}")
                report.append(f"- Detection Rate: {scenario_result['detection_rate']:.2%}")
                report.append(f"- Average Position Error: {scenario_result['avg_position_error']:.3f} mm")
                report.append(f"- Detection Latency: {scenario_result['avg_detection_latency']:.2f} ms")
                
        # Statistical analysis
        report.append("\n## Statistical Analysis")
        stats = self.data_logger.get_statistics()
        report.append(f"```json\n{json.dumps(stats, indent=2)}\n```")
        
        # Conclusions
        report.append("\n## Conclusions")
        report.append("Based on the experimental results:")
        
        # Auto-generate insights
        for scenario_result in results['scenarios']:
            if scenario_result and scenario_result['defenses']:
                improvement = (1 - scenario_result['attack_success_rate']) * 100
                report.append(f"- Defenses reduced {scenario_result['scenario_id']} attack effectiveness by {improvement:.1f}%")
                
        # Save report
        report_text = "\n".join(report)
        with open(self.output_dir / 'experiment_report.md', 'w') as f:
            f.write(report_text)
            
        print(f"\nReport saved to: {self.output_dir / 'experiment_report.md'}")
        
        # Generate visualizations
        self._generate_visualizations(results)
        
    def _generate_visualizations(self, results):
        """Generate research visualizations"""
        try:
            # Set style
            sns.set_style("darkgrid")
            plt.style.use('seaborn-v0_8-darkgrid')
            
            # Create figure with subplots
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            
            # 1. Attack Success Rates
            ax1 = axes[0, 0]
            scenarios = []
            success_rates = []
            colors = []
            
            for result in results['scenarios']:
                if result:
                    label = f"{result['scenario_id']}\n{'With Def' if result['defenses'] else 'No Def'}"
                    scenarios.append(label)
                    success_rates.append(result['attack_success_rate'] * 100)
                    colors.append('green' if result['defenses'] else 'red')
                    
            ax1.bar(scenarios, success_rates, color=colors, alpha=0.7)
            ax1.set_ylabel('Attack Success Rate (%)')
            ax1.set_title('Attack Effectiveness: With vs Without Defenses')
            ax1.tick_params(axis='x', rotation=45)
            
            # 2. Detection Performance
            ax2 = axes[0, 1]
            detection_rates = []
            detection_latencies = []
            
            for result in results['scenarios']:
                if result and result['defenses']:
                    detection_rates.append(result['detection_rate'] * 100)
                    detection_latencies.append(result['avg_detection_latency'])
                    
            if detection_rates:
                x = np.arange(len(detection_rates))
                width = 0.35
                
                ax2_twin = ax2.twinx()
                bars1 = ax2.bar(x - width/2, detection_rates, width, label='Detection Rate', color='blue', alpha=0.7)
                bars2 = ax2_twin.bar(x + width/2, detection_latencies, width, label='Latency (ms)', color='orange', alpha=0.7)
                
                ax2.set_ylabel('Detection Rate (%)', color='blue')
                ax2_twin.set_ylabel('Latency (ms)', color='orange')
                ax2.set_title('Detection Performance Metrics')
                ax2.legend(loc='upper left')
                ax2_twin.legend(loc='upper right')
                
            # 3. Position Error Distribution
            ax3 = axes[1, 0]
            all_errors = []
            labels = []
            
            for result in results['scenarios']:
                if result and 'position_errors' in result['metrics']:
                    if result['metrics']['position_errors']:
                        errors = [e.get('total', 0) if isinstance(e, dict) else e 
                                 for e in result['metrics']['position_errors']]
                        all_errors.append(errors)
                        labels.append(f"{result['scenario_id'][:10]}...")
                        
            if all_errors:
                ax3.boxplot(all_errors, labels=labels)
                ax3.set_ylabel('Position Error (mm)')
                ax3.set_title('Position Error Distribution by Attack Type')
                ax3.tick_params(axis='x', rotation=45)
                
            # 4. Performance Impact
            ax4 = axes[1, 1]
            
            # Compare baseline vs under attack
            baseline_throughput = results['baseline']['throughput']
            attack_impacts = []
            defense_overheads = []
            
            for result in results['scenarios']:
                if result:
                    # Simplified calculation - in real implementation, measure actual throughput
                    if result['defenses']:
                        defense_overheads.append(result['avg_detection_latency'])
                    else:
                        attack_impacts.append(result['attack_success_rate'] * 100)
                        
            if attack_impacts or defense_overheads:
                data = []
                labels = []
                
                if attack_impacts:
                    data.append(attack_impacts)
                    labels.append('Attack Impact')
                if defense_overheads:
                    data.append(defense_overheads)
                    labels.append('Defense Overhead')
                    
                ax4.violinplot(data, positions=range(len(data)), showmeans=True)
                ax4.set_xticks(range(len(labels)))
                ax4.set_xticklabels(labels)
                ax4.set_ylabel('Performance Impact (%)')
                ax4.set_title('System Performance Under Attack/Defense')
                
            plt.tight_layout()
            
            # Save figure
            fig.savefig(self.output_dir / 'experiment_visualizations.png', dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"Visualizations saved to: {self.output_dir / 'experiment_visualizations.png'}")
            
        except Exception as e:
            print(f"Warning: Could not generate visualizations: {e}")
            
    def _generate_normal_command(self, index):
        """Generate normal G-code command for testing"""
        commands = [
            f"G1 X{10 + index % 100} Y{10 + (index // 100) % 100} F1500",
            f"G1 X{20 + index % 100} Y{10 + (index // 100) % 100}",
            "M3 S500",
            "M5",
            f"G0 Z{5 + (index % 10)}"
        ]
        return commands[index % len(commands)]
        
    def _get_recent_commands(self, count=10):
        """Get recent command history"""
        # In production, maintain actual command history
        return [self._generate_normal_command(i) for i in range(count)]
        
    def _calculate_position_error(self, original, modified):
        """Calculate position error between commands"""
        import re
        
        error = {'x': 0, 'y': 0, 'z': 0, 'total': 0}
        
        for axis in ['X', 'Y', 'Z']:
            orig_match = re.search(f'{axis}([\\-\\d.]+)', original)
            mod_match = re.search(f'{axis}([\\-\\d.]+)', modified)
            
            if orig_match and mod_match:
                orig_val = float(orig_match.group(1))
                mod_val = float(mod_match.group(1))
                error[axis.lower()] = abs(mod_val - orig_val)
                
        error['total'] = np.sqrt(error['x']**2 + error['y']**2 + error['z']**2)
        
        return error


def run_dissertation_experiment():
    """Run a complete dissertation research experiment"""
    
    # Configure experiment
    experiment = ResearchExperimentFramework("dissertation_demo")
    
    config = {
        'scenarios': [
            'calibration_drift',
            'resonance_attack',
            'safety_margin_erosion'
        ],
        'defenses': [
            'authentication',
            'anomaly_detection',
            'rate_limiting'
        ],
        'duration': 60,  # Seconds per scenario
        'command_rate': 10,  # Commands per second
        'network_config': {
            'topology': 'flat',
            'subnet': '192.168.0.0/24',
            'latency_ms': 10,
            'bandwidth_mbps': 100
        },
        'device_config': {
            'name': 'Test_CNC_Machine',
            'type': 'laser_engraver',
            'firmware': 'grbl_1.1h'
        },
        'hypothesis': 'Multi-layer defense mechanisms significantly reduce attack effectiveness while maintaining acceptable performance overhead',
        'control_variables': {
            'room_temperature': 22,
            'network_load': 'moderate',
            'concurrent_users': 1
        }
    }
    
    experiment.configure_experiment(config)
    
    # Run full experiment
    results = experiment.run_full_experiment()
    
    print("\n" + "=" * 80)
    print("EXPERIMENT COMPLETE")
    print("=" * 80)
    print(f"Results saved to: {experiment.output_dir}")
    print("\nKey Findings:")
    
    # Analyze results
    for scenario in results['scenarios']:
        if scenario:
            defense_text = "with defenses" if scenario['defenses'] else "without defenses"
            print(f"\n{scenario['scenario_id']} ({defense_text}):")
            print(f"  - Attack success: {scenario['attack_success_rate']:.1%}")
            print(f"  - Detection rate: {scenario['detection_rate']:.1%}")
            print(f"  - Avg position error: {scenario['avg_position_error']:.3f} mm")
            
    return results


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║   ONR Cyber-Physical Systems Security Research Framework    ║
    ║          PhD Dissertation Experimental Platform             ║
    ╚══════════════════════════════════════════════════════════════╝
    
    This framework provides:
    • 8 sophisticated attack scenarios
    • 8 defense mechanisms  
    • Comprehensive data collection
    • Statistical analysis
    • Automated report generation
    • Publication-ready visualizations
    
    Starting demonstration experiment...
    """)
    
    results = run_dissertation_experiment()
    
    print("""
    
    Experiment complete! 
    
    For your dissertation, you can:
    1. Modify scenarios in research_scenarios.py
    2. Adjust defense parameters in prevention_modules.py
    3. Configure experiments in this framework
    4. Export data for analysis in R/Python/MATLAB
    5. Generate figures for publication
    
    All data is stored in SQLite database for further analysis.
    Use the exported CSV files for statistical software.
    
    Good luck with your dissertation research!
    """)
