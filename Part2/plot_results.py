import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys
import os

def plot_results():
	if not os.path.exists('results.csv'):
		print("Error: results.csv not found.")
		sys.exit(1)
	
	try:
		df = pd.read_csv('results.csv')
		stats = df.groupby('clients')['completion_time'].agg(['mean', 'std', 'min', 'max']).reset_index()
		
		plt.figure(figsize=(12, 8))
		plt.errorbar(stats['clients'], stats['mean'], yerr=stats['std'], 
					marker='o', markersize=8, linewidth=2, capsize=5,
					label='Mean ± Std Dev', color='blue')
		plt.fill_between(stats['clients'], stats['min'], stats['max'], 
						alpha=0.3, color='lightblue', label='Min-Max Range')
		plt.scatter(df['clients'], df['completion_time'], 
				   alpha=0.6, color='red', s=30, label='Individual Runs')
		
		plt.xlabel('Number of Concurrent Clients', fontsize=12)
		plt.ylabel('Completion Time (ms)', fontsize=12)
		plt.title('Server Performance vs Number of Concurrent Clients', fontsize=14)
		plt.grid(True, alpha=0.3)
		plt.legend()
		plt.xticks(stats['clients'])
		
		repetitions = len(df[df['clients'] == df['clients'].iloc[0]])
		textstr = f"Repetitions per test: {repetitions}"
		props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
		plt.text(0.02, 0.98, textstr, transform=plt.gca().transAxes, fontsize=10,
				verticalalignment='top', bbox=props)
		
		plt.tight_layout()
		plt.savefig('p2_plot.png', dpi=300, bbox_inches='tight')
		plt.close()
		
		print("Plot saved as p2_plot.png")
		
		print("\nSummary Statistics:")
		print("=" * 50)
		for _, row in stats.iterrows():
			clients = int(row['clients'])
			mean_time = row['mean']
			std_time = row['std']
			print(f"Clients: {clients:2d} | Mean: {mean_time:7.2f}ms | Std: {std_time:6.2f}ms")
			
	except Exception as e:
		print(f"Error generating plot: {e}")
		sys.exit(1)

if __name__ == "__main__":
	plot_results()