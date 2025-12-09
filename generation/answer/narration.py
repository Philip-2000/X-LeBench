class narration:
    def __init__(self, narration_dict):
        self.timestamp_sec = narration_dict.get("timestamp_sec", 0.0)
        self.timestamp_frame = narration_dict.get("timestamp_frame", 0)
        self.unmapped_timestamp_sec = narration_dict.get("_unmapped_timestamp_sec", 0.0)
        self.narration_text = narration_dict.get("narration_text", "")
        self.annotation_uid = narration_dict.get("annotation_uid", "")
    
    @property
    def time_s(self):
        return self.timestamp_sec
    
    def diff(self, other_time_s):
        return abs(self.time_s - other_time_s)

    @property
    def narr_text(self):
        return self.narration_text.replace("C ", "I ").replace(" C", " I").replace("X ", "a person ").replace(" X", " a person")
    
    def to_dict(self):
        return {
            "timestamp_sec": self.timestamp_sec,
            "timestamp_frame": self.timestamp_frame,
            "_unmapped_timestamp_sec": self.unmapped_timestamp_sec,
            "narration_text": self.narration_text,
            "annotation_uid": self.annotation_uid
        }
    
class narration_result:
    def __init__(self, time_s, top_k=5):
        self.top_k = top_k
        self.time_s = time_s
        self.results = []
    
    def __iadd__(self, other):
        if len(self.results) < self.top_k:
            self.results.append(other)
        else:
            if other.diff(self.time_s) < self.results[-1].diff(self.time_s):
                self.results[-1] = other
        self.results.sort(key=lambda x: x.diff(self.time_s))
        return self
    
    
class narrations:
    def __init__(self, json_data, key):
        self.json_data = json_data
        self.key = key
    
    def search(self, time, time_end, max_results=5):
        results = narration_result(time, top_k=max_results)
        for _pass in self.json_data:
            try:
                for narration_dict in self.json_data[_pass].get("narrations", []):
                    narration_object = narration(narration_dict)
                    if narration_object.time_s >= time and narration_object.time_s <= time_end:
                        results += narration_object
            except:
                pass
        return results
        

class all_narrations:
    def __init__(self, file_path):
        import json
        self.json_data = {}
        with open(file_path, 'r') as f:
            self.json_data = json.load(f)

    def __getitem__(self, key):
        return narrations(self.json_data.get(key, None), key)