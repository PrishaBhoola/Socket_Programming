import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys
import os
from scipy import stats

def calculate_confidence_interval(data, confidence=0.95):
    """Calculate confidence interval for the mean."""
    n = len(data)
    mean = np.mean(data)
    sem = stats.sem(data)  # Standard error of the mean
    h = sem * stats.t.ppf((1 + confidence) / 2., n-1)  # t-distribution
    return mean - h, mean + h

def plot_results():
    if not os.path.exists('results.csv'):
        print("Error: results.csv not found.")
        print("Run 'python3 run_experiments.py' first to generate results.")
        sys.exit(1)
    
    try:
        # Read results
        df = pd.read_csv('results.csv')
        
        if df.empty:
            print("Error: results.csv is empty.")
            sys.exit(1)
        
        # Calculate statistics for each client count
        stats_data = []
        for clients in sorted(df['clients'].unique()):
            client_data = df[df['clients'] == clients]['completion_time']
            
            mean_time = client_data.mean()
            std_time = client_data.std()
            min_time = client_data.min()
            max_time = client_data.max()
            
            # Calculate 95% confidence interval
            ci_lower, ci_upper = calculate_confidence_interval(client_data)
            
            stats_data.append({
                'clients': clients,
                'mean': mean_time,
                'std': std_time,
                'min': min_time,
                'max': max_time,
                'ci_lower': ci_lower,
                'ci_upper': ci_upper,
                'count': len(client_data)
            })
        
        stats_df = pd.DataFrame(stats_data)
        
        # Create the plot
        plt.figure(figsize=(12, 8))
        
        # Plot mean with confidence intervals
        plt.errorbar(stats_df['clients'], stats_df['mean'], 
                    yerr=[stats_df['mean'] - stats_df['ci_lower'], 
                          stats_df['ci_upper'] - stats_df['mean']], 
                    marker='o', markersize=8, linewidth=2, capsize=5,
                    label='Mean ± 95% CI', color='blue', capthick=2)
        
        # Plot min-max range as shaded area
        plt.fill_between(stats_df['clients'], stats_df['min'], stats_df['max'], 
                        alpha=0.2, color='lightblue', label='Min-Max Range')
        
        # Plot individual data points
        plt.scatter(df['clients'], df['completion_time'], 
                   alpha=0.6, color='red', s=30, label='Individual Runs')
        
        # Formatting
        plt.xlabel('Number of Concurrent Clients', fontsize=12)
        plt.ylabel('Completion Time (ms)', fontsize=12)
        plt.title('Server Performance vs Number of Concurrent Clients', fontsize=14, pad=20)
        plt.grid(True, alpha=0.3)
        plt.legend(loc='upper left')
        
        # Set x-axis ticks to show all client counts tested
        plt.xticks(sorted(df['clients'].unique()))
        
        # Add statistics box
        repetitions = len(df[df['clients'] == df['clients'].iloc[0]])
        total_experiments = len(df)
        textstr = f"Repetitions per test: {repetitions}\nTotal experiments: {total_experiments}"
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
        plt.text(0.02, 0.98, textstr, transform=plt.gca().transAxes, fontsize=10,
                verticalalignment='top', bbox=props)
        
        plt.tight_layout()
        plt.savefig('p2_plot.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("Plot saved as p2_plot.png")
        
        # Print detailed statistics
        print("\n" + "="*70)
        print("DETAILED PERFORMANCE ANALYSIS")
        print("="*70)
        print(f"{'Clients':<8} {'Mean (ms)':<12} {'Std (ms)':<12} {'95% CI':<20} {'Min (ms)':<10} {'Max (ms)':<10}")
        print("-"*70)
        
        for _, row in stats_df.iterrows():
            clients = int(row['clients'])
            mean_time = row['mean']
            std_time = row['std']
            ci_range = f"[{row['ci_lower']:.1f}, {row['ci_upper']:.1f}]"
            min_time = row['min']
            max_time = row['max']
            
            print(f"{clients:<8} {mean_time:<12.2f} {std_time:<12.2f} {ci_range:<20} {min_time:<10.2f} {max_time:<10.2f}")
        
        # Analysis observations
        print("\n" + "="*70)
        print("OBSERVATIONS")
        print("="*70)
        
        # Check if completion time increases with more clients
        first_mean = stats_df.iloc[0]['mean']
        last_mean = stats_df.iloc[-1]['mean']
        percent_increase = ((last_mean - first_mean) / first_mean) * 100
        
        print(f"• Completion time with 1 client: {first_mean:.2f} ms")
        print(f"• Completion time with {int(stats_df.iloc[-1]['clients'])} clients: {last_mean:.2f} ms")
        print(f"• Overall increase: {percent_increase:+.1f}%")
        
        if percent_increase > 10:
            print("• SIGNIFICANT INCREASE: Completion time increases substantially with more clients")
            print("  This suggests the server processes requests sequentially (first-come-first-serve)")
        elif percent_increase > 0:
            print("• MODERATE INCREASE: Some performance degradation with more clients")
        else:
            print("• NO SIGNIFICANT INCREASE: Performance remains relatively constant")
        
        # Check for linear relationship
        correlation = np.corrcoef(stats_df['clients'], stats_df['mean'])[0, 1]
        print(f"• Correlation between client count and completion time: {correlation:.3f}")
        
        if correlation > 0.8:
            print("  Strong positive correlation - likely sequential processing")
        elif correlation > 0.5:
            print("  Moderate positive correlation - some queuing effects")
        else:
            print("  Weak correlation - good concurrent handling")
            
    except Exception as e:
        print(f"Error generating plot: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    plot_results()