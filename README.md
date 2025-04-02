<div align=center>
  <img width=200 src="docs/public/logo.png"  alt="image"/>
  <h1 align="center">MuiceBot</h1>
  <p align="center">Muice-Chatbot 的 NoneBot2 实现</p>
</div>
<div align=center>
  <img src="https://img.shields.io/github/stars/Moemu/MuiceBot" alt="Stars">
  <img src="https://img.shields.io/badge/python-3.10+-blue" alt="python">
  <img src="https://img.shields.io/badge/nonebot-2-red" alt="nonebot2">
  <img src="https://img.shields.io/badge/Code%20Style-Black-121110.svg" alt="codestyle">
  <img src="https://github.com/Moemu/MuiceBot/actions/workflows/pre-commit.yml/badge.svg?branch=main" alt="Pre-commit Checks">
</div>
<div align=center>
  <img src="https://wakatime.com/badge/user/637d5886-8b47-4b82-9264-3b3b9d6add67/project/a4557f7b-4d26-4105-842a-7a783cbad588.svg" alt="wakatime">
  <img src="https://img.shields.io/badge/ModelScope-Dataset-644cfd?link=https://www.modelscope.cn/datasets/Moemuu/Muice-Dataset" alt="ModelScope">
  <img src="https://img.shields.io/badge/HuggingFace-Dataset-yellow?link=https%3A%2F%2Fhuggingface.co%2Fdatasets%2FMoemu%2FMuice-Dataset" alt="HuggingFace">
  <a href='https://pd.qq.com/s/d4n2xp45i'><img src="https://img.shields.io/badge/QQ频道-沐雪的小屋-blue" alt="Stars"></a>
</div>
<div align=center>
  <a href="https://bot.snowy.moe">📃使用文档</a>
  <a href="https://bot.snowy.moe/guide/setup.html">✨快速开始</a>
</div>


> [!NOTE]
>
> 欢迎来到本项目！目前此项目尚处于预发布状态，运行时可能会遇到一些问题。请务必向我们反馈在运行时遇到的各种错误！
>
> 由于本项目待实现的功能还有很多，因此近期没有也可能永远也不会有**发布**正式版或商店的打算。


# 介绍✨

沐雪，一只会**主动**找你聊天的 AI 女孩子，其对话模型基于 [Qwen](https://github.com/QwenLM) 微调而成，训练集体量 3k+ ，具有二次元女孩子的说话风格，比较傲娇，但乐于和你分享生活的琐碎，每天会给你不一样的问候。

# 功能🪄

✅ 内嵌多种模型加载器，比如 [Llmtuner](https://github.com/hiyouga/LLaMA-Factory) 和 [OpenAI](https://platform.openai.com/docs/overview) ，可加载市面上大多数的模型服务或本地模型，部分支持多模态（图片识别）。另外还附送只会计算 3.9 > 3.11 的沐雪 Roleplay 微调模型一枚~

✅ 使用 `nonebot_plugin_alconna` 作为通用信息接口，支持市面上的大多数适配器，当然也对一些常见的适配器做了优化

✅ 支持基于 `nonebot_plugin_apscheduler` 的定时任务，可定时向大语言模型交互或直接发送信息

✅ 支持基于 `nonebot_plugin_alconna` 的几条常见指令。什么，没有群管理指令？下次再说吧（bushi）

✅ 使用 SQLite3 保存对话数据。那有人就要问了：Maintainer，Maintainer，能不能实现长期短期记忆、LangChain、FairSeq 这些记忆优化啊，实在不行，多模态图像数据保存和最大记忆长度总该有吧。很抱歉，都没有（

# 本项目适合谁？

- 拥有编写过 Python 程序经验的开发者

- 搭建过 Nonebot 项目的 bot 爱好者

- 想要随时随地和大语言模型交互并寻找着能够同时兼容市面上绝大多数 SDK 的机器人框架的 AI 爱好者

# TODO📝

- [X] Function Call 插件系统

- [X] 多模态模型：工具集支持

- [ ] OFA 图像识别。既然都有了多模态为什么还用 OFA？好吧，因为没钱调用接口

- [ ] Faiss 记忆优化。沐雪总记不太清楚上一句话是什么

- [ ] 短期记忆和长期记忆优化。总感觉这是提示工程师该做的事情，~~和 Bot 没太大关系~~

- [ ] （多）对话语音合成器。比如 [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS) 、[RVC](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI)之类的。

- [ ] 发布。我知道你很急，但是你先别急。


近期更新路线：[MuiceBot 更新计划](https://github.com/users/Moemu/projects/2)

# 使用教程💻

参考 [使用文档](https://bot.snowy.moe)


# 关于🎗️

本项目基于 [BSD 3](https://github.com/Moemu/nonebot-plugin-muice/blob/main/LICENSE) 许可证提供（暂定），出现特殊用途时请仔细阅读许可证中的规定

本项目标识使用了 [nonebot/nonebot2](https://github.com/nonebot/nonebot2) 和 画师 [Nakkar](https://www.pixiv.net/users/28246124) ~~[Pixiv作品](https://www.pixiv.net/artworks/101063891)~~ 的资产或作品。如有侵权，请及时与我们联系

对于沐雪的人设和未明确注明许可证和使用范围的模型文件，虽然没有明确限制，但十分不建议将其作为商业用途

此项目中基于或参考了部分开源项目的实现，在这里一并表示感谢：

- [nonebot/nonebot2](https://github.com/nonebot/nonebot2) 本项目使用的机器人框架

- [@botuniverse](https://github.com/botuniverse) 负责制定 Onebot 标准的组织

- [@Tencent](https://github.com/Tencent) 封了我两个号，直接导致本项目的出现

感谢各位开发者的协助，这里就不一一列举出名字了：

<a href="https://github.com/eryajf/Moemu/MuiceBot/contributors">
  <img src="https://contrib.rocks/image?repo=Moemu/MuiceBot"  alt="图片加载中..."/>
</a>

友情链接：[LiteyukiStudio/nonebot-plugin-marshoai](https://github.com/LiteyukiStudio/nonebot-plugin-marshoai)

本项目隶属于 MuikaAI

基于 OneBot V11 的原始实现：[Moemu/Muice-Chatbot](https://github.com/Moemu/Muice-Chatbot)

官方唯一频道：[沐雪的小屋](https://pd.qq.com/s/d4n2xp45i)

<a href="https://www.afdian.com/a/Moemu" target="_blank"><img src="https://pic1.afdiancdn.com/static/img/welcome/button-sponsorme.png" alt="afadian" style="height: 45px !important;width: 163px !important;"></a>
<a href="https://www.buymeacoffee.com/Moemu" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 45px !important;width: 163px !important;" ></a>

Star History：

[![Star History Chart](https://api.star-history.com/svg?repos=Moemu/MuiceBot&type=Date)](https://star-history.com/#Moemu/MuiceBot&Date)