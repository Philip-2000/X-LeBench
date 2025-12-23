
import sys, tqdm, os, json, traceback
from pathlib import Path
sys.path.append(".") 
sys.path.append("..") 
import script
OUT_DIR = Path(script.out_folder)
V_DIR = Path(script.v_folder)
CLIP_DIR = Path(script.clip_folder)#

GLOBAL_CNT=0
report = {}

bar = tqdm.tqdm(total=12027, desc="Clipping videos") #11444+583=12027 #37
def GLOBAL_UID_FORM(TYPE, SIM_ID):
    global GLOBAL_CNT
    uid = f"{GLOBAL_CNT:05d}_{TYPE}_{SIM_ID}"
    GLOBAL_CNT += 1
    report[TYPE] = report.get(TYPE, 0) + 1
    return uid

def load(video_uid):
    video_path = V_DIR / f"{video_uid}.mp4"
    # Return the video file path. We'll use PyAV (av) to read/clip instead
    #print(f"Using video path: {video_path}")
    return str(video_path)

def clip(vr, start_s, end_s):
    # Deprecated: `save` now performs clipping with PyAV directly.
    # Keep this function for compatibility but return None.
    return None

def save(vr, start_s, end_s, query_id):
    """Clip `vr` (a path string returned by `load`) between `start_s` and `end_s` seconds and save to `CLIP_DIR/query_id.mp4`.

    Uses PyAV (av) for decoding and encoding. If PyAV is not available, falls back to calling ffmpeg CLI.
    Returns the output path string or None when the clip is empty/invalid.
    """
    if start_s is None or end_s is None or end_s <= start_s:
        return None
    # vr is expected to be a path string
    video_path = Path(vr)
    if not video_path.exists():
        return None
    out_path = CLIP_DIR / f"{query_id}.mp4"

    import subprocess
    cmd = [
        'ffmpeg', '-y', '-ss', str(start_s), '-to', str(end_s), '-i', str(video_path),
        '-c:v', 'mpeg4', '-vf', 'scale=1080:-2:flags=lanczos', '-crf', '23', '-c:a', 'aac', '-b:a', '128k', str(out_path)
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"ffmpeg clipping failed for out_path: {out_path}", e)
        traceback.print_exc()
    return str(out_path)
    #ffmpeg -y -ss 0 -to 10 -i /mnt/data/raw_data/Ego4d/v2/full_scale/c645ddf0-1efc-4c0a-bf58-889ea519b254.mp4 -c:v mpeg4 -vf "scale=1080:-2:flags=lanczos" -crf 23 -c:a aac -b:a 128k ./clip.mp4

    # try:
    #     import av
    #     # open input
    #     container = av.open(str(video_path))
    #     try:
    #         video_stream = next(s for s in container.streams if s.type == 'video')
    #     except StopIteration:
    #         container.close()
    #         return None

    #     # derive fps/size
    #     try:
    #         fps = int(video_stream.average_rate) if video_stream.average_rate else 25
    #     except Exception:
    #         fps = 25
    #     width = video_stream.codec_context.width
    #     height = video_stream.codec_context.height

    #     output = av.open(str(out_path), mode='w')
    #     out_stream = output.add_stream('libx264', rate=fps)
    #     out_stream.width = width
    #     out_stream.height = height
    #     out_stream.pix_fmt = 'yuv420p'

    #     # seek to start (timestamp in microseconds)
    #     try:
    #         container.seek(int(start_s * 1e6), any_frame=False, backward=True, stream=video_stream)
    #     except Exception:
    #         # ignore seek failures, we'll skip frames until we hit start_s
    #         pass

    #     done = False
    #     for packet in container.demux(video_stream):
    #         for frame in packet.decode():
    #             if frame.pts is None:
    #                 continue
    #             t = float(frame.pts * frame.time_base)
    #             if t + 1e-6 < start_s:
    #                 continue
    #             if t >= end_s:
    #                 done = True
    #                 break
    #             # ensure frame format; encoding will handle conversion
    #             for packet_out in out_stream.encode(frame):
    #                 output.mux(packet_out)
    #         if done:
    #             break

    #     # flush encoder
    #     for packet_out in out_stream.encode():
    #         output.mux(packet_out)
    #     output.close()
    #     container.close()
    #     print(f"Clipped video saved to: {out_path}")
    #     return str(out_path)

    # except Exception as e:
    #     # Fallback to ffmpeg CLI if av isn't available or encoding fails
    #     print(f"PyAV clipping failed ({e}), falling back to ffmpeg CLI.")
    #     traceback.print_exc()
    #     import subprocess
    #     cmd = [
    #         'ffmpeg', '-y', '-ss', str(start_s), '-to', str(end_s), '-i', str(video_path),
    #         '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '23', '-c:a', 'aac', '-b:a', '128k', str(out_path)
    #     ]
    #     try:
    #         subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    #         print(f"Clipped video saved to: {out_path}")
    #         return str(out_path)
    #     except Exception as e:
    #         print(f"ffmpeg clipping failed for video: {video_path}", e)
    #         #traceback.print_exc()
    #         return None
    

def assign_uid_single(sim_json: dict, sim_id: str) -> dict:
    class vs:
        def __init__(self):
            self.Vs = {}
        def __getitem__(self, uid):
            if uid not in self.Vs: self.Vs[uid] = load(uid)
            return self.Vs[uid]
        def __del__(self):
            for v in self.Vs.values():
                del v
    VS = vs()
    global bar
    TYPE = "objects_retrieval"
    for qq in sim_json["tasks"][TYPE].get("query_list", []):
        V = VS[qq["query_metadata"]["video_uid"]]
        start_time_sec = float(qq["query_metadata"]["query_range"]["start_time"].split(":")[0]) * 3600 + float(qq["query_metadata"]["query_range"]["start_time"].split(":")[1]) * 60
        for q in qq.get("queries", []):
            q["query_id"] = GLOBAL_UID_FORM(TYPE, sim_id)
            save(V, q["response_start_time_sec"] - start_time_sec, q["response_end_time_sec"]-start_time_sec, q["query_id"])
            bar.update(1)

    TYPE = "people_retrieval"
    for qq in sim_json["tasks"][TYPE].get("query_list", []):
        V = VS[qq["query_metadata"]["video_uid"]]
        start_time_sec = float(qq["query_metadata"]["query_range"]["start_time"].split(":")[0]) * 3600 + float(qq["query_metadata"]["query_range"]["start_time"].split(":")[1]) * 60
        for q in qq.get("queries", []):
            q["query_id"] = GLOBAL_UID_FORM(TYPE, sim_id)
            save(V, q["response_start_time_sec"] - start_time_sec, q["response_end_time_sec"]-start_time_sec, q["query_id"])
            bar.update(1)

    TYPE = "action_retrieval"
    for qq in sim_json["tasks"][TYPE].get("moment_localisation", {}).get("query_list", []):
        for q in qq.get("queries", []):
            q["query_id"] = GLOBAL_UID_FORM(TYPE, sim_id)
        
    TYPE = "summarisation"
    sim_json["tasks"][TYPE]["query_id"] = GLOBAL_UID_FORM(TYPE, sim_id)

    TYPE = "counting"
    for qq in sim_json["tasks"].get(TYPE, []):
        for q in qq.get("verb_noun_pairs", []):
            q["query_id"] = GLOBAL_UID_FORM(TYPE, sim_id)

    TYPE = "summary_ordering"
    sim_json["tasks"][TYPE]["query_id"] = GLOBAL_UID_FORM(TYPE, sim_id)

    del VS # life circle management
    return sim_json  # Placeholder for actual implementation

def main():
    sim_files = [f for f in os.listdir(script.out_folder) if f.endswith('_annotations.json')]
    for sf in (sim_files):
        sim_id = sf[len("simulation_"):-len("_annotations.json")]
        sim_path = Path(script.out_folder) / sf
        try:
            with open(sim_path, 'r', encoding='utf-8') as f:
                sim_json = json.load(f)
        except Exception as e:
            print(f"Failed to load {sim_path}: {e}")
            continue
        sim_json = assign_uid_single(sim_json, sim_id)
        out_path = OUT_DIR / sf
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(sim_json, f, indent=4)
        #break
    print("UID assignment report:", report) #{'objects_retrieval': 11444, 'summarisation': 432, 'counting': 5295, 'summary_ordering': 432, 'people_retrieval': 583}

if __name__ == "__main__":
    main()