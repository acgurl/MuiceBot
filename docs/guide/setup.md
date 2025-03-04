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