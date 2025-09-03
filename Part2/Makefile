# Makefile for concurrent client-server experiment

# Python interpreter
PYTHON = python3

# Configuration file
CONFIG_FILE = config.json

.PHONY: all clean run plot setup kill-server check-config

all: setup run

# Setup: create necessary files and check configuration
setup: check-config words.txt plot_results.py run_experiments.py

check-config:
	@if [ ! -f $(CONFIG_FILE) ]; then \
		echo "Error: $(CONFIG_FILE) not found!"; \
		echo "Required keys: server_ip, server_port, p, k, filename, num_clients, num_repetitions"; \
		exit 1; \
	fi
	@$(PYTHON) -c "import json; config=json.load(open('config.json')); required=['server_ip','server_port','p','k','filename','num_clients','num_repetitions']; missing=[k for k in required if k not in config]; print('Missing keys:', missing) if missing else print('All required keys present ✓'); exit(1 if missing else 0)"

words.txt: check-config
	@$(PYTHON) -c "import json; config=json.load(open('config.json')); print(','.join([f'word{i}' for i in range(1000)]))" > $$($(PYTHON) -c "import json; print(json.load(open('config.json'))['filename'])")

# # Kill any existing server processes
# kill-server:
# 	@echo "Killing existing server processes..."
# 	@pkill -f "python.*server.py" 2>/dev/null || true
# 	@sleep 1

# Run single experiment with number of clients from config.json
run: setup kill-server
	@echo "Starting single experiment..."
	@$(PYTHON) -c "import json, subprocess, time, os; \
		config = json.load(open('config.json')); \
		num_clients = config['num_clients']; \
		print(f'Running with {num_clients} clients...'); \
		server = subprocess.Popen(['$(PYTHON)', 'server.py']); \
		time.sleep(2); \
		clients = [subprocess.Popen(['$(PYTHON)', 'client.py']) for _ in range(num_clients)]; \
		[c.wait() for c in clients]; \
		server.terminate(); \
		print('Experiment completed.')"

# Run experiments with varying number of clients and generate plot
PYTHON := python3

plot: setup kill-server
	@echo "Running plotting experiments..."
	@$(PYTHON) run_experiments.py
	@$(PYTHON) plot_results.py

# Clean up generated files (keep config.json as it's provided)
clean:
	@echo "Cleaning up..."
	@rm -f words.txt results.csv plot_results.py run_experiments.py p2_plot.png
	@$(MAKE) kill-server
	@echo "Note: config.json preserved (provided file)"

# Help target
help:
	@echo "Available targets:"
	@echo "  setup     - Check for config.json and create sample data files"
	@echo "  run       - Run single experiment (uses num_clients from config.json)"
	@echo "  plot      - Run experiments with varying clients and generate plot"
	@echo "  clean     - Remove generated files and kill server (preserves config.json)"
	@echo "  kill-server - Kill any running server processes"
	@echo ""
	@echo "Prerequisites:"
	@echo "  - config.json must be provided with required keys"
	@echo "  - Python packages: pandas, matplotlib"
	@echo ""
	@echo "Examples:"
	@echo "  make run"
	@echo "  make plot"