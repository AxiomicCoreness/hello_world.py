#!/usr/bin/env python3
import cmd
import json
import requests
from typing import Dict, Any

class DashboardREPL(cmd.Cmd):
    intro = "Sovereign Engine - 25D Estate Dashboard REPL. Type 'help' for commands."
    prompt = "sovereign-25d> "
    
    grafana_url = "http://localhost:3000"
    prometheus_url = "http://localhost:9090"
    app_main_url = "http://localhost:8001"
    token_server_url = "http://localhost:8089"
    dashboard_uid = "sovereign-engine-25d"
    
    def do_status(self, arg):
        """Check status of all services."""
        print("
SERVICES STATUS - Estate 25D")
        print("="*60)
        services = [
            ("Token Server", self.token_server_url, 8089),
            ("Fuse Stack", self.app_main_url, 8001),
            ("Metrics", self.prometheus_url, 9090),
            ("Grafana", self.grafana_url, 3000)
        ]
        for name, url, port in services:
            try:
                r = requests.get(f"{url}", timeout=2)
                status = "RUNNING" if r.status_code < 500 else "ERROR"
                print(f"  {name:20} {url:40} {status}")
            except: print(f"  {name:20} {url:40} DOWN")
        print("="*60)
    
    def do_metrics(self, arg):
        """Query Prometheus metrics."""
        try:
            r = requests.get(f"{self.prometheus_url}/metrics", timeout=5)
            if r.status_code == 200:
                print("
PROMETHEUS METRICS")
                for line in r.text.split('
'):
                    if 'sovereign' in line.lower() or 'TYPE' in line or 'HELP' in line:
                        print(line)
        except Exception as e:
            print(f"Error: {e}")
    
    def do_grafana(self, arg):
        """Open Grafana dashboard."""
        print(f"Opening: {self.grafana_url}/d/{self.dashboard_uid}")
        try:
            import webbrowser
            webbrowser.open(f"{self.grafana_url}/d/{self.dashboard_uid}")
        except: pass
    
    def do_test(self, arg):
        """Run smoke tests."""
        print("
SMOKE TESTS")
        tests = [
            ("Token Health", f"{self.token_server_url}/oauth/health"),
            ("Fuse Status", f"{self.app_main_url}/status"),
            ("Metrics", f"{self.prometheus_url}/metrics"),
            ("Grafana", f"{self.grafana_url}"),
            ("Mesh/Run", f"{self.app_main_url}/mesh/run?steps=1")
        ]
        passed = 0
        for name, url in tests:
            try:
                r = requests.get(url, timeout=5)
                if r.status_code < 400:
                    print(f"  PASS: {name}")
                    passed += 1
                else:
                    print(f"  FAIL: {name} ({r.status_code})")
            except: print(f"  ERROR: {name}")
        print(f"
Results: {passed}/5 passed")
    
    def do_tectonic(self, arg):
        """Check tectonic convergence."""
        print("
TECTONIC CONVERGENCE")
        print("R: Absolute Mobility (Phase Lock 202.6)")
        print("C: Perfect Contrast (Commutator)")
        print("N: No Decay (Coherence)")
        print("U: Universal Set (Entropy)")
        print("All checks: PASS (simulated)")
    
    def do_seal(self, arg):
        """Display seal information."""
        print("
SEAL: 25D_ESTATE_8366_SEALED")
        print("CERTIFICATE: FLAWLESS_WORKLOAD_IPHONE12_REVELATION")
        print("WITNESS: 8365 -> 8366 - UNBROKEN")
    
    def do_exit(self, arg):
        """Exit REPL."""
        print("
Session ended. Garden continues.")
        return True
    
    def do_quit(self, arg):
        return self.do_exit(arg)
    
    def do_EOF(self, arg):
        print()
        return self.do_exit(arg)

if __name__ == "__main__":
    DashboardREPL().cmdloop()
