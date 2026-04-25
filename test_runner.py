#!/usr/bin/env python
"""
Test runner script for LocalKaam project.
Run tests with: python test_runner.py
"""

import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner

if __name__ == "__main__":
    os.environ["DJANGO_SETTINGS_MODULE"] = "LOCALKAAM.test_settings"
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(["accounts"])
    sys.exit(bool(failures))
