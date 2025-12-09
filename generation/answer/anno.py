from narration import narration, narrations, all_narrations

class answer:
    def __init__(self, QUERY):
        self.QUERY = QUERY
        self.answer_text = ""
    
    @property
    def hints(self):
        return self.QUERY.hints

    @property
    def LLM(self):
        return self.QUERY.LLM

    def run(self):
        if len(self.hints.results) < 1:
            #self.answer_text = f"Too few relevant annotations found {len(self.hints.results)} {f"({self.QUERY.hints.results[0].narr_text})" if len(self.hints.results) == 1 else ''}."
            self.answer_text = "Insufficient information to answer the question."
            return
            
        SYSTEM_PROMPT = "You are an AI assistant that helps people find information efficiently. " + \
            "You will be provided with a question and a set of relevant annotations. " + \
            "Use the provided annotations to answer the question as accurately as possible. " + \
            "If the annotations do not contain enough information to answer the question, respond with 'Insufficient information to answer the question.' " + \
            "Based on the annotations, please answer the question concisely and directly, do not include any additional information."

        USER_PROMPT = "The question is " + self.QUERY.query_text + "\n" + \
            "The annotations near the time are: \n" + \
            "\n".join([ n.narr_text for n in self.QUERY.hints.results ]) + "\n" + \
            
        self.answer_text = self.LLM(USER_PROMPT, system_prompt=SYSTEM_PROMPT)

    def to_dict(self):
        return {
            "narrations": [ n.to_dict() for n in self.QUERY.hints.results ],
            "answer_text": self.answer_text
        }


class query:
    def __init__(self, query_dict, QUERIES):
        self.response_start_time_sec = query_dict.get("response_start_time_sec", 0.0)
        self.response_end_time_sec = query_dict.get("response_end_time_sec", 0.0)
        self.query_text = query_dict.get("query", "")
        self.template = query_dict.get("template", "")
        self.video_uid = query_dict.get("video_uid", "")
        self.QUERIES = QUERIES

        self.hints = None
        self._answer = answer(self)
    
    @property
    def LLM(self):
        return self.QUERIES.LLM
    
    @property
    def narrations(self):
        return self.QUERIES.narrations

    def hour_min2sec(self, time_str):
        h, m = map(int, time_str.split(":"))
        return h * 3600 + m * 60    

    @property
    def base_start_time_sec(self):
        return self.hour_min2sec(self.QUERIES.query_metadata["query_range"]["start_time"])

    @property
    def ANNOS(self):
        return self.QUERIES.QUERIES_LIST.ANNO.ANNOS

    def search(self):
        self.hints = self.QUERIES.narrations.search(self.response_start_time_sec - self.base_start_time_sec, self.response_end_time_sec - self.base_start_time_sec, max_results=self.ANNOS.top_k)

    def run(self):
        self.search()
        self.ANNOS.BINS[len(self.hints.results)] += 1
        self._answer.run()
        try:
            self.QUERIES.QUERIES_LIST.ANNO.progress.update(1)
        except:
            pass

    def to_dict(self):
        return {
            "response_start_time_sec": self.response_start_time_sec,
            "response_end_time_sec": self.response_end_time_sec,
            "query": self.query_text,
            "template": self.template,
            "video_uid": self.video_uid,
            "answer": self._answer.to_dict() if self._answer is not None else {}
        }

class queries:
    def __init__(self, queries_dict, QUERIES_LIST):
        self.QUERIES_LIST = QUERIES_LIST
        """
        {
            "query_metadata": {
                "query_range": {
                    "start_time": "07:00",
                    "end_time": "08:13"
                },
                "video_index": 0,
                "video_uid": "662a5fbd-6865-43e6-a2e5-06ffd30c8fc6"
            },
            "queries": [
                {
                    "response_start_time_sec": 25362.1010186,
                    "response_end_time_sec": 25369.5030286,
                    "query": "What did I put in the drawer?",
                    "template": "Objects: What did I put in X?",
                    "video_uid": "662a5fbd-6865-43e6-a2e5-06ffd30c8fc6"
                },
                {
                    "response_start_time_sec": 25370.2937986,
                    "response_end_time_sec": 25371.8460286,
                    "query": "Where did i put my towel?",
                    "template": "Place: Where did I put X?",
                    "video_uid": "662a5fbd-6865-43e6-a2e5-06ffd30c8fc6"
                },
            ]
        },
        """
        self.query_metadata = queries_dict.get("query_metadata", {})

        self.queries = []
        for query_dict in queries_dict.get("queries", []):
            self.queries.append(query(query_dict, self))
        
        self.narrations = self.ALL_NARRATION[self.query_metadata.get("video_uid", "")]

    @property
    def LLM(self):
        return self.QUERIES_LIST.LLM
    
    @property
    def ALL_NARRATION(self):
        return self.QUERIES_LIST.ALL_NARRATION

    def run(self):
        for q in self.queries: q.run()

    def __getitem__(self, index):
        return self.queries[index]

    def __len__(self):
        return len(self.queries)
    
    def to_dict(self):
        return {
            "query_metadata": self.query_metadata,
            "queries": [ q.to_dict() for q in self.queries ]
        }

class queries_list:
    def __init__(self, queries_list_dict, ANNO):
        self.ANNO = ANNO
        self.queries_list = []
        for queries_dict in queries_list_dict:
            self.queries_list.append(queries(queries_dict, self))
    
    def __getitem__(self, index):
        return self.queries_list[index]

    def __len__(self):
        return sum([len(ql) for ql in self.queries_list])
    
    def to_dict(self):
        return [ q.to_dict() for q in self.queries_list ]
    
    def run(self):
        for q in self.queries_list: q.run()

    @property
    def LLM(self):
        return self.ANNO.LLM
    
    @property
    def ALL_NARRATION(self):
        return self.ANNO.ALL_NARRATION

class anno:
    def __init__(self, file_path, ANNOS):
        self.ANNOS = ANNOS
        import json
        self.anno_data = {}
        with open(file_path, 'r') as f:
            self.anno_data = json.load(f)
        
        self.anno_task = self.anno_data.get("tasks", "")
        self.anno_data["mixed"] = True
        self.anno_data["tasks"] = self.anno_task
        self.anno_task["mixed"] = True

        self.objects_retrieval = self.anno_task.get("objects_retrieval", [])
        self.anno_task["objects_retrieval"] = self.objects_retrieval
        self.objects_retrieval["mixed"] = True
        self.objects_retrieval["query_list"] = queries_list(self.objects_retrieval["query_list"], self)

        self.people_retrieval = self.anno_task.get("people_retrieval", [])
        self.anno_task["people_retrieval"] = self.people_retrieval
        self.people_retrieval["mixed"] = True
        self.people_retrieval["query_list"] = queries_list(self.people_retrieval["query_list"], self)

    
    def __len__(self):
        return len(self.objects_retrieval["query_list"]) + len(self.people_retrieval["query_list"])

    def run(self):
        from tqdm import tqdm
        #self.progress = tqdm(total=len(self))

        self.objects_retrieval["query_list"].run()
        self.people_retrieval["query_list"].run()

    def to_dict(self, obj):
        try:
            d = obj.to_dict()
            return d
        except:
            if isinstance(obj, list):
                return [ self.to_dict(o) for o in obj ]
            elif obj.get("mixed", None) is not None:
                return { k: self.to_dict(v) for k, v in obj.items() if k != "mixed" }
            else:
                return obj

    def save(self, file_path):
        import json
        with open(file_path, 'w') as f:
            json.dump(self.to_dict(self.anno_data), f, indent=4)
    
    @property
    def LLM(self):
        return self.ANNOS.LLM

    @property
    def ALL_NARRATION(self):
        return self.ANNOS.ALL_NARRATION
    
class annos:
    def __init__(self, ALL_NARRATION_PATH, in_folder, out_folder, model_path, keys=None, top_k=5):
        try:
            from MyLm import call
            from llm import MyLLM, MyLL
            LLM = MyLL(model_path)
        except:
            from llm import DeepSeekLLM
            LLM = DeepSeekLLM()

        self.LLM = LLM
        self.ALL_NARRATION = all_narrations(ALL_NARRATION_PATH)

        import os
        self.annos_data = {}
        for key in keys if keys is not None else [f[:-16] for f in os.listdir(in_folder) if f.endswith('_annotation.json')]:
            file_path = os.path.join(in_folder, f"{key}_annotation.json")
            self.annos_data[key] = anno(file_path, self)
        
        self.out_folder = out_folder
        self.top_k = top_k
        self.BINS = [0 for _ in range(self.top_k + 1)] #[2065, 1709, 2890, 1279, 786, 3298]

    def __len__(self): #12027 * 12s = 144324s = 40.09 hours
        return sum([len(anno_obj) for anno_obj in self.annos_data.values()])

    def human_readable_time(self, seconds):
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        return f"{int(h):02}:{int(m):02}:{s:06.3f}"

    def run(self):
        import os, time
        t_start, t_this = time.time(), time.time()
        cnt = 0
        from tqdm import tqdm
        #for key, anno_obj in tqdm(self.annos_data.items()):
        for key, anno_obj in (self.annos_data.items()):
            anno_obj.run()
            anno_obj.save(os.path.join(self.out_folder, f"{key}_annotations.json"))
            cnt += len(anno_obj)
            print(f"Saved annotation for {key}, time elapsed: {self.human_readable_time(time.time() - t_this)}, processed: {len(anno_obj)} queries, total time elapsed: {self.human_readable_time(time.time() - t_start)}, remaining: {len(self) - cnt} queries, estimated remaining time: {self.human_readable_time((time.time() - t_start) / cnt * (len(self) - cnt))}")
            t_this = time.time()
            #break
        
        #print("BINS:", self.BINS)