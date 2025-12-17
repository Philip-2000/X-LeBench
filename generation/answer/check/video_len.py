import sys 
sys.path.append(".") 
sys.path.append("..") 
import script
import json, os, tqdm
from pathlib import Path
FULL_SCALE_DIR = Path(script.v_folder) #Path('/mnt/data/raw_data/Ego4d/v2/full_scale')
UIDS = Path(os.path.dirname(__file__)) / 'video_uids.txt'
LENS = {}

def sec2hhmmss(total_sec: int) -> str:
    """Convert total seconds to 'HH:MM:SS' string."""
    hours = total_sec // 3600
    minutes = (total_sec % 3600) // 60
    seconds = total_sec % 60
    return f"{hours:02}:{minutes:02}:{seconds:02}"

for uid in tqdm.tqdm(open(UIDS, 'r').read().splitlines()):
    video_path = FULL_SCALE_DIR / f"{uid}.mp4"
    from decord import VideoReader, cpu
    vr = VideoReader(str(video_path), ctx=cpu(0))
    video_len = len(vr)
    fps = vr.get_avg_fps()
    duration_sec = int(video_len / fps)
    LENS[uid] = sec2hhmmss(duration_sec)
    
LEN_JSON = Path(os.path.dirname(__file__)) / 'video_len.json'
with open(LEN_JSON, 'w', encoding='utf-8') as f:
    json.dump(LENS, f, ensure_ascii=False, indent=2)