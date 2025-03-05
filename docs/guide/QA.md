# 常见问题

这里收录了一些常见的问题，请务必在查阅本文档和上网查询后再提交 issue

## 已知 Bugs

1. 当 Telegram 适配器收到两张图片时，会触发两次事件

2. QQ频道 Bot 图片消息会触发两次事件

## 常见报错及解决方案

### HTTPSConnectionPool(host='multimedia.nt.qq.com.cn', port=443): Max retries exceeded with url

> Caused by SSLErrr(SSLErPOr(1, '[SSL: SSLV3 ALERT HANDSHAKE FAILURE] ssIv3 alert handshake failure ( ss1.c:1806)'))

临时解决方法：降级 `urllib3` 到 `1.26.0`，但这样做可能会导致依赖冲突，目前还没找到比较好的方案

```shell
pip install urllib3==1.26.0
```

