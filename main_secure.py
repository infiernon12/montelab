"""
MonteLab - Secure Entry Point
This is the main entry point that launches the compiled main_start module
"""

import sys

if __name__ == "__main__":
    try:
        # Import and run the compiled main_start module
        from main_start import main
        sys.exit(main())
    except Exception as e:
        print(f"Critical error: {e}")
        sys.exit(1)
