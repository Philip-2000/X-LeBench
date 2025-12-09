
class MyLL:
    def __init__(self, path):
        pass
    
    def __call__(self, user_prompt, system_prompt=None):
        return "I don't know"

class MyLLM:
    def __init__(self, path):
        from transformers import AutoModelForCausalLM, AutoTokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(path)
        self.model = AutoModelForCausalLM.from_pretrained(path, dtype="auto", device_map="auto")

    def __call__(self, user_prompt, system_prompt=None):
        messages = [
            {"role": "user", "content": user_prompt}
        ] if system_prompt is None else [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=True # Switches between thinking and non-thinking modes. Default is True.
        )
        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)

        # conduct text completion
        generated_ids = self.model.generate( **model_inputs, max_new_tokens=32768 )
        output_ids = generated_ids[0][len(model_inputs.input_ids[0]):].tolist() 

        # parsing thinking content
        try:# rindex finding 151668 (</think>)
            index = len(output_ids) - output_ids[::-1].index(151668)
        except ValueError:
            index = 0

        thinking_content = self.tokenizer.decode(output_ids[:index], skip_special_tokens=True).strip("\n")
        content = self.tokenizer.decode(output_ids[index:], skip_special_tokens=True).strip("\n")
        return content
    

class LLMBase:
    def __init__(self, api_key_env_name, base_url, model):
        self.api_key = os.getenv(api_key_env_name)
        self.base_url = 'https://' + base_url
        self.model = model
        from openai import OpenAI
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def __call__(self, user_prompt, system_prompt=None, max_tokens=1024, stream=False):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": user_prompt}
            ] if system_prompt is None else [
                {"role": "system", "content": system_prompt}, 
                {"role": "user", "content": user_prompt}
            ],
            #temperature=temperature,
            max_tokens=max_tokens,
            stream=stream
        )
        return response.choices[0].message.content.strip()
    
    def text(self, txt):
        return txt
    
class DeepSeekLLM(LLMBase):
	def __init__(self, model=""):
		super().__init__(api_key_env_name='DEEPSEEK_API_KEY',
						base_url='api.deepseek.com',
						model = model if len(model) else 'deepseek-chat')


class QwenLLM(LLMBase):
	def __init__(self, model=""):
		super().__init__(api_key_env_name='QWEN_API_KEY',
						base_url='dashscope.aliyuncs.com/compatible-mode/v1',
						model = model if len(model) else 'qwen-plus')


# ================= VLM相关实现 =====================
import os


class VLMBase:
    def __init__(self, api_key_env_name, base_url, model):
        self.api_key = os.getenv(api_key_env_name)
        self.base_url = 'https://' + base_url
        self.model = model

    def __call__(self, **kwargs):
        raise NotImplementedError("Subclasses should implement this method.")


class QwenVLM(VLMBase):
    def __init__(self, model="", api_key_env=""):
        super().__init__(api_key_env_name=api_key_env if len(api_key_env) else 'QWEN_API_KEY',
                         base_url='',
                         model=model if len(model) else 'qwen-vl-max-latest')
        #https://help.aliyun.com/zh/model-studio/vision/?spm=a2c4g.11186623.0.i5#356cfd6a142g3

    def __call__(self, user_prompt, system_prompt=None):
        from dashscope import MultiModalConversation
        messages = [
            {'role':'user', 'content': user_prompt}
        ] if system_prompt is None else [
            {"role": "system", "content": system_prompt},
            {'role':'user', 'content': user_prompt}
        ]
        response = MultiModalConversation.call(
            api_key=self.api_key,
            model=self.model,
            messages=messages) #print(response)
        return response["output"]["choices"][0]["message"].content[0]["text"]

    def video_img_seq(self, img_seq, fps=2):
        return {'video': ["file://"+i for i in img_seq], "fps": fps}

    def video_img_folder(self, folder, fps=2, original_fps=4, ext=".jpg"):
        assert original_fps % fps == 0, "original_fps should be multiple of fps"
        step = original_fps // fps
        img_seq = [os.path.join(folder, f) for i, f in enumerate(sorted(os.listdir(folder))) if i % step == 0 and f.endswith(ext)]
        return {'video': ["file://"+i for i in img_seq], "fps": fps}

    def video_file(self, video_path, fps=2):
        return {"video": "file://"+video_path, "fps": fps}

    def img(self, img_path):
        return {"image": "file://"+img_path}

    def text(self, text):
        return {"text": text}

class DeepSeekVLM(VLMBase):
    def __init__(self, model=""):
        super().__init__(api_key_env_name='DEEPSEEK_API_KEY',
                         base_url='',
                         model=model if len(model) else 'deepseek-v1')

    def __call__(self, user_prompt, system_prompt=None):
        raise NotImplementedError("DeepSeekVLM api_call not implemented yet.")
