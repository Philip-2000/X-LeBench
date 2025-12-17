import json
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plot
OUT = os.path.join(os.path.dirname(__file__),'pie.png')

labels = ['0 descriptions', '1 description', '2 descriptions', '3 descriptions', '4 descriptions', '5 descriptions']
sizes = [2065, 1709, 2890, 1279, 786, 3298]
#对于共12027个问题，有2065个其时间范围内找不到叙述标注, 有1709个找到1条叙述标注, 有2890个找到2条, 1279个找到3条, 786个找到4条, 3298个找到5条
colors = ['lightcoral', 'gold', 'lightskyblue', 'lightgreen', 'orange', 'violet']
explode = (0.1, 0, 0, 0, 0, 0)  # only "explode" the 1st slice
plot.figure(figsize=(8, 6))
plot.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%',
        shadow=True, startangle=140)
plot.title('Distribution of Description Presence in X-LeBench Questions')
plot.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
plot.savefig(OUT)