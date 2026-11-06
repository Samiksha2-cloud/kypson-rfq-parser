import json
import sys
import time
from parse import parse_rfq

FIELDS = ["category", "quantity", "unit", "gsm", "micron", "location"]

def main(path):
    total = 0
    exact = 0
    field_ok = {f: 0 for f in FIELDS}
    start = time.time()

    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            got = parse_rfq(item["text"])
            exp = item["expected"]
            total += 1

            wrong = [k for k in FIELDS if got.get(k) != exp.get(k)]
            for k in FIELDS:
                if k not in wrong:
                    field_ok[k] += 1
            if not wrong:
                exact += 1
            else:
                print("WRONG:", item["text"])
                for k in wrong:
                    print(f"   {k}: expected {exp.get(k)!r}, got {got.get(k)!r}")

    print()
    print(f"Exact match: {exact}/{total}")
    for k in FIELDS:
        print(f"  {k}: {field_ok[k]}/{total}")
    print(f"Time: {time.time() - start:.2f}s")

if __name__ == "__main__":
    main(sys.argv[1])