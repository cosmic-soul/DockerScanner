"""
Test script for the health report feature.
This will directly test the functionality without using the interactive menu.
"""

import sys
import time
from docker_manager.core.health_report import HealthReport

def main():
    # Initialize health report in demo mode
    print("Initializing health report in demo mode...")
    health_report = HealthReport(demo_mode=True)
    
    # Generate and display report
    print("\nGenerating and displaying health report...\n")
    health_report.generate_report()
    
    # Save report to file
    print("\nSaving health report to file...")
    filename = health_report.save_report("test_health_report.json")
    print(f"Report saved to: {filename}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())