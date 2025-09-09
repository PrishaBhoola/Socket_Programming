import csv
import matplotlib.pyplot as plt
import statistics
from pathlib import Path

def plot_results():
    results_file = Path("results.csv")

    if not results_file.exists():
        print("Error: results.csv not found")
        return False

    k_data = {}
    with results_file.open('r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            k = int(row['k'])
            elapsed_ms = float(row['elapsed_ms'])

            if k not in k_data:
                k_data[k] = []
            k_data[k].append(elapsed_ms)

    k_values = []
    avg_times = []
    conf_intervals = []

    for k in sorted(k_data.keys()):
        times = k_data[k]
        avg_time = statistics.mean(times)
        std_dev = statistics.stdev(times) if len(times) > 1 else 0
        std_err = std_dev / (len(times) ** 0.5)
        conf_interval = 1.96 * std_err  

        k_values.append(k)
        avg_times.append(avg_time)
        conf_intervals.append(conf_interval)

    plt.figure(figsize=(10, 6))
    plt.errorbar(k_values, avg_times, yerr=conf_intervals,
                marker='o', capsize=5, capthick=2, linewidth=2, markersize=8)

    plt.xlabel('Number of Words Requested (k)')
    plt.ylabel('Average Completion Time (ms)')
    plt.title('Socket Programming Performance Analysis')
    plt.grid(True, alpha=0.3)

    # Add value labels
    for k, avg_time in zip(k_values, avg_times):
        plt.annotate(f'{avg_time:.1f}ms', (k, avg_time), 
                    textcoords="offset points", xytext=(0,10), ha='center')

    plt.tight_layout()
    plt.savefig('p1_plot.png', dpi=300, bbox_inches='tight')

    with open('part1_results.csv', 'w', newline='') as f:
        fieldnames = ['k', 'avg_time', 'std_dev', 'confidence_interval', 'num_samples']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for i, k in enumerate(k_values):
            times = k_data[k]
            writer.writerow({
                'k': k,
                'avg_time': avg_times[i],
                'std_dev': statistics.stdev(times) if len(times) > 1 else 0,
                'confidence_interval': conf_intervals[i],
                'num_samples': len(times)
            })

    return True

if __name__ == "__main__":
    plot_results()