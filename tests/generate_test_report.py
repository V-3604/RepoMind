#!/usr/bin/env python3
"""
Test report generator for RepoMind.
This script runs the tests and generates a summary report.
"""

import os
import sys
import subprocess
import json
from datetime import datetime


def run_tests():
    """Run pytest and capture the output."""
    # Run pytest with JSON output
    result = subprocess.run(
        ["python", "-m", "pytest", "tests/", "--json-report", "--json-report-file=tests/report.json"],
        capture_output=True,
        text=True
    )
    
    return result.returncode, result.stdout


def generate_report(exit_code, output):
    """Generate a test report based on pytest output."""
    # Check if report file exists
    if not os.path.exists("tests/report.json"):
        return {
            "success": False,
            "message": "Test report not generated. Make sure pytest-json-report is installed.",
            "timestamp": datetime.now().isoformat(),
            "output": output
        }
    
    # Load report data
    with open("tests/report.json", "r") as f:
        report_data = json.load(f)
    
    # Extract summary
    summary = report_data.get("summary", {})
    
    # Generate report
    report = {
        "success": exit_code == 0,
        "timestamp": datetime.now().isoformat(),
        "total": summary.get("total", 0),
        "passed": summary.get("passed", 0),
        "failed": summary.get("failed", 0),
        "skipped": summary.get("skipped", 0),
        "duration": summary.get("duration", 0),
        "tests": []
    }
    
    # Add individual test results
    for test_id, test_data in report_data.get("tests", {}).items():
        report["tests"].append({
            "name": test_id,
            "outcome": test_data.get("outcome", "unknown"),
            "duration": test_data.get("duration", 0),
            "message": test_data.get("message", "")
        })
    
    return report


def save_report(report):
    """Save the report to a file."""
    # Create reports directory if it doesn't exist
    if not os.path.exists("tests/reports"):
        os.makedirs("tests/reports")
    
    # Generate filename based on timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"tests/reports/test_report_{timestamp}.json"
    
    # Save report
    with open(filename, "w") as f:
        json.dump(report, f, indent=2)
    
    return filename


def print_summary(report):
    """Print a summary of the test results."""
    print("\n" + "=" * 80)
    print(f"RepoMind Test Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print(f"Total tests: {report['total']}")
    print(f"Passed: {report['passed']}")
    print(f"Failed: {report['failed']}")
    print(f"Skipped: {report['skipped']}")
    print(f"Duration: {report['duration']:.2f} seconds")
    print("=" * 80)
    
    # Print failed tests if any
    if report['failed'] > 0:
        print("\nFailed tests:")
        for test in report['tests']:
            if test['outcome'] == 'failed':
                print(f"- {test['name']}")
                print(f"  Error: {test['message']}")
    
    print(f"\nFull report saved to: {report['report_file']}")
    print("=" * 80)


def main():
    """Main function."""
    print("Running tests...")
    exit_code, output = run_tests()
    
    print("Generating report...")
    report = generate_report(exit_code, output)
    
    filename = save_report(report)
    report['report_file'] = filename
    
    print_summary(report)
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main()) 