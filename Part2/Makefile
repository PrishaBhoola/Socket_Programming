.PHONY: all setup test single run plot clean help mininet-test

all: help

# Run single experiment with current config (requires sudo)
run:
	@echo "Running single experiment in Mininet..."
	@echo "Note: This requires root privileges for Mininet"
	@sudo python3 runner.py
	@echo "✅ Single experiment complete"

# Run full experimental suite (requires sudo)
plot:
	@echo "Running full experimental suite in Mininet..."
	@echo "Note: This requires root privileges for Mininet"
	@sudo python3 run_experiments.py
	@python3 plot_results.py
	@echo "✅ Experiments complete"

# Clean generated files
clean:
	@echo "Cleaning generated files..."
	@rm -f results.csv *.png *.pdf server.log
	@rm -rf __pycache__
	@sudo mn -c 2>/dev/null || echo "Mininet cleanup completed"
	@echo "✅ Clean complete"

# Clean Mininet state specifically
clean-mininet:
	@echo "Cleaning Mininet state..."
	@sudo mn -c
	@echo "✅ Mininet cleanup complete"

# Dependencies
results.csv:
	@echo "No results found, running experiments..."
	@$(MAKE) run

plot: results.csv
