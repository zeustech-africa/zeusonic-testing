#!/usr/bin/env python3
"""Simple health check script for Zeusonic backend.

Usage:
  python3 scripts/health_check.py --url http://127.0.0.1:8000/api/v1/health
"""
import argparse
import json
import sys
from urllib.request import urlopen, Request

parser = argparse.ArgumentParser()
parser.add_argument("--url", default="http://127.0.0.1:8000/api/v1/health")
args = parser.parse_args()

req = Request(args.url)
try:
    with urlopen(req, timeout=5) as r:
        body = r.read().decode('utf-8')
        data = json.loads(body)
        print(json.dumps(data, indent=2))
        if data.get('status') == 'ok' and data.get('db') == 'ok' and data.get('storage') == 'ok':
            sys.exit(0)
        else:
            sys.exit(2)
except Exception as e:
    print('error:', e)
    sys.exit(1)
