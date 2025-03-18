# 模型加载器配置

对于每一个模型加载器，他们需要或支持的模型配置都不尽相同。本页面将向您展示目前 MuiceBot 所有的模型加载器类所需要的不同配置。你也可以从 [_types.py](https://github.com/Moemu/MuiceBot/blob/main/Muice/llm/_types.py) 中获取所有支持的模型配置项。

## Azure (Github Models)

```yaml
loader: Azure # 使用 Azure 加载器（必填）
model_name: DeepSeek-R1 # 模型名称（必填）
api_key: <your-github-token-goes-here> # GitHub Token 或 Azure Key（必填）
system_prompt: "" # 系统提示（可选）
auto_system_prompt: false # 自动配置沐雪的系统提示（默认为 false）
user_instructions: '我们来玩一个角色扮演的小游戏吧，现在开始你是一个名为的“沐雪”的AI女孩子，用猫娘的语气和我说话。' # 用户提示（可选。对于 DeepSeek-R1 此类不推荐添加系统提示的模型非常有用，此项内容将自动添加至历史首段对话中）
auto_user_instructions: false # 自动配置沐雪的用户提示（默认为 false）
max_tokens: 1024 # 模型生成的最大 token 数（可选，默认为 1024）
temperature: 0.75 # 模型生成的温度参数（可选）
top_p: 0.95 # 模型生成的 Top_p 参数（可选）
frequency_penalty: 1.0 # 模型的频率惩罚（可选）
presence_penalty: 0.0 # 模型的存在惩罚（可选）
think: 1 # DeepSeek-R1 思考过程优化（0不做任何处理；1提取并同时输出思考过程和结果；2仅输出思考结果）
stream: false # 流式对话
multimodal: false # 是否启用多模态（可选。注意：使用的模型必须是多模态的）
```

## Dashscope (阿里百炼大模型平台)

```yaml
loader: Dashscope # 使用 Dashscope 加载器（必须）
model_name: qwen-max # 模型名称（必须）
multimodal: false # 是否启用多模态（可选。注意：使用的模型必须是多模态的）
api_key: xxxxxx # API 密钥（必须）
max_tokens: 1024 # 模型生成的最大 token 数（可选，默认为 1024）
temperature: 0.7 #  模型生成的温度参数（可选，默认为 0.7）
top_p: 0.95 # 模型生成的 Top_p 参数（可选）
repetition_penalty: 1.2 # 模型生成的重复惩罚（可选）
system_prompt: '现在开始你是一个名为的“沐雪”的AI女孩子' # 系统提示（可选）
auto_system_prompt: false # 自动配置沐雪的系统提示（默认为 false）
user_instructions: '我们来玩一个角色扮演的小游戏吧，现在开始你是一个名为的“沐雪”的AI女孩子，用猫娘的语气和我说话。' # 用户提示（对于 DeepSeek-R1 此类不推荐添加系统提示的模型非常有用。此项仅在 History 为空时生效）
auto_user_instructions: false # 自动配置沐雪的用户提示（默认为 false）
think: 1 # DeepSeek-R1 思考过程优化（0不做任何处理；1提取并同时输出思考过程和结果；2仅输出思考结果）
stream: false # 流式对话
online_search: false # 联网搜索（目前仅支持 qwen-max/plus/turbo 系列模型）
```

## Llmtuner (LLama-Factory)

*由于 llmtuner pypi 版本过低，无法兼容最新的模型，且被使用的可能性越来越少。为了优化本项目的环境大小，我们最终决定放弃 llmtuner 模型加载器*

*如果你觉得此加载器的对您的意义重大，您可以 [从此处](https://github.com/Moemu/MuiceBot/blob/f62969871a296744c1b601730c3027816a4fe133/Muice/llm/Llmtuner.py) 获取到 Llmtuner.py 内容并放置到 `Muice/llm` 文件夹中并安装相关依赖，感谢您的理解*

## Ollama

```yaml
loader: Ollama # 使用 Ollama 加载器（必填）
model_name: deepseek-r1 # ollama 模型名称（必填）
api_host: http://localhost:11434 # ollama 客户端端口（可选）
top_k: 20 #从概率分布中选择最高概率的前k个候选项
top_p: 0.9 # 从概率分布中选择累积概率达到阈值p的候选项
temperature: 0.8 # 温度参数，用于调整概率分布的形状
repeat_penalty: 1.2 # 模型的重复惩罚
presence_penalty: 1.5 # 存在惩罚系数，用于调整已出现的词的概率
frequency_penalty: 1.0 # 频率惩罚系数，用于调整频繁出现的词的概率
stream: false # 流式对话
system_prompt: '现在开始你是一个名为的“沐雪”的AI女孩子' # 系统提示（可选）
auto_system_prompt: false # 自动配置沐雪的系统提示（默认为 false）
user_instructions: '我们来玩一个角色扮演的小游戏吧，现在开始你是一个名为的“沐雪”的AI女孩子，用猫娘的语气和我说话。' # 用户提示（对于 DeepSeek-R1 此类不推荐添加系统提示的模型非常有用。此项仅在 History 为空时生效）
auto_user_instructions: false # 自动配置沐雪的用户提示（默认为 false）
multimodal: false # 是否启用多模态（可选。注意：使用的模型必须是多模态的）
```

## Openai (支持 DeepSeek 官方 API 调用)

```yaml
loader: Openai # 使用 openai 加载器（必填）
model_name: text-davinci-003 # 模型名称（必填）
api_key: xxxxxx # API 密钥（必须）
api_host: https://api.openai.com/v1 # 服务器 API 接口地址 （可选，默认 OpenAI 服务）
max_tokens: 1024 # 模型生成的最大 token 数（可选，默认为 1024）
temperature: 0.7 #  模型生成的温度参数（可选，默认为 0.7，对R1使用无效）
system_prompt: '现在开始你是一个名为的“沐雪”的AI女孩子' # 系统提示（可选）
auto_system_prompt: false # 自动配置沐雪的系统提示（默认为 false）
user_instructions: '我们来玩一个角色扮演的小游戏吧，现在开始你是一个名为的“沐雪”的AI女孩子，用猫娘的语气和我说话。' # 用户提示（对于 DeepSeek-R1 此类不推荐添加系统提示的模型非常有用。此项仅在 History 为空时生效）
auto_user_instructions: true # 自动配置沐雪的用户提示（默认为 false）
think: 1 # DeepSeek-R1 思考过程优化（0不做任何处理；1提取并同时输出思考过程和结果；2仅输出思考结果）
stream: false # 流式对话
multimodal: false # 是否启用多模态（可选。注意：使用的模型必须是多模态的）
online_search: false # 联网搜索（目前仅支持从阿里云调用的 qwen-max/plus/turbo/2.5 系列模型）
```

## Rwkv (基于 RWKV-Runner 提供的 API 服务)

*由于 RWKV-Runner 支持 OpenAI API 接口，因此我们已在最新的版本中移除了该模型加载器，请使用 Openai 加载器作为替代*

## Transformers

*由于 Transformers 模型加载器最初为加载 ChatGLM2 系列模型而制作，现已不支持市面上大多数模型，故被弃用*


## Xfyun (星火大模型精调平台)

```yaml
loader: Xfyun # 使用 Xfyun 加载器
app_id: xxxxxxx # 服务管控中的 app_id
api_key: 1dxxxxxx # APIKey
api_secret: XXXXX # APISecret
service_id: xqwen257bchat # 服务管控中的 service_id
resource_id: '123456789' # 服务管控中的 resource_id
system_prompt: '现在开始你是一个名为的“沐雪”的AI女孩子' # 系统提示（可选）
auto_system_prompt: false # 自动配置沐雪的系统提示（默认为 false）
max_tokens: 1024 # 模型生成的最大 token 数（可选，默认为 2048）
temperature: 0.75 # 模型生成的温度参数（可选，默认为 0.5）
top_p: 0.95 # 模型生成的 Top_p 参数（可选，默认为 4）
stream: false # 流式对话
```