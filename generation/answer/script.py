import os
from os.path import dirname, abspath, join as opj
D = opj("/mnt", "data", "raw_data")
all_narration_path = opj(D, "Ego4d", "v2", "annotations", "narration.json")
v_folder = opj(D, "Ego4d", "v2", "full_scale")
in_folder = opj(D, "X-LeBench", "simulation_annotation")
clip_folder = opj(D, "X-LeBench", "video_clips")
out_folder = opj(D, "X-LeBench", "simulation_annotations") #"/home/yl/simulation_annotations"
model_path = opj("/mnt", "data", "models", "Qwen3-32B")

if __name__ == '__main__':
    import sys,os
    from anno import annos

    keys = [f[:-16] for f in os.listdir(in_folder) if f.endswith('_annotation.json')]
    if len(sys.argv) > 1:
        keys = keys[int(sys.argv[1])*len(keys)//8: (int(sys.argv[1])+1)*len(keys)//8]
    A = annos(
        ALL_NARRATION_PATH=all_narration_path,
        in_folder=in_folder,
        out_folder=out_folder,
        model_path=model_path,
        keys=keys)#["simulation_0c4a73fc_570e7f85"]) #
    A.run()
