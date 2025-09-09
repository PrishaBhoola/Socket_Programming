import csv
import matplotlib.pyplot as plt
import numpy as np
import argparse
from pathlib import Path
from collections import defaultdict
import scipy.stats as st

def load_and_aggregate_results(results_file):
    """
    Loads the results from the CSV and aggregates them by the 'c' value.
    """
    if not Path(results_file).exists():
        print(f"ERROR: Results file not found at '{results_file}'.")
        print("Please run the experiments first using 'sudo make run'")
        return None

    results_by_c = defaultdict(lambda: {'jains_indices': []})

    with open(results_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                c_value = int(row['c_value'])
                jains_index = float(row['jains_index'])
                results_by_c[c_value]['jains_indices'].append(jains_index)
            except (ValueError, KeyError) as e:
                print(f"Skipping malformed row in CSV: {row}. Error: {e}")
    
    return results_by_c

def calculate_statistics(aggregated_results):
    """
    Calculates the mean and 95% confidence interval for each 'c' value.
    """
    stats = {}
    for c_value, data in aggregated_results.items():
        jains_indices = data['jains_indices']
        
        if len(jains_indices) < 2:
            mean = np.mean(jains_indices) if jains_indices else 0
            y_error = 0
        else:
            mean = np.mean(jains_indices)
            conf_interval = st.t.interval(0.95, len(jains_indices)-1, loc=mean, scale=st.sem(jains_indices))
            y_error = (conf_interval[1] - conf_interval[0]) / 2
        
        stats[c_value] = {'mean_jfi': mean, 'y_error': y_error}
    return stats

def create_jains_fairness_plot(stats, output_file='p3_plot.png'):
    """
    Generates and saves the plot for Jain's Fairness Index vs. 'c'.
    """
    if not stats:
        print("No statistics to plot.")
        return

    sorted_c = sorted(stats.keys())
    mean_jfi = [stats[c]['mean_jfi'] for c in sorted_c]
    y_error = [stats[c]['y_error'] for c in sorted_c]

    plt.style.use('seaborn-v0_8-whitegrid')
    plt.figure(figsize=(10, 6))

    plt.errorbar(sorted_c, mean_jfi, yerr=y_error, fmt='-o',
                 capsize=5, capthick=2, elinewidth=2, markeredgewidth=2,
                 label="Jain's Fairness Index (JFI) with 95% CI")

    plt.axhline(y=1.0, color='green', linestyle='--', label='Perfect Fairness (JFI = 1.0)')
    plt.axhline(y=0.5, color='orange', linestyle=':', label='Fairness Threshold')

    plt.title("Fairness Analysis: Impact of a Greedy Client on FCFS", fontsize=16)
    plt.xlabel("Greediness Factor 'c' (Requests per Turn)", fontsize=12)
    plt.ylabel("Jain's Fairness Index (JFI)", fontsize=12)
    plt.xticks(sorted_c)
    plt.ylim(0, 1.1)
    plt.legend(fontsize=10)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    print(f"✅ Plot saved successfully to '{output_file}'")

def main():
    parser = argparse.ArgumentParser(description="Plot results for Greedy Client FCFS analysis")
    parser.add_argument('--input', default='fairness_results.csv', help="Input CSV file")
    parser.add_argument('--output', default='p3_plot.png', help="Output plot file")
    args = parser.parse_args()

    aggregated_results = load_and_aggregate_results(args.input)
    if aggregated_results:
        statistics = calculate_statistics(aggregated_results)
        create_jains_fairness_plot(statistics, args.output)

if __name__ == "__main__":
    main()

