#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MonteLab - Secure Entry Point
Entry point for compiled/protected version
"""

import sys

if __name__ == "__main__":
    # Import and run main_start
    from main_start import main
    sys.exit(main())
