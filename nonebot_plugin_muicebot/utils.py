import nonebot_plugin_localstore as store
import requests

IMG_DIR = store.get_plugin_data_dir() / ".cache" / "images"
IMG_DIR.mkdir(parents=True, exist_ok=True)

User_Agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0"


def save_image(image_url: str, file_name: str) -> str:
    """
    保存图片至本地目录

    :return: 保存后的本地目录
    """
    r = requests.get(image_url, headers={"User-Agent": User_Agent})
    local_path = (IMG_DIR / file_name).resolve()
    with open(local_path, "wb") as file:
        file.write(r.content)
    r.close()
    return str(local_path)
