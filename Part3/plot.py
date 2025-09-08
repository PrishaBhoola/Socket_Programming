#!/usr/bin/env python3
"""
Plotting and analysis for Greedy Client FCFS Fairness (Part 3)
Generates visualizations showing fairness impact of greedy behavior
"""

import csv
import matplotlib.pyplot as plt
import numpy as np
import argparse
from pathlib import Path

def load_results(results_file):
    """Load experimental results"""
    if not Path(results_file).exists():
        print(f"Results file not found: {results_file}")
        return None

    results_by_c = {}

    with open(results_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            c_value = int(row['c_value'])
            fairness_ratio = float(row['fairness_ratio'])
            greedy_time = float(row['greedy_completion_time'])
            normal_time = float(row['normal_avg_completion_time'])

            if c_value not in results_by_c:
                results_by_c[c_value] = {
                    'fairness_ratios': [],
                    'greedy_times': [],
                    'normal_times': []
                }

            results_by_c[c_value]['fairness_ratios'].append(fairness_ratio)
            results_by_c[c_value]['greedy_times'].append(greedy_time)
            results_by_c[c_value]['normal_times'].append(normal_time)

    return results_by_c

def calculate_statistics(results_by_c):
    """Calculate statistics for each c value"""
    stats = {}

    for c_value, data in results_by_c.items():
        stats[c_value] = {
            'avg_fairness_ratio': np.mean(data['fairness_ratios']),
            'std_fairness_ratio': np.std(data['fairness_ratios']),
            'avg_greedy_time': np.mean(data['greedy_times']),
            'std_greedy_time': np.std(data['greedy_times']),
            'avg_normal_time': np.mean(data['normal_times']),
            'std_normal_time': np.std(data['normal_times']),
            'num_samples': len(data['fairness_ratios'])
        }

    return stats

def create_fairness_ratio_plot(stats, output_file='fairness_ratio_plot.png'):
    """Create main fairness ratio plot"""
    c_values = sorted(stats.keys())
    fairness_ratios = [stats[c]['avg_fairness_ratio'] for c in c_values]
    fairness_stds = [stats[c]['std_fairness_ratio'] for c in c_values]

    plt.figure(figsize=(12, 8))

    # Main plot with error bars
    plt.errorbar(c_values, fairness_ratios, yerr=fairness_stds,
                marker='o', capsize=5, capthick=2, linewidth=3, markersize=10,
                color='red', label='Measured Fairness Ratio')

    # Theoretical line (perfect efficiency would follow c)
    plt.plot(c_values, c_values, '--', color='blue', alpha=0.7, linewidth=2,
             label='Theoretical Maximum (Perfect Efficiency)')

    # Diagonal reference line
    if c_values:
        plt.plot([min(c_values), max(c_values)], [1, 1], ':', color='gray', alpha=0.5,
                 label='Fair (1:1 ratio)')

    plt.xlabel('C (Number of Greedy Client Requests)', fontsize=14)
    plt.ylabel('Fairness Ratio (Normal Avg Time / Greedy Time)', fontsize=14)
    plt.title('FCFS Fairness Analysis: Impact of Greedy Client Behavior\n' +
             'Higher ratio = more unfairness to normal clients', fontsize=16)
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=12)

    # Add annotations
    for i, (x, y) in enumerate(zip(c_values, fairness_ratios)):
        if i % 2 == 0:  # Annotate every other point to avoid clutter
            plt.annotate(f'{y:.1f}x', (x, y), 
                        textcoords="offset points", xytext=(0,15), ha='center',
                        fontsize=10, alpha=0.7)

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✅ Saved fairness ratio plot: {output_file}")
    return output_file

def create_completion_times_plot(stats, output_file='completion_times_plot.png'):
    """Create completion times comparison plot"""
    c_values = sorted(stats.keys())
    greedy_times = [stats[c]['avg_greedy_time'] for c in c_values]
    normal_times = [stats[c]['avg_normal_time'] for c in c_values]
    greedy_stds = [stats[c]['std_greedy_time'] for c in c_values]
    normal_stds = [stats[c]['std_normal_time'] for c in c_values]

    plt.figure(figsize=(12, 8))

    # Plot both lines
    plt.errorbar(c_values, greedy_times, yerr=greedy_stds,
                marker='s', capsize=4, linewidth=2, markersize=8,
                color='green', label='Greedy Client (gets c requests)')

    plt.errorbar(c_values, normal_times, yerr=normal_stds,
                marker='^', capsize=4, linewidth=2, markersize=8,
                color='orange', label='Normal Clients Average (1 request each)')

    plt.xlabel('C (Number of Greedy Client Requests)', fontsize=14)
    plt.ylabel('Completion Time (ms)', fontsize=14)
    plt.title('Completion Times: Greedy vs Normal Clients\n' +
             'Shows how greedy behavior affects completion times', fontsize=16)
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=12)

    # Fill area between lines to show advantage
    plt.fill_between(c_values, greedy_times, normal_times, alpha=0.2, color='red',
                     label='Greedy Advantage')
    plt.legend(fontsize=12)

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✅ Saved completion times plot: {output_file}")
    return output_file

def create_efficiency_analysis_plot(stats, output_file='efficiency_analysis.png'):
    """Create efficiency analysis plot"""
    c_values = sorted(stats.keys())
    fairness_ratios = [stats[c]['avg_fairness_ratio'] for c in c_values]

    # Calculate efficiency (actual ratio / theoretical ratio)
    efficiency = [ratio / c for c, ratio in zip(c_values, fairness_ratios)]

    plt.figure(figsize=(12, 8))

    # Efficiency plot
    plt.plot(c_values, efficiency, marker='D', linewidth=3, markersize=8,
             color='purple', label='FCFS Efficiency')

    # Reference lines
    plt.axhline(y=1.0, color='green', linestyle='--', alpha=0.7,
                label='Perfect Efficiency (1.0)')
    plt.axhline(y=0.5, color='orange', linestyle=':', alpha=0.7,
                label='50% Efficiency')

    plt.xlabel('C (Number of Greedy Client Requests)', fontsize=14)
    plt.ylabel('Efficiency (Actual Fairness Ratio / C)', fontsize=14)
    plt.title('FCFS Scheduling Efficiency Analysis\n' +
             'How well does the unfairness scale with greedy requests?', fontsize=16)
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=12)
    plt.ylim(0, 1.2)

    # Add efficiency annotations
    for x, y in zip(c_values, efficiency):
        plt.annotate(f'{y:.2f}', (x, y), 
                    textcoords="offset points", xytext=(0,10), ha='center',
                    fontsize=9)

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✅ Saved efficiency analysis plot: {output_file}")
    return output_file

def print_summary_analysis(stats):
    """Print detailed fairness analysis"""
    print("\n" + "="*60)
    print("GREEDY CLIENT FAIRNESS ANALYSIS SUMMARY")
    print("="*60)

    c_values = sorted(stats.keys())
    print(f"\nTested C values: {c_values}")

    print("\nDetailed Results:")
    print("C Value | Fairness Ratio | Greedy Time | Normal Time | Efficiency | Samples")
    print("--------|----------------|-------------|-------------|------------|--------")

    for c_value in c_values:
        s = stats[c_value]
        efficiency = s['avg_fairness_ratio'] / c_value

        print(f"{c_value:7d} | {s['avg_fairness_ratio']:12.2f}x | {s['avg_greedy_time']:9.1f} ms | "
              f"{s['avg_normal_time']:9.1f} ms | {efficiency:8.2f} | {s['num_samples']:6d}")

    # Impact analysis
    if len(c_values) >= 2:
        first_c = c_values[0]
        last_c = c_values[-1]

        first_ratio = stats[first_c]['avg_fairness_ratio']
        last_ratio = stats[last_c]['avg_fairness_ratio']

        print(f"\n=== FAIRNESS IMPACT ANALYSIS ===")
        print(f"C range tested: {first_c} → {last_c} ({last_c/first_c:.1f}x increase)")
        print(f"Fairness ratio change: {first_ratio:.2f}x → {last_ratio:.2f}x ({last_ratio/first_ratio:.1f}x increase)")

        # Theoretical vs actual
        theoretical_change = last_c / first_c
        actual_change = last_ratio / first_ratio

        print(f"\nEfficiency Analysis:")
        print(f"  Theoretical unfairness increase: {theoretical_change:.1f}x")
        print(f"  Actual unfairness increase: {actual_change:.1f}x")
        print(f"  FCFS efficiency: {actual_change/theoretical_change:.2f}")

        if actual_change / theoretical_change > 0.7:
            print("  ✅ FCFS shows strong unfairness scaling")
        elif actual_change / theoretical_change > 0.4:
            print("  ⚠️ FCFS shows moderate unfairness scaling")
        else:
            print("  ❓ FCFS shows weak unfairness scaling")

        # Worst case analysis
        max_ratio = max(stats[c]['avg_fairness_ratio'] for c in c_values)
        worst_c = [c for c in c_values if stats[c]['avg_fairness_ratio'] == max_ratio][0]

        print(f"\nWorst Case Fairness:")
        print(f"  At c={worst_c}: Normal clients take {max_ratio:.1f}x longer than greedy client")
        print(f"  Greedy client gets {worst_c}x more data in {stats[worst_c]['avg_greedy_time']:.1f} ms")
        print(f"  Normal clients get 1x data in {stats[worst_c]['avg_normal_time']:.1f} ms")

def main():
    parser = argparse.ArgumentParser(description='Plot greedy client fairness results')
    parser.add_argument('--input', default='fairness_results.csv', help='Input results file')
    parser.add_argument('--output-dir', default='.', help='Output directory')
    parser.add_argument('--format', choices=['png', 'pdf'], default='png', help='Output format')

    args = parser.parse_args()

    # Load results
    results = load_results(args.input)
    if not results:
        print("No valid results to plot")
        return

    # Calculate statistics
    stats = calculate_statistics(results)
    print(f"Loaded results for {len(stats)} different c values")
    print(f"C values tested: {sorted(stats.keys())}")

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    # Generate plots
    plots_created = []

    # Main fairness ratio plot
    plot_file = output_dir / f'fairness_ratio_plot.{args.format}'
    create_fairness_ratio_plot(stats, plot_file)
    plots_created.append(plot_file)

    # Completion times comparison
    plot_file = output_dir / f'completion_times_plot.{args.format}'
    create_completion_times_plot(stats, plot_file)
    plots_created.append(plot_file)

    # Efficiency analysis
    plot_file = output_dir / f'efficiency_analysis.{args.format}'
    create_efficiency_analysis_plot(stats, plot_file)
    plots_created.append(plot_file)

    # Print detailed analysis
    print_summary_analysis(stats)

    print(f"\n✅ Generated {len(plots_created)} plots:")
    for plot_file in plots_created:
        print(f"   {plot_file}")

    print("\n🎯 Fairness analysis complete!")
    print("Key insights:")
    print("1. Fairness Ratio Plot shows how unfairness scales with greedy requests")
    print("2. Completion Times Plot shows the advantage greedy clients get")  
    print("3. Efficiency Analysis shows how well FCFS enables unfairness")

if __name__ == "__main__":
    main()
