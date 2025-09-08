#!/usr/bin/env python3
"""
Single experiment runner for Greedy Client FCFS Analysis (Part 3)
Runs one experiment with specified parameters
"""

import subprocess
import sys
import time
import json
import os
from pathlib import Path
import argparse

def load_config(config_file='config.json'):
    """Load experiment configuration"""
    try:
        with Path(config_file).open() as f:
            return json.load(f)
    except Exception as e:
        print("Error loading config: {}".format(e))
        return {}

def create_default_config():
    """Create default configuration"""
    config = {
        "server_ip": "10.0.0.100",
        "port": 8887,
        "num_clients": 10,
        "c": 10,
        "p": 0,
        "k": 5
    }

    with open('config.json', 'w') as f:
        json.dump(config, f, indent=2)

    print("Created default config.json")
    return config

def create_words_file():
    """Create words file for testing"""
    if not Path('words.txt').exists():
        words = []
        for i in range(100):  # 100 words for testing
            words.append("word_{:03d}".format(i))

        content = ','.join(words)
        with open('words.txt', 'w') as f:
            f.write(content)

        print("Created words.txt with {} words".format(len(words)))

def setup_experiment_files(net):
    """Copy files to network hosts"""
    print("Setting up experiment files...")

    files = ['server.py', 'client.py', 'config.json', 'words.txt']

    # Setup server
    server = net.get('server')
    server.cmd('mkdir -p /tmp/experiment')
    for filename in files:
        if Path(filename).exists():
            server.cmd('cp {} /tmp/experiment/'.format(filename))

    # Setup clients
    for host in net.hosts:
        if host.name.startswith('client'):
            host.cmd('mkdir -p /tmp/experiment')
            for filename in ['client.py', 'config.json']:
                if Path(filename).exists():
                    host.cmd('cp {} /tmp/experiment/'.format(filename))

def start_server(net):
    """Start the server"""
    print("Starting FCFS server...")
    server = net.get('server')

    server.cmd('cd /tmp/experiment && python3 server.py > server.log 2>&1 &')
    time.sleep(3)

    # Check if server started
    result = server.cmd('ps aux | grep "python3 server.py" | grep -v grep')
    if result.strip():
        print("✅ Server started successfully")
        return True
    else:
        print("❌ Server failed to start")
        log = server.cmd('cat /tmp/experiment/server.log 2>/dev/null || echo "No log"')
        print("Server log: {}".format(log))
        return False

def stop_server(net):
    """Stop the server"""
    server = net.get('server')
    server.cmd('pkill -f "python3 server.py"')

def run_greedy_experiment(net, num_clients, c_value, greedy_client_id=1):
    """Run greedy client fairness experiment"""
    print("Running greedy experiment:")
    print("  Total clients: {}".format(num_clients))
    print("  Greedy client: client{} (c={} requests)".format(greedy_client_id, c_value))
    print("  Normal clients: {} clients (1 request each)".format(num_clients-1))

    results = {}

    # Start all clients
    for i in range(1, num_clients + 1):
        client = net.get('client{}'.format(i))
        if not client:
            continue

        if i == greedy_client_id:
            # Greedy client
            cmd = 'cd /tmp/experiment && python3 client.py --client-id client{} --greedy --c {} --quiet > client{}_result.txt 2>&1 &'.format(
                i, c_value, i)
        else:
            # Normal client
            cmd = 'cd /tmp/experiment && python3 client.py --client-id client{} --quiet > client{}_result.txt 2>&1 &'.format(i, i)

        client.cmd(cmd)
        behavior = 'GREEDY' if i == greedy_client_id else 'NORMAL'
        print("  Started client{} ({})".format(i, behavior))

    # Wait for completion
    print("Waiting for all clients to complete...")
    max_wait = 120
    elapsed = 0

    while elapsed < max_wait:
        all_done = True
        for i in range(1, num_clients + 1):
            client = net.get('client{}'.format(i))
            if client:
                result = client.cmd('ps aux | grep "python3 client.py" | grep -v grep')
                if result.strip():
                    all_done = False
                    break

        if all_done:
            print("✅ All clients completed")
            break

        time.sleep(2)
        elapsed += 2

        if elapsed % 10 == 0:
            print("  Still waiting... ({}s elapsed)".format(elapsed))

    # Collect results
    print("\nCollecting results...")

    for i in range(1, num_clients + 1):
        client = net.get('client{}'.format(i))
        if client:
            output = client.cmd('cat /tmp/experiment/client{}_result.txt 2>/dev/null || echo "No output"'.format(i))

            if "ELAPSED_MS:" in output:
                try:
                    # Parse: ELAPSED_MS:123.45:TYPE:GREEDY:REQUESTS:10
                    parts = output.strip().split(':')
                    elapsed_ms = float(parts[1])
                    client_type = parts[3] if len(parts) > 3 else "NORMAL"
                    requests = int(parts[5]) if len(parts) > 5 else 1

                    results['client{}'.format(i)] = {
                        'completion_time': elapsed_ms,
                        'type': client_type,
                        'requests': requests
                    }

                    print("  client{}: {:.3f} ms ({}, {} req)".format(i, elapsed_ms, client_type, requests))

                except Exception as e:
                    print("  client{}: Failed to parse - {}".format(i, e))
            else:
                print("  client{}: No completion time found".format(i))

    return results

def analyze_fairness(results, c_value):
    """Analyze fairness of results"""
    if not results:
        return None

    greedy_results = [r for r in results.values() if r['type'] == 'GREEDY']
    normal_results = [r for r in results.values() if r['type'] == 'NORMAL']

    analysis = {
        'total_clients': len(results),
        'greedy_clients': len(greedy_results),
        'normal_clients': len(normal_results),
        'c_value': c_value
    }

    if greedy_results:
        greedy_time = greedy_results[0]['completion_time']
        analysis['greedy_completion_time'] = greedy_time

    if normal_results:
        normal_times = [r['completion_time'] for r in normal_results]
        analysis['normal_avg_time'] = sum(normal_times) / len(normal_times)
        analysis['normal_min_time'] = min(normal_times)
        analysis['normal_max_time'] = max(normal_times)

    # Calculate fairness metrics
    if greedy_results and normal_results:
        greedy_time = analysis['greedy_completion_time']
        normal_avg = analysis['normal_avg_time']

        # Fairness ratio: how much longer normal clients take vs greedy
        if greedy_time > 0:
            analysis['fairness_ratio'] = normal_avg / greedy_time
        else:
            analysis['fairness_ratio'] = float('inf')

        # Expected ratio based on requests (greedy gets c requests vs 1 for normal)
        analysis['expected_requests_ratio'] = c_value

        # Efficiency: actual fairness ratio vs expected
        if analysis['expected_requests_ratio'] > 0:
            analysis['efficiency_ratio'] = analysis['fairness_ratio'] / analysis['expected_requests_ratio']
        else:
            analysis['efficiency_ratio'] = 0

    return analysis

def run_mininet_experiment(num_clients, c_value, greedy_client_id=1, verbose=True):
    """Run complete Mininet experiment"""
    try:
        from mininet.net import Mininet
        from mininet.node import OVSSwitch
        from mininet.link import TCLink
        from mininet.log import setLogLevel
        from topology import GreedyClientTopo

        if not verbose:
            setLogLevel('warning')

        if verbose:
            print("\n=== GREEDY CLIENT FCFS EXPERIMENT ===")
            print("Total clients: {}".format(num_clients))
            print("Greedy client: client{} (c={})".format(greedy_client_id, c_value))
            print("Normal clients: {}".format(num_clients-1))

        # Create network
        topo = GreedyClientTopo(num_clients)
        net = Mininet(topo=topo, switch=OVSSwitch, link=TCLink)
        net.start()

        try:
            setup_experiment_files(net)

            if start_server(net):
                results = run_greedy_experiment(net, num_clients, c_value, greedy_client_id)
                analysis = analyze_fairness(results, c_value)

                if verbose and analysis:
                    print("\n=== FAIRNESS ANALYSIS ===")
                    greedy_time = analysis.get('greedy_completion_time', 0)
                    normal_avg = analysis.get('normal_avg_time', 0)
                    fairness_ratio = analysis.get('fairness_ratio', 0)

                    print("Greedy client time: {:.3f} ms".format(greedy_time))
                    print("Normal clients avg: {:.3f} ms".format(normal_avg))

                    if fairness_ratio > 0:
                        print("Fairness ratio: {:.2f}x".format(fairness_ratio))
                        print("Expected ratio: {}x".format(analysis['expected_requests_ratio']))
                        print("Efficiency: {:.2f}".format(analysis.get('efficiency_ratio', 0)))

                        # Fairness assessment
                        if fairness_ratio > 3.0:
                            print("✅ Strong unfairness detected - greedy client has major advantage")
                        elif fairness_ratio > 1.5:
                            print("⚠️ Moderate unfairness detected")
                        elif fairness_ratio > 1.1:
                            print("📊 Slight unfairness detected")
                        else:
                            print("❓ No significant unfairness detected")

                return results, analysis
            else:
                return {}, None

        finally:
            stop_server(net)
            net.stop()

    except Exception as e:
        print("❌ Experiment failed: {}".format(e))
        import traceback
        traceback.print_exc()
        return {}, None

def main():
    parser = argparse.ArgumentParser(description='Greedy client experiment runner')
    parser.add_argument('--clients', type=int, help='Number of clients')
    parser.add_argument('--c', type=int, help='Requests for greedy client')
    parser.add_argument('--greedy-id', type=int, default=1, help='ID of greedy client')
    parser.add_argument('--quiet', action='store_true', help='Minimal output')
    parser.add_argument('--setup', action='store_true', help='Setup files')

    args = parser.parse_args()

    if args.setup:
        print("Setting up greedy client experiment files...")
        create_default_config()
        create_words_file()
        print("✅ Setup complete")
        return

    # Load config
    config = load_config()
    num_clients = args.clients or config.get('num_clients', 10)
    c_value = args.c or config.get('c', 10)

    # Ensure files exist
    if not Path('config.json').exists():
        create_default_config()
    if not Path('words.txt').exists():
        create_words_file()

    print("Running greedy client fairness experiment...")
    print("Configuration:")
    print("  Number of clients: {}".format(num_clients))
    print("  Greedy client requests (c): {}".format(c_value))
    print("  Greedy client ID: {}".format(args.greedy_id))

    results, analysis = run_mininet_experiment(
        num_clients, c_value, args.greedy_id, not args.quiet
    )

    if results and analysis:
        if args.quiet:
            # Output for experimental suite
            greedy_time = analysis.get('greedy_completion_time', 0)
            normal_avg = analysis.get('normal_avg_time', 0)
            fairness_ratio = analysis.get('fairness_ratio', 0)
            print("SUCCESS:{}:{:.3f}:{:.3f}:{:.3f}".format(len(results), greedy_time, normal_avg, fairness_ratio))
        else:
            print("\n✅ Experiment completed successfully")
            print("Results summary:")
            print("  Total clients: {}".format(len(results)))
            print("  Successful completions: {}".format(len(results)))
            print("SUCCESS:")
            if analysis.get('fairness_ratio', 0) > 0:
                print("  Fairness ratio: {:.2f}x".format(analysis['fairness_ratio']))
    else:
        if args.quiet:
            print("FAILED:0:0:0:0")
        else:
            print("\n❌ Experiment failed")
            print("Troubleshooting:")
            print("  1. Check if all files exist: server.py, client.py, config.json, words.txt")
            print("  2. Verify Mininet is working: sudo mn --test pingall")  
            print("  3. Check server can start: python3 server.py")
            print("  4. Try smaller test: --clients 3 --c 2")
        sys.exit(1)

if __name__ == "__main__":
    main()
