"""Send a saved replay request to the local API without disclosing the key."""
import argparse
import json
import os
from pathlib import Path
import httpx

parser=argparse.ArgumentParser()
parser.add_argument('--sample',default='artifacts/sample_fraud.json',type=Path)
parser.add_argument('--url',default='http://127.0.0.1:8000')
args=parser.parse_args()
key=os.environ['FRAUDSHIELD_API_KEY']
result=httpx.post(args.url+'/v1/score',json=json.loads(args.sample.read_text()),
    headers={'Authorization':'Bearer '+key},timeout=15,trust_env=False)
result.raise_for_status()
print(json.dumps(result.json(),indent=2))
