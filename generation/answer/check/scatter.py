#!/usr/bin/env python3
import json
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

IN = os.path.join(os.path.dirname(__file__),'report.json')
OUT = os.path.join(os.path.dirname(__file__),'scatter.png')

with open(IN, 'r') as f:
    data = json.load(f)

per = data.get('per_file', [])
xs = []
ys = []
skipped = 0
for itm in per:
    # build lowercase->orig key map
    km = {k.lower(): k for k in itm.keys()}
    full_k = km.get('full_second') or km.get('fullsecond') or km.get('full_second')
    dense_k = km.get('dense_second') or km.get('densesecond') or km.get('dence_second') or km.get('dencesecond')
    if not full_k or not dense_k:
        skipped += 1
        continue
    fx = itm.get(full_k)
    dy = itm.get(dense_k)
    try:
        x = int(fx)
        y = int(dy)
    except Exception:
        skipped += 1
        continue
    xs.append(x)
    ys.append(y)

print(f'Found {len(xs)} points, skipped {skipped} entries')
if len(xs) == 0:
    raise SystemExit('No data points to plot')

plt.figure(figsize=(8,6))
plt.scatter(xs, ys, s=10, alpha=0.6)
plt.xlabel('full_second')
plt.ylabel('dense_second')
plt.xlim(0, 75000)
plt.ylim(0, 75000)
#draw x=y line
plt.plot([0, 75000], [0, 75000], color='red', linestyle='--', linewidth=1, label='y=x')
plt.title('full_second vs dense_second (per_file)')
plt.grid(True, linestyle=':', alpha=0.4)

# annotate some stats
import statistics
try:
    mx = max(xs)
    my = max(ys)
    medx = int(statistics.median(xs))
    medy = int(statistics.median(ys))
    stats_txt = f"n={len(xs)}\nmax_full={mx}\nmax_dense={my}\nmedian_full={medx}\nmedian_dense={medy}"
    plt.annotate(stats_txt, xy=(0.02, 0.98), xycoords='axes fraction', ha='left', va='top', fontsize=18,
                 bbox=dict(boxstyle='round', fc='white', alpha=0.7))
except Exception:
    pass

os.makedirs(os.path.dirname(OUT), exist_ok=True)
plt.tight_layout()
plt.savefig(OUT, dpi=150)
print('Saved scatter to', OUT)
