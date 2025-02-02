import re


def get_video_id_by_url(url: str) -> str | None:
    matched = re.match(
        r"^((?:https?:)?//)?((?:www|m)\.)?((?:youtube(-nocookie)?\.com|youtu\.be))(/(?:[\w\-]+\?v=|embed/|live/|v/)?)([\w\-]{11})([?&]\S+)?$",
        url,
        re.IGNORECASE | re.MULTILINE
    )
    if matched:
        return matched.group(6)
    return None