import json, os
import csv
from pathlib import Path
import sys 
sys.path.append(".") 
sys.path.append("..") 
import script
SIM_DIR = Path(script.in_folder) #Path('/mnt/data/raw_data/X-LeBench/simulation_annotation')
FULL_SCALE_DIR = Path(script.v_folder) #Path('/mnt/data/raw_data/Ego4d/v2/full_scale')
MANIFEST_CSV = FULL_SCALE_DIR / 'manifest.csv'
REPORT_JSON = Path(os.path.dirname(__file__)) / 'report.json'


def load_manifest_uids(manifest_csv: Path) -> set:
    return set([f[:-4] for f in os.listdir(FULL_SCALE_DIR) if f.endswith('.mp4')])

def hour_min2sec(hm_str: str) -> int:
    """Convert 'HH:MM' string to total seconds."""
    parts = hm_str.split(':')
    if len(parts) != 2:
        return 0
    try:
        hours = int(parts[0])
        minutes = int(parts[1])
        return hours * 3600 + minutes * 60
    except ValueError:
        return 0
    
def sec2hour_min(total_sec: int) -> str:
    """Convert total seconds to 'HH:MM' string."""
    hours = total_sec // 3600
    minutes = (total_sec % 3600) // 60
    return f"{hours:02}:{minutes:02}"

def extract_simulation_uids(json_path: Path) -> list:
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        return []
    sims = data.get('simulations', [])
    result, dur_s = [], []
    for s in sims:
        uid = None
        if isinstance(s, dict):
            uid = s.get('video_uid')
        if isinstance(uid, str) and uid:
            result.append(uid)
        start_s = hour_min2sec(s.get('start_time'))
        end_s = hour_min2sec(s.get('end_time'))
        if end_s < start_s:
            end_s += 24 * 3600  # handle next day case
        dur_s.append(end_s - start_s)
    return result, dur_s

def time_check(uid, dur_s):
    from decord import VideoReader, cpu
    video_path = FULL_SCALE_DIR / f"{uid}.mp4"
    if not video_path.exists():
        return False, 0
    try:
        vr = VideoReader(str(video_path), ctx=cpu(0))
        total_frames = len(vr)
        fps = vr.get_avg_fps()
        video_duration = total_frames / fps
        expected_duration = dur_s
        is_match = (video_duration > expected_duration) or (video_duration < expected_duration + 59.9)
        return is_match, video_duration
    except Exception:
        return False, 0

def main():
    manifest_uids = load_manifest_uids(MANIFEST_CSV)
    print(len(manifest_uids), "uids loaded from manifest")
    sim_files = sorted(SIM_DIR.glob('simulation_*_annotation.json'))

    summary = []
    uids_count = {}
    totals = {
        'files': 0,
        'uids_total': 0,
        'uids_present': 0,
        'uids_missing': 0,
    }

    for jf in sim_files:
        uids, dur_s = extract_simulation_uids(jf)
        present = [u for u in uids if u in manifest_uids]
        missing = [u for u in uids if u not in manifest_uids]
        total = len(uids)
        present_n = len(present)
        missing_n = len(missing)
        ratio = (present_n / total) if total > 0 else 0.0
        all_present = (total > 0 and missing_n == 0)
        almost_all_present = (total > 0 and ratio >= 0.9 and not all_present)

        for uid, dur in zip(uids, dur_s):
            break #this is too slow to check all videos
            if uid in manifest_uids:
                match, video_dur = time_check(uid, dur)
                if not match:
                    print(f"Time mismatch for UID {uid} in file {jf.name}: expected {dur}s, got {video_dur:.2f}s")
                else:
                    print(f"Time match for UID {uid} in file {jf.name}: expected {dur}s, got {video_dur:.2f}s")

        #full_second is the second part of the end time of last simulations item minus the start time of the first simulations item
        full_second = 0
        with open(jf, 'r', encoding='utf-8') as f:
            data = json.load(f)
        sims = data.get('simulations', [])
        if sims:
            start_time = sims[0].get('start_time', '00:00')
            end_time = sims[-1].get('end_time', '00:00')
            start_sec = hour_min2sec(start_time)
            end_sec = hour_min2sec(end_time)
            if end_sec < start_sec:
                end_sec = end_sec + 24 * 3600  # handle next day case
            full_second = end_sec - start_sec
        full_hour_min = sec2hour_min(full_second)

        #dense_second is the summation of all simulations durations
        dense_second = 0
        try:
            with open(jf, 'r', encoding='utf-8') as f:
                data = json.load(f)
            sims = data.get('simulations', [])
            for s in sims:
                start_time = s.get('start_time', '00:00')
                end_time = s.get('end_time', '00:00')
                start_sec = hour_min2sec(start_time)
                end_sec = hour_min2sec(end_time)
                dense_second += max(0, end_sec - start_sec)+60 #we use such value but not video_dur, because that one is too slow to obtain,
        except Exception:
            dense_second = 0
        dense_hour_min = sec2hour_min(dense_second)

        dense_ratio = (dense_second / full_second) if full_second > 0 else 0.0

        summary.append({
            'file': jf.name,
            'total': total,
            'present': present_n,
            'missing': missing_n,
            'presence_ratio': round(ratio, 4),
            'all_present': all_present,
            'almost_all_present': almost_all_present,
            'missing_uids': missing,
            'full_hour_min': full_hour_min,
            'Full_second': full_second,
            'dense_hour_min': dense_hour_min,
            'dense_second': dense_second,
            'dense_ratio': round(dense_ratio, 4),
        })

        totals['files'] += 1
        totals['uids_total'] += total
        for u in uids: uids_count[u] = uids_count.get(u, 0) + 1
        totals['uids_present'] += present_n
        totals['uids_missing'] += missing_n
    
    #sort summary by total uids descending
    summary.sort(key=lambda x: x['dense_second']/x['total'])#x['total']) #
    uids_set = set(uids_count.keys())
    uids_count = {u: c for u, c in sorted(uids_count.items(), key=lambda item:-item[1])}

    report = {
        'manifest_csv_found': MANIFEST_CSV.exists(),
        'manifest_uid_count': len(manifest_uids),
        'totals': totals,
        'per_file': summary,
        "uids_count": uids_count,
    }

    with open(REPORT_JSON, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    UIDS_TXT = Path(os.path.dirname(__file__)) / 'video_uids.txt'
    with open(UIDS_TXT, 'w', encoding='utf-8') as f:
        for uid in uids_count.keys():
            f.write(f"{uid}\n")

    # Pretty-print concise table
    print(f"Manifest CSV found: {MANIFEST_CSV.exists()} | uid count: {len(manifest_uids)}")
    print(f"Files: {totals['files']} | uids total: {totals['uids_total']} | unique uids: {len(uids_set)} | present: {totals['uids_present']} | missing: {totals['uids_missing']}")
    print("file,total,present,missing,ratio,all,almost-all,full_hour_min,dense_hour_min,dense_ratio")
    for row in summary[:20]:  # limit console output
        print(
            f"{row['file']},{row['total']},{row['present']},{row['missing']},{row['presence_ratio']},{row['all_present']},{row['almost_all_present']},{row['full_hour_min']},{row['dense_hour_min']},{row['dense_ratio']}"
        )


    key_sets = set()
    for row in summary[:4]:
        uids, _ = extract_simulation_uids(SIM_DIR / row['file'])
        for u in uids:
            key_sets.add(u)
    print("Sample UIDs from top 4 files:", list(key_sets), "len:", len(key_sets))
        

if __name__ == '__main__':
    main()
