
import sys,os
from anno import annos

keys = [f[:-16] for f in os.listdir("/mnt/data/raw_data/X-LeBench/simulation_annotation") if f.endswith('_annotation.json')]
if len(sys.argv) > 1:
    keys = keys[int(sys.argv[1])*len(keys)//8: (int(sys.argv[1])+1)*len(keys)//8]
A = annos(
    ALL_NARRATION_PATH="/mnt/data/raw_data/Ego4d/v2/annotations/narration.json",
    in_folder="/mnt/data/raw_data/X-LeBench/simulation_annotation",
    out_folder="/mnt/data/raw_data/X-LeBench/simulation_annotations",#"/home/yl/simulation_annotations", #
    model_path="/mnt/data/models/Qwen3-32B",
    keys=keys)#["simulation_0c4a73fc_570e7f85"])
A.run()