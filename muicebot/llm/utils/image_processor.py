import re
from typing import List

from nonebot import logger
from nonebot_plugin_alconna.uniseg import Image


def extract_image_urls(text: str) -> List[str]:
    """
    从文本中提取图片URL

    支持的格式:
    1. Markdown格式: ![alt](url)
    2. HTML格式: <img src="url">
    3. 纯URL格式（独立成行的URL）

    :param text: 输入文本
    :return: 图片URL列表
    """
    if not text or not isinstance(text, str):
        return []

    # Markdown图片语法 ![alt](url)
    markdown_pattern = r"!\[.*?\]\((https?://[^\s\)]+\.(?:jpe?g|png|gif|webp|bmp|svg))\)"

    # HTML img标签
    html_pattern = r'<img.*?src=["\'](https?://[^\s"\'>]+\.(?:jpe?g|png|gif|webp|bmp|svg))["\'].*?>'

    markdown_urls = re.findall(markdown_pattern, text, re.IGNORECASE)
    html_urls = re.findall(html_pattern, text, re.IGNORECASE)

    # 查找纯URL（逐行检查）
    url_urls = []
    for line in text.split("\n"):
        line = line.strip()
        # 检查是否为独立的图片URL
        if re.match(r"^https?://[^\s\)]+\.(?:jpe?g|png|gif|webp|bmp|svg)(?:\?[^\s]*)?$", line, re.IGNORECASE):
            url_urls.append(line)

    # 合并并去重
    all_urls = list(set(markdown_urls + html_urls + url_urls))

    logger.debug(f"从文本中提取到 {len(all_urls)} 个图片URL: {all_urls}")
    return all_urls


def create_image_segments(urls: List[str]) -> List[Image]:
    """
    根据URL列表创建Image对象列表

    :param urls: 图片URL列表
    :return: Image对象列表
    """
    if not urls:
        return []

    image_segments = []
    for url in urls:
        try:
            # 直接使用URL创建Image对象
            image_segment = Image(url=url)
            image_segments.append(image_segment)
        except Exception as e:
            logger.warning(f"创建Image对象失败 URL: {url}, 错误: {e}")

    logger.debug(f"创建了 {len(image_segments)} 个Image对象")
    return image_segments


def remove_image_url_markers(text: str) -> str:
    """
    从文本中移除图片URL标记，只保留描述性文本

    :param text: 输入文本
    :return: 清理后的文本
    """
    if not text or not isinstance(text, str):
        return text or ""

    # 移除Markdown图片语法
    text = re.sub(
        r"!\[.*?\]\(https?://[^\s\)]+\.(?:jpe?g|png|gif|webp|bmp|svg)(?:\?[^\s]*)?\)", "", text, flags=re.IGNORECASE
    )

    # 移除HTML img标签
    text = re.sub(
        r'<img.*?src=["\']https?://[^\s"\'>]+\.(?:jpe?g|png|gif|webp|bmp|svg)(?:\?[^\s]*)?["\'].*?>',
        "",
        text,
        flags=re.IGNORECASE,
    )

    # 清理多余的空白行和空格
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    cleaned_text = "\n".join(lines)

    logger.debug("已清理文本中的图片URL标记")
    return cleaned_text


def process_model_images(response_text: str) -> tuple[str, List[str]]:
    """
    处理模型响应中的图片，提取URL

    :param response_text: 模型返回的文本
    :return: (清理后的文本, 图片URL列表)
    """
    if not response_text or not isinstance(response_text, str):
        return response_text or "", []

    # 提取图片URL
    image_urls = extract_image_urls(response_text)

    # 移除图片URL标记
    cleaned_text = remove_image_url_markers(response_text)

    logger.info(f"处理模型图片完成: 提取到 {len(image_urls)} 个图片URL")
    return cleaned_text, image_urls
