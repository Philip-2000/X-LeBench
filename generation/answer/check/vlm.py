
import sys, tqdm, os, json, traceback
from os.path import join as opj
from pathlib import Path
sys.path.append(".") 
sys.path.append("..") 
import script
OUT_DIR = Path(script.out_folder)
V_DIR = Path(script.v_folder)
CLIP_DIR = Path(script.clip_folder)#
MODEL = "Qwen2.5-VL-7B-Instruct"
from MyLm import call
bar = tqdm.tqdm(total=12027, desc="Processing simulations") #11444+583=12027 #37
cnt=0
def assign_uid_single(sim_json: dict, sim_id: str) -> dict:
    global cnt
    TYPE = "objects_retrieval"
    for qq in sim_json["tasks"][TYPE].get("query_list", []):
        #V = VS[qq["query_metadata"]["video_uid"]]
        #start_time_sec = float(qq["query_metadata"]["query_range"]["start_time"].split(":")[0]) * 3600 + float(qq["query_metadata"]["query_range"]["start_time"].split(":")[1]) * 60
        for q in qq.get("queries", []):
            cnt+=1
            bar.update(1)
            if cnt < 10000: continue
            q["vlm"] = call(MODEL, {"content": [{"text": q["query"]}, {"video":opj(CLIP_DIR, q["query_id"]+".mp4")}], "num_segments":32} )
            
    TYPE = "people_retrieval"
    for qq in sim_json["tasks"][TYPE].get("query_list", []):
        #V = VS[qq["query_metadata"]["video_uid"]]
        #start_time_sec = float(qq["query_metadata"]["query_range"]["start_time"].split(":")[0]) * 3600 + float(qq["query_metadata"]["query_range"]["start_time"].split(":")[1]) * 60
        for q in qq.get("queries", []):
            cnt+=1
            bar.update(1)
            if cnt < 10000: continue
            q["vlm"] = call(MODEL, {"content": [{"text": q["query"]}, {"video":opj(CLIP_DIR, q["query_id"]+".mp4")}], "num_segments":32} )
            
    return sim_json  # Placeholder for actual implementation

def main():
    sim_files = [f for f in os.listdir(script.out_folder) if f.endswith('_annotations.json')]
    for sf in (sim_files):
        sim_id = sf[len("simulation_"):-len("_annotations.json")]
        sim_path = Path(script.out_folder) / sf
        try:
            with open(sim_path, 'r', encoding='utf-8') as f:
                sim_json = json.load(f)
            sim_json = assign_uid_single(sim_json, sim_id)
            out_path = OUT_DIR / sf
            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump(sim_json, f, indent=4) #        break
        except Exception as e:
            print(f"Failed to process with {sim_path}: {e}")
    #print("UID assignment report:", report) #{'objects_retrieval': 11444, 'summarisation': 432, 'counting': 5295, 'summary_ordering': 432, 'people_retrieval': 583}

if __name__ == "__main__":
    main()