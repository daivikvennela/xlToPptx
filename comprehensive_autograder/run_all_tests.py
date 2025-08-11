#!/usr/bin/env python3
"""
Quick test runner for comprehensive lease population autograder
"""

import subprocess
import sys
import os

def run_autograder():
    """Run the comprehensive autograder"""
    print("🚀 Running Comprehensive Lease Population Autograder...")
    print("=" * 60)
    
    try:
        # Run the main autograder
        result = subprocess.run([
            sys.executable, 
            os.path.join(os.path.dirname(__file__), 'autograder.py')
        ], capture_output=True, text=True)
        
        # Print output
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        # Return exit code
        return result.returncode
        
    except Exception as e:
        print(f"Error running autograder: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = run_autograder()
    print(f"\n✅ Autograder completed with exit code: {exit_code}")
    sys.exit(exit_code)