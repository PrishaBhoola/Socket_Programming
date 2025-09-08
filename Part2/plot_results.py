import csv
import matplotlib.pyplot as plt
import numpy as np
import argparse
from pathlib import Path
import json

def load_results(results_file):
    if not Path(results_file).exists():
        print(f"Results file not found: {results_file}")
        return None

    results_by_clients = {}

    with open(results_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            num_clients = int(row['num_clients'])
            avg_time = float(row['avg_completion_time'])
            success_rate = int(row['successful_clients']) / int(row['total_clients'])

            if avg_time > 0:  
                if num_clients not in results_by_clients:
                    results_by_clients[num_clients] = {
                        'times': [], 
                        'success_rates': []
                    }

                results_by_clients[num_clients]['times'].append(avg_time)
                results_by_clients[num_clients]['success_rates'].append(success_rate)

    return results_by_clients

def calculate_statistics(results_by_clients):
    stats = {}

    for num_clients, data in results_by_clients.items():
        times = data['times']
        success_rates = data['success_rates']

        if times:
            stats[num_clients] = {
                'avg_time': np.mean(times),
                'std_time': np.std(times),
                'min_time': np.min(times),
                'max_time': np.max(times),
                'avg_success_rate': np.mean(success_rates),
                'num_samples': len(times)
            }

    return stats

def create_completion_time_plot(stats, output_file='completion_time_plot.png'):
    client_counts = sorted(stats.keys())
    avg_times = [stats[c]['avg_time'] for c in client_counts]
    std_times = [stats[c]['std_time'] for c in client_counts]

    plt.figure(figsize=(12, 8))

    plt.errorbar(client_counts, avg_times, yerr=std_times,
                marker='o', capsize=5, capthick=2, linewidth=2, markersize=8,
                color='blue', label='Average completion time')

    if len(client_counts) >= 3:
        z = np.polyfit(client_counts, avg_times, 2)  
        p = np.poly1d(z)

        x_trend = np.linspace(min(client_counts), max(client_counts), 100)
        y_trend = p(x_trend)

        plt.plot(x_trend, y_trend, '--', alpha=0.7, color='red',
                label=f'Trend (R² = {calculate_r_squared(client_counts, avg_times, p):.3f})')

    plt.xlabel('Number of Concurrent Clients', fontsize=12)
    plt.ylabel('Average File Download Time (ms)', fontsize=12)
    plt.title('Concurrent File Download Performance\nServer Processing: FIFO Request Queue', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.legend()

    # Add value annotations
    for x, y in zip(client_counts, avg_times):
        plt.annotate(f'{y:.0f}ms', (x, y), 
                    textcoords="offset points", xytext=(0,15), ha='center',
                    fontsize=9)

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✅ Saved completion time plot: {output_file}")
    return output_file

def calculate_r_squared(x_data, y_data, poly_func):
    """Calculate R-squared for polynomial fit"""
    y_pred = poly_func(x_data)
    ss_res = np.sum((y_data - y_pred) ** 2)
    ss_tot = np.sum((y_data - np.mean(y_data)) ** 2)
    return 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

def main():
    parser = argparse.ArgumentParser(description='Plot concurrent download experiment results')
    parser.add_argument('--input', default='results.csv', help='Input results file')
    parser.add_argument('--output-dir', default='.', help='Output directory for plots')
    parser.add_argument('--format', choices=['png', 'pdf', 'svg'], default='png',
                       help='Output format')

    args = parser.parse_args()

    results = load_results(args.input)
    if not results:
        print("No valid results to plot")
        return

    stats = calculate_statistics(results)
    if not stats:
        print("No statistics to calculate")
        return

    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    plots_created = []

    plot_file = output_dir / f'completion_time_plot.{args.format}'
    create_completion_time_plot(stats, plot_file)
    plots_created.append(plot_file)

if __name__ == "__main__":
    main()
