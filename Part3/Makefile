# Makefile for Greedy Client FCFS Fairness Analysis (Part 3)

.PHONY: all setup run-fcfs run plot clean help

# Default target
all: help

# Install required Python packages
setup:
	@echo "--- Installing required Python packages (numpy, matplotlib) ---"
	pip3 install numpy matplotlib
	@echo "--- Setup complete ---"

# Run a single FCFS experiment with parameters from config.json
run-fcfs:
	@echo "--- Running single FCFS fairness experiment (requires sudo) ---"
	sudo python3 runner.py
	@echo "--- Single run complete ---"

# Run the full experimental suite for varying 'c' values
run:
	@echo "--- Running full greedy client fairness experiments (requires sudo) ---"
	sudo python3 run_experiments.py
	@echo "--- Experimental suite complete. Results are in fairness_results.csv ---"

# Generate fairness analysis plots from the results of the full suite
# This depends on 'run' to ensure the data file exists.
plot: run
	@echo "--- Generating fairness plot from results ---"
	python3 plot.py
	@echo "--- Plotting complete ---"

# Clean generated files and Mininet state
clean:
	@echo "--- Cleaning generated files and Mininet state ---"
	rm -f fairness_results.csv *.png *.pdf server.log client*.log
	rm -rf __pycache__
	sudo mn -c
	@echo "--- Clean complete ---"

# Help message
help:
	@echo "Greedy Client FCFS Fairness Analysis (Part 3) Makefile"
	@echo ""
	@echo "This Makefile orchestrates the experiment as required by the assignment."
	@echo ""
	@echo "Main Targets:"
	@echo "  make setup      - Installs required Python packages (run this first!)."
	@echo "  make run-fcfs   - Runs ONE experiment using the parameters in config.json."
	@echo "  make plot       - Runs the FULL experiment suite for c=1..10 and then generates p3_plot.png."
	@echo ""
	@echo "Other Targets:"
	@echo "  make run        - Runs the full experiment suite without plotting."
	@echo "  make clean      - Removes all generated files and cleans up Mininet."
	@echo ""
	@echo "Recommended Workflow:"
	@echo "  1. Run 'make setup' to install dependencies."
	@echo "  2. Edit config.json for a single test run."
	@echo "  3. Run 'make run-fcfs' to test."
	@echo "  4. To generate the final plot for the report, simply run 'make plot'."

