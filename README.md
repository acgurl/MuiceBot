<div align=center>
  <img width=200 src="doc/image/Avatar.png"  alt="image"/>
  <h1 align="center">MuxueBot</h1>
  <p align="center">Muice-Chatbot 的 NoneBot2 实现</p>
</div>
<div align=center>
  <img src="https://img.shields.io/badge/python-3.10+-blue" alt="python">
  <img src="https://img.shields.io/badge/nonebot-2-red" alt="nonebot2">
</div>

# 介绍✨

沐雪，一只会**主动**找你聊天的 AI 女孩子，其对话模型基于 [Qwen](https://github.com/QwenLM) 微调而成，训练集体量 3k+ ，具有二次元女孩子的说话风格，比较傲娇，但乐于和你分享生活的琐碎，每天会给你不一样的问候。

# 功能🪄

✅ 内嵌多种模型加载器，比如 [Llmtuner](https://github.com/hiyouga/LLaMA-Factory) 和 [OpenAI](https://platform.openai.com/docs/overview) ，可加载市面上大多数的模型服务或本地模型，部分支持多模态（图片识别）。另外还附送只会计算 3.9 > 3.11 的沐雪 Roleplay 微调模型一枚~

✅ 支持 `nonebot.adapters.onebot.v11&v12` 、`nonebot.adapters.qq`  、`nonebot.adapters.telegram` 适配器，其中部分特定适配器可为对应的平台提供较好的支持 ~~（大概吧）~~

✅ 支持基于 `nonebot_plugin_apscheduler` 的定时任务，可定时向大语言模型交互或直接发送信息。

✅ 支持基于 `nonebot_plugin_alconna` 的几条常见指令。什么，没有群管理指令？下次再说吧（bushi）

✅ 使用 SQLite3 保存对话数据。那有人就要问了：Maintainer，Maintainer，能不能实现长期短期记忆、LangChain、FairSeq 这些记忆优化啊，实在不行，多模态图像数据保存和最大记忆长度总该有吧。很抱歉，都没有（

# TODO📝

- [ ] 撰写文档。你没听错，我们还没有文档。

- [ ] 插件系统。世界上唯一一个还没支持插件的 Bot 诞生了

- [ ] 多模态：工具集。沐雪还不会用呢

- [ ] OFA 图像识别。既然都有了多模态为什么还用 OFA？好吧，因为没钱调用接口

- [ ] Faiss 记忆优化。沐雪总记不太清楚上一句话是什么

- [ ] 短期记忆和长期记忆优化。总感觉这是提示工程师该做的事情，~~和 Bot 没太大关系~~

- [ ] （多）对话语音合成器。比如 [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS) 、[RVC](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI)之类的。

- [ ] 发布。我知道你很急，但是你先别急。

# 快速开始💻

本节及后续文档默认您有独立搭建过 Nonebot 服务的相关经验。

建议环境：

- 安装好 `nb-cli` 环境的 Python 3.10 及以上 Python 版本

如果您计划在本地与大语言模型交互，我们强烈建议您创建一个虚拟环境。

由于此插件还在开发早期，因此请通过 git clone 等方式安装插件：

```shell
git clone https://github.com/Moemu/nonebot-plugin-muice
```

然后安装依赖：

如果只使用在线模型服务，请执行：

```shell
pip install .
pip install nonebot2[fastapi]
```

如果想同时使用本地运行的模型服务，请执行：

```shell
pip install .[local]
pip install nonebot2[fastapi]
```

> [!NOTE]
>
> 通过这种方法安装的 `Pytorch` 可能并不支持 `cuda` 。如需要，请额外安装。

如果想为本项目做出贡献，请执行：

```shell
pip install .[local,dev]
pip install nonebot2[fastapi]
```

这将安装 `pre-commit` 和其他必须项用于代码检查

如一切顺利，我们可以开始配置：

在项目中创建 `.env` 文件并写入：

```dotenv
DRIVER=~fastapi+~websockets+~httpx
```

这只是 NoneBot 运行的必需项，接下来我们将配置适配器。

如果你使用 OneBot 适配器，则无需另行配置，在平台实现中配置连接即可。除非你想[配置访问权限](https://onebot.adapters.nonebot.dev/docs/guide/configuration) 。

如果你使用 Telegram 适配器，请写入 Bot 密钥，如需要，也可写入代理配置：

```dotenv
telegram_bots = [{"token": "1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHI"}]
telegram_proxy = "http://127.0.0.1:10809"
```

如果你使用 QQ 适配器，请参考[文档示例](https://github.com/nonebot/adapter-qq)填写信息。下面给出了私域频道机器人（审核未通过沙盒版）的示例配置：

```dotenv
QQ_IS_SANDBOX=true
QQ_BOTS='[{"id": "11451419", "token": "KFCvivo50MuxueYYDS", "secret": "GiveAStarToMuice5Q", "intent": {"guild_messages": true,"at_messages": true}, "use_websocket": true}]'
```

至此，`NoneBot` 的本身的配置部分到此结束


# 额外配置⚙️

上面的配置只能够让你的 Bot 跑起来而不能正常回答你的问题，要能与大语言模型交互，我们需要进行一些额外配置。

由于这一节的配置项相当灵活，所以我们需要创建一个 `configs.yml` 并在这里面配置。

## 模型配置

这是 Azure 模型加载器一个实例配置，您可以在 [模型加载器配置](https://github.com/Moemu/Muice-Chatbot/blob/main/docs/model.md#模型加载器配置) 一节中获取这些模型加载器的配置项。

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

## 定时任务（TODO 发生更改）

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
    message: 中午好呀各位~吃饭了没有？
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

`ask` 和 `message` 虽作为可选参数但必须选择一个，分别代表了传递给模型的 prompt 和直接发送信息的文本内容

`target` 指定发送信息的目标用户/群聊，作为参数传入 `bot` 的 `send_message` 方法。具体参数内容请参见 [适配器文档](https://onebot.adapters.nonebot.dev/docs/api/v12/bot#Bot-send)


定时任务运行引擎将在 `driver.on_bot_connect` 时启动，你也可以运行 `.schedule` 指令手动启动引擎



# 指令介绍🕹️

MuxueAI 内嵌了多种指令方便开发者开发和日常聊天，只需使用前缀 “.” 或 “/” 即可调用指令。

调用 `.help` 将返回指令说明（无需 @ 机器人）

> 基本命令：
> help 输出此帮助信息
> status 显示当前状态
> refresh 刷新模型输出
> reset 清空对话记录
> undo 撤回上一个对话
> load <config_name> 加载模型
>（支持的命令前缀：“.”、“/”）

调用 `.status` 将返回 Bot 运行状态，好吧，现在还是模型运行状态（TODO: 加入定时任务状态）

> 当前模型加载器：Xfyun
> 模型加载器状态：运行中
> 多模态模型: 否

调用 `.load <config_name>` 将加载新的模型加载器配置文件，比如 `.load model.dashscope`

> 已成功加载 model.dashscope

> .status

> 当前模型加载器：Dashscope
> 模型加载器状态：运行中
> 多模态模型: 是

当 `.load` 未提供任何参数时将加载默认配置文件，即 `.load model.default`，等同于切换模型前的 `.load model` 命令

需要注意的一点是，`.undo` 不是撤回 Bot 的发言，而是撤回*消息发送者*的上一次对话，将其从数据库中删除而不是调用适配器撤回接口

一些命令虽然不存在于文档中，但它确实存在于代码，比如 `.schedule` 。这个指令虽然不会返回任何东西，但它负责启用定时任务引擎。对于某些适配器连接后不会触发 `driver.on_bot_connect` 的事件，其非常有用


# 关于沐雪

## 沐雪人设

与其他聊天机器人项目不同，本项目提供由本人通过自家对话数据集微调后的模型，在 Release 中提供下载，关于微调后的模型人设，目前公开的信息如下：

![沐雪人设图（若无法打开请通过右键打开）](https://i0.hdslb.com/bfs/new_dyn/9fc79347b54c5f2835884c8f755bd1ea97020216.png)

训练集开源地址： [Moemu/Muice-Dataset](https://huggingface.co/datasets/Moemu/Muice-Dataset)

原始模型：[THUDM/ChatGLM2-6B](https://github.com/THUDM/ChatGLM2-6B) & [QwenLM/Qwen](https://github.com/QwenLM/Qwen)）

本项目源码使用 [MIT License](https://github.com/Moemu/Muice-Chatbot/blob/main/LICENSE)，对于微调后的模型文件，不建议将其作为商业用途

## 示例对话（训练集）📑

参见公开的训练集 [(HuggingFace)Moemu/Muice-Dataset](https://huggingface.co/datasets/Moemu/Muice-Dataset) | [(Modelscope)Moemuu/Muice-Dataset](https://www.modelscope.cn/datasets/Moemuu/Muice-Dataset)

## 模型下载

参见 [加载沐雪微调模型](https://github.com/Moemu/Muice-Chatbot/tree/main?tab=readme-ov-file#%E5%8A%A0%E8%BD%BD%E6%B2%90%E9%9B%AA%E5%BE%AE%E8%B0%83%E6%A8%A1%E5%9E%8B)


# 关于🎗️

本项目基于 [BSD 3](https://github.com/Moemu/nonebot-plugin-muice/blob/main/LICENSE) 许可证提供（暂定），出现特殊用途时请仔细阅读许可证中的规定

对于沐雪的人设和未明确注明许可证和使用范围的模型文件，虽然没有明确限制，但十分不建议将其作为商业用途

此项目中基于或参考了部分开源项目的实现，在这里一并表示感谢：

- [nonebot/nonebot2](https://github.com/nonebot/nonebot2) 本项目使用的机器人框架

- [@botuniverse](https://github.com/botuniverse) 负责制定 Onebot 标准的组织

- [@Tencent](https://github.com/Tencent) 封了我两个号，直接导致本项目的出现

感谢各位开发者的协助，这里就不一一列举出名字了：

<a href="https://github.com/eryajf/Moemu/Muice-Chatbot/contributors">
  <img src="https://contrib.rocks/image?repo=Moemu/Muice-Chatbot"  alt="图片加载中..."/>
</a>

友情链接：[LiteyukiStudio/nonebot-plugin-marshoai](https://github.com/LiteyukiStudio/nonebot-plugin-marshoai)

本项目隶属于 MuikaAI

基于 OneBot V11 的原始实现：[Moemu/Muice-Chatbot](https://github.com/Moemu/Muice-Chatbot)

官方唯一频道：[沐雪的小屋](https://pd.qq.com/s/d4n2xp45i)

<a href="https://www.afdian.com/a/Moemu" target="_blank"><img src="https://pic1.afdiancdn.com/static/img/welcome/button-sponsorme.png" alt="afadian" style="height: 45px !important;width: 163px !important;"></a>
<a href="https://www.buymeacoffee.com/Moemu" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 45px !important;width: 163px !important;" ></a>

<!-- Star History： -->

<!-- [![Star History Chart](https://api.star-history.com/svg?repos=Moemu/Muice-Chatbot&type=Date)](https://star-history.com/#Moemu/Muice-Chatbot&Date) -->