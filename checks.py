"""
================================================================================
    WEB-BASED E-LEARNING SYSTEM - SYSTEM CHECKS MODULE
================================================================================

Institution: West Prime Horizon Institute Inc.
Program: Bachelor of Science in Information Technology
Location: Zamboanga Del Sur

Project Title: E-Learning System
Adviser: RANDY L. CAÑETE

Date: February 07, 2026
Version: MVP (Minimum Viable Product)

================================================================================
DESCRIPTION:
    This module performs basic system integrity checks on startup.
    
    Verifies:
    - Required project files and folders exist
    - Python code compiles correctly
    - System is ready for deployment

================================================================================
"""

import os
import sys

BASE = os.path.dirname(__file__)
REQUIRED = ['app.py', 'schema.sql', 'templates', 'static/css/styles.css']
missing = [p for p in REQUIRED if not os.path.exists(os.path.join(BASE, p))]
if missing:
    print('Missing files or folders:', missing)
    sys.exit(2)

print('✓ Basic project files present')

# ============================================================================
# CODE COMPILATION CHECK
# ============================================================================

# attempt to compile app
try:
    import py_compile
    py_compile.compile(os.path.join(BASE, 'app.py'), doraise=True)
    print('✓ app.py compiles successfully')
except Exception as e:
    print('✗ app.py compile error:', e)
    sys.exit(3)

print('✓ All checks passed')
