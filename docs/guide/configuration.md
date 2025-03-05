# 配置文件⚙️

上面的配置只能够让你的 Bot 跑起来而不能正常回答你的问题，要能与大语言模型交互，我们需要进行一些额外配置。

由于这一节的配置项相当灵活，所以我们需要创建一个 `configs.yml` 并在这里面配置。

## 模型配置

这是 Azure 模型加载器的一个示例配置文件，您可以在 [模型加载器配置](https://github.com/Moemu/Muice-Chatbot/blob/main/docs/model.md#模型加载器配置) 一节中获取这些模型加载器的配置项。

```yaml
model.azure:
  loader: Azure # 使用 azure 加载器
  model_name: DeepSeek-R1 # 模型名称（可选，默认为 DeepSeek-R1）
  token: ghp_xxxxxxxxxxxxxxxxx # GitHub Token（若配置了环境变量，此项不填）
  system_prompt: '我们来玩一个角色扮演的小游戏吧，现在开始你是一个名为的“沐雪”的AI女孩子，用猫娘的语气和我说话。' # 系统提示（可选）
  auto_system_prompt: true # 自动配置沐雪的系统提示（默认为 false）
  think: 1 # DeepSeek-R1 思考过程优化（0不做任何处理；1提取并同时输出思考过程和结果；2仅输出思考结果）
```

实际上，我们支持多个模型配置，并可在聊天中通过指令动态切换，例如：

```yaml
# 模型相关
model:
  loader: Xfyun
  app_id: 'b84ff476'
  api_key: 'XXXXXXXXXX'
  api_secret: xxxxxxxxxxxxxxxxxxxxx
  service_id: 'xxxxxxxxxxxxxxx'
  resource_id: '1234567890'
  system_prompt: '' # 系统提示语（目前仅支持llmtuner模式）
  auto_system_prompt: false # 是否自动生成系统提示语（仅适用于2.7.1以上的Qwen模型）
  max_tokens: 1024 # 模型生成的最大 token 数（可选，默认为 2048）
  temperature: 0.75 # 模型生成的温度参数（可选，默认为 0.5）
  top_p: 0.95 # 模型生成的 Top_p 参数（可选，默认为 4）

model.dashscope:
  loader: Dashscope # 使用 dashscope 加载器
  multimodal: true
  model_name: qwen2.5-vl-7b-instruct # 多模态模型名称
  api_key: sk-xxxxxxxxxxxxxxxxxxxxxxx # API 密钥（必须）
  max_tokens: 1024 # 模型生成的最大 token 数（可选，默认为 1024）
  temperature: 0.7 #  模型生成的温度参数（可选，默认为 0.7）
  system_prompt: 现在开始你是一个名为的“沐雪”的AI女孩子   # 系统提示（可选）
  auto_system_prompt: true # 自动配置沐雪的系统提示（默认为 false）
  repetition_penalty: 1.2

model.azure:
  loader: Azure # 使用 azure 加载器
  model_name: DeepSeek-R1 # 模型名称（可选，默认为 DeepSeek-R1）
  token: ghp_xxxxxxxxxxxxxxxxx # GitHub Token（若配置了环境变量，此项不填）
  system_prompt: '我们来玩一个角色扮演的小游戏吧，现在开始你是一个名为的“沐雪”的AI女孩子，用猫娘的语气和我说话。' # 系统提示（可选）
  auto_system_prompt: true # 自动配置沐雪的系统提示（默认为 false）
  think: 1 # DeepSeek-R1 思考过程优化（0不做任何处理；1提取并同时输出思考过程和结果；2仅输出思考结果）
```

你可能留意到这些模型加载器的配置都是以 `model.<loader>` 的格式命名的，实际上，您可以自由指定顶级键的名字而并非使用二级键，比如 `muxue` 、`muxue_azure` 等。**只需保证存在一个以model为顶级键的模型配置作为默认配置项即可**，当模型配置出现问题时，加载该模型配置时将抛出错误。

虽然但是，这些是不能作为顶级键的键名的，它们会被保留做其他用途：

- `model.default`: Bot 加载配置文件时会创建默认 `model` 配置项的副本，名为 `model.default` ，以便后续回滚切换。如果配置文件存在 `model.default` ，此配置将会被覆盖

- `schedule`: 定时任务配置，不能作为配置文件

其中有一些配置是每个模型加载器配置共有的，这里稍微介绍一下：

```yaml
loader: Xfyun # 模型加载器名称，这些模型加载器位于插件目录下的 llm 文件夹中，并初始化同名文件的同名类，如果不存在则报错。注意，每个模型加载器因为兼容问题，开头首字母都是大写的
think: 1 # 针对于 DeepSeek-R1 等思考模型的思考过程优化（0不做任何处理；1提取并同时输出思考过程和结果；2仅输出思考结果）。即使思考过程不存在，设置为 1 或 2 也不会引发任何错误。
multimodal: true # 多模态支持。目前仅支持 Dashscope 加载器。设置为 true 将处理图片事件。如果调用的模型不是多模态模型将引发报错
```

下面的配置虽然出于各种原因，它们并不是通用的，但还是值得介绍一下：

```yaml
system_prompt: '现在开始你是一个名为的“沐雪”的AI女孩子' # 系统提示（可选）
auto_system_prompt: false # 自动配置沐雪的系统提示（默认为 false）
user_instructions: '我们来玩一个角色扮演的小游戏吧，现在开始你是一个名为的“沐雪”的AI女孩子，用猫娘的语气和我说话。' # 用户提示（对于 DeepSeek-R1 此类不推荐添加系统提示的模型非常有用，此项内容自动添加至历史上下文中）
auto_user_instructions: true # 自动配置沐雪的用户提示（默认为 false）
```

这里主要想补充沐雪的系统提示词，如果你不知道的话可以参考：[auto_system_prompt.py](nonebot_plugin_muicebot/llm/utils/auto_system_prompt.py)


如果一切顺利，以 QQ 适配器为例，在运行 `nb run` 后，你将会看到以下输出，这表明 Bot 已经开始工作：

```shell
(MuxueBot) C:\Users\Muika\Desktop\nonebot-plugin-muice>nb run
[SUCCESS] init: NoneBot is initializing...
[INFO] init: Current Env: prod
[SUCCESS] load_plugin: Succeeded to load plugin "nonebot_plugin_alconna:uniseg" from "nonebot_plugin_alconna.uniseg"
[SUCCESS] load_plugin: Succeeded to load plugin "nonebot_plugin_waiter"
[SUCCESS] load_plugin: Succeeded to load plugin "nonebot_plugin_alconna"
[SUCCESS] load_plugin: Succeeded to load plugin "nonebot_plugin_localstore"
[SUCCESS] load_plugin: Succeeded to load plugin "nonebot_plugin_apscheduler"
[INFO] __init__: 数据库路径: C:\Users\Muika\AppData\Local\nonebot2\nonebot_plugin_muicebot\ChatHistory.db
[SUCCESS] load_plugin: Succeeded to load plugin "nonebot_plugin_muicebot"
[SUCCESS] run: Running NoneBot...
[SUCCESS] run: Loaded adapters: OneBot V12, OneBot V11, Telegram, QQ
[INFO] _serve: Started server process [40776]
[INFO] startup: Waiting for application startup.
[INFO] _start_scheduler: Scheduler Started
[INFO] load_model: 正在加载模型...
[INFO] load_model: 模型加载成功
[INFO] on_startup: MuiceAI 聊天框架已开始运行⭐
[INFO] startup: Application startup complete.
[INFO] _log_started_message: Uvicorn running on http://127.0.0.1:8080 (Press CTRL+C to quit)
[INFO] log: QQ | Bot 123456789 connected
```

现在，当你 @ 机器人或执行命令时 Bot 将开始回复消息流程，除此之外它不会做任何事，除非定时任务开始。

可以愉快地和机器人玩耍啦！⭐

## 定时任务

> [!WARNING]
>
> 由于在主动发起对话时调用 `send_message` 方法需要构建适配器的 Message 类，而我们尚未对不同适配器做优化，所以目前定时任务仅支持 Onebot V12 协议适配器。

众所周知，MuxueAI 支持基于 `nonebot_plugin_apscheduler` 的定时任务，可定时向大语言模型交互或直接发送信息。这也是沐雪系列模型的一个特色之一，尽管其效果确实不是很好（

有关定时任务的配置同样在 `configs.yml` 中进行，以下是一个示例配置：

```yaml
schedule:
  - id: morning
    trigger: cron
    args:
      hour: 8
      minute: 30
    ask: <日常问候：早上>
    target:
      detail_type: private
      user_id: '123456789'

  - id: afternoon
    trigger: cron
    args:
      hour: 12
      minute: 30
    say: 中午好呀各位~吃饭了没有？
    target:
      detail_type: group
      group_id: '123456789'

  - id: auto_create_topic
    trigger: interval
    args:
      minutes: 30
    random: 1
    ask: "<生成推文: 胡思乱想>"
    target:
      detail_type: group
      group_id: '123456789'
```

正如你所见，每个定时任务在 `schedule` 下以列表的形式进行配置。

其中 `id` 和 `trigger` 是 `nonebot_plugin_apscheduler` 的原始参数，分别代表定时任务名称和触发器。

`trigger` 项接受两个值 `cron` 与 `interval`，分别代表定时调度器和固定间隔执行器。

`args` 用于传入两个触发器所需要的不同的参数值，其中：

- `cron` 接受以下参数值： `year`、`month`、`day`、`week`、`day_of_week`、`hour`、`minute`、`second`、`start_date`、`end_date`、`timezone`

- `interval` 接受以下参数值： `week`、`day_of_week`、`hour`、`minute`、`second`、`start_date`、`end_date`、`timezone`

`ask` 和 `say` 虽作为可选参数但必须选择一个，分别代表了传递给模型的 prompt 和直接发送信息的文本内容

`target` 指定发送信息的目标用户/群聊，作为参数传入 `bot` 的 `send_message` 方法。具体参数内容请参见 [适配器文档](https://onebot.adapters.nonebot.dev/docs/api/v12/bot#Bot-send)


定时任务运行引擎将在 `driver.on_bot_connect` 时启动，你也可以运行 `.schedule` 指令手动启动引擎