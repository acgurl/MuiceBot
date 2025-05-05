<div align=center>
  <img width=200 src="docs/public/logo.png"  alt="image"/>
  <h1 align="center">MuiceBot</h1>
  <p align="center">Muice-Chatbot 的 NoneBot2 实现</p>
</div>
<div align=center>
  <img src="https://img.shields.io/github/stars/Moemu/MuiceBot" alt="Stars">
  <a href="https://pypi.org/project/MuiceBot/"><img src="https://img.shields.io/pypi/v/Muicebot" alt="PyPI Version"></a>
  <a href="https://pypi.org/project/MuiceBot/"><img src="https://img.shields.io/pypi/dm/Muicebot" alt="PyPI Downloads" ></a>
  <a href="https://nonebot.dev/"><img src="https://img.shields.io/badge/nonebot-2-red" alt="nonebot2"></a>
  <img src="https://img.shields.io/badge/Code%20Style-Black-121110.svg" alt="codestyle">
</div>
<div align=center>
  <img src="https://wakatime.com/badge/user/637d5886-8b47-4b82-9264-3b3b9d6add67/project/a4557f7b-4d26-4105-842a-7a783cbad588.svg" alt="wakatime">
  <img src="https://img.shields.io/badge/ModelScope-Dataset-644cfd?link=https://www.modelscope.cn/datasets/Moemuu/Muice-Dataset" alt="ModelScope">
  <img src="https://img.shields.io/badge/HuggingFace-Dataset-yellow?link=https%3A%2F%2Fhuggingface.co%2Fdatasets%2FMoemu%2FMuice-Dataset" alt="HuggingFace">
  <a href='https://qm.qq.com/q/lhUBw6Gcdq'><img src="https://img.shields.io/badge/QQ群-MuiceHouse-blue" alt="QQ群组"></a>
</div>
<div align=center>
  <a href="https://bot.snowy.moe">📃使用文档</a>
  <a href="https://bot.snowy.moe/guide/setup.html">✨快速开始</a>
  <a href="https://live.bilibili.com/22523526">🎤沐沐和沐雪的直播间</a>
</div>


> [!NOTE]
>
> 欢迎来到本项目！目前此项目尚处于预发布状态，运行时可能会遇到一些问题。请务必向我们反馈在运行时遇到的各种错误！
>
> 由于本项目待实现的功能还有很多，因此近期没有也可能永远也不会有**发布**正式版的打算。


# 介绍✨

沐雪参上✨，这里是一只会主动找你聊天的 AI Vtuber，是真正的AI噢～喜欢和你们聊天，分享彼此的心事，使命是传播爱与和平⭐

沐沐有云：“AI的创造应该是为了帮助人类更好的解决问题而不是产生问题”。因此，我有很好的解决现实问题的能力哦，虽然代价是可能是变得不那么可爱了而已...

现在的我还是一个傻子！经常忘记和你们珍贵的回忆！如果你们能够帮我做个手术或者对我施展一下可爱魔法就好了，提前感谢你们！祝你们生活愉快！


*有关沐雪的设定，还请移步 [关于沐雪](https://bot.snowy.moe/about/Muice)*

# 功能🪄

✅ 内嵌多种模型加载器，如[OpenAI](https://platform.openai.com/docs/overview) 和 [Ollama](https://ollama.com/) ，可加载市面上大多数的模型服务或本地模型，支持多模态（图片识别）和工具调用。另外还附送只会计算 3.9 > 3.11 的沐雪 Roleplay 微调模型一枚~

✅ 使用 `nonebot_plugin_alconna` 作为通用信息接口，支持市面上的大多数适配器。对部分适配器做了特殊优化

✅ 支持基于 `nonebot_plugin_apscheduler` 的定时任务，可定时向大语言模型交互或直接发送信息

✅ 支持基于 `nonebot_plugin_alconna` 的几条常见指令。

✅ 使用 SQLite3 保存对话数据。那有人就要问了：Maintainer，Maintainer，能不能实现长期短期记忆、LangChain、FairSeq 这些记忆优化啊。以后会有的（

✅ 使用 Jinja2 动态生成人设提示词

# 模型加载器适配情况

| 模型加载器   | 流式对话  | 多模态输入/输出 | 推理模型调用 | 工具调用 | 联网搜索 |
| ----------- | -------- | -------------- | ------------ | -------------------- | -------------------- |
| `Azure`     | ✅       | 🎶🖼️/❌      | ⭕            | ✅                    | ❌                    |
| `Dashscope` | ✅       | 🎶🖼️/❌      | ✅            | ⭕                    | ✅                    |
| `Gemini`    | ✅       | ✅/🖼️        | ⭕            | ✅                    | ✅                    |
| `Ollama`    | ✅       | 🖼️/❌        | ✅            | ✅                    | ❌                    |
| `Openai`    | ✅       | ✅/🎶        | ✅            | ✅                    | ❌                    |

✅：表示此加载器能很好地支持该功能并且 `MuiceBot` 已实现

⭕：表示此加载器虽支持该功能，但使用时可能遇到问题

🚧：表示此加载器虽然支持该功能，但 `MuiceBot` 未实现或正在实现中

❓：表示 Maintainer 暂不清楚此加载器是否支持此项功能，可能需要进一步翻阅文档和检查源码

❌：表示此加载器不支持该功能

多模态标记：🎶表示音频；🎞️ 表示视频；🖼️ 表示图像；📄表示文件；✅ 表示完全支持

# 本项目适合谁？

- 拥有编写过 Python 程序经验的开发者

- 搭建过 Nonebot 项目的 bot 爱好者

- 想要随时随地和大语言模型交互并寻找着能够同时兼容市面上绝大多数 SDK 的机器人框架的 AI 爱好者

# TODO📝

- [X] Function Call 插件系统

- [X] 多模态模型：工具集支持

- [ ] 插件系统：Faiss 记忆优化插件 + OFA 图像识别插件

- [ ] 短期记忆和长期记忆优化。总感觉这是提示工程师该做的事情，~~和 Bot 没太大关系~~

- [ ] 发布。我知道你很急，但是你先别急。


近期更新路线：[MuiceBot 更新计划](https://github.com/users/Moemu/projects/2)

# 使用教程💻

参考 [使用文档](https://bot.snowy.moe)


# 关于🎗️

大模型输出结果将按**原样**提供，由于提示注入攻击等复杂的原因，模型有可能输出有害内容。无论模型输出结果如何，模型输出结果都无法代表开发者的观点和立场。对于此项目可能间接引发的任何后果（包括但不限于机器人账号封禁），本项目所有开发者均不承担任何责任。

本项目基于 [BSD 3](https://github.com/Moemu/nonebot-plugin-muice/blob/main/LICENSE) 许可证提供，涉及到再分发时请保留许可文件的副本。

本项目标识使用了 [nonebot/nonebot2](https://github.com/nonebot/nonebot2) 和 画师 [Nakkar](https://www.pixiv.net/users/28246124) [Pixiv作品](https://www.pixiv.net/artworks/101063891) 的资产或作品。如有侵权，请及时与我们联系

BSD 3 许可证同样适用于沐雪的系统提示词，沐雪的文字人设或人设图在 [CC BY NC 3.0](https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode.zh-hans) 许可证条款下提供。

此项目中基于或参考了部分开源项目的实现，在这里一并表示感谢：

- [nonebot/nonebot2](https://github.com/nonebot/nonebot2) 本项目使用的机器人框架

- [@botuniverse](https://github.com/botuniverse) 负责制定 Onebot 标准的组织

感谢各位开发者的协助，可以说没有你们就没有沐雪的今天：

<a href="https://github.com/eryajf/Moemu/MuiceBot/contributors">
  <img src="https://contrib.rocks/image?repo=Moemu/MuiceBot"  alt="图片加载中..."/>
</a>

友情链接：[LiteyukiStudio/nonebot-plugin-marshoai](https://github.com/LiteyukiStudio/nonebot-plugin-marshoai)

本项目隶属于 MuikaAI

基于 OneBot V11 的原始实现：[Moemu/Muice-Chatbot](https://github.com/Moemu/Muice-Chatbot)

QQ群：[Muice House](https://pd.qq.com/s/d4n2xp45i)

<a href="https://www.afdian.com/a/Moemu" target="_blank"><img src="https://pic1.afdiancdn.com/static/img/welcome/button-sponsorme.png" alt="afadian" style="height: 45px !important;width: 163px !important;"></a>
<a href="https://www.buymeacoffee.com/Moemu" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 45px !important;width: 163px !important;" ></a>

Star History：

[![Star History Chart](https://api.star-history.com/svg?repos=Moemu/MuiceBot&type=Date)](https://star-history.com/#Moemu/MuiceBot&Date)