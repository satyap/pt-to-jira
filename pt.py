import configparser

import requests

BASE = "https://www.pivotaltracker.com/services/v5"
RAW_BASE = "https://www.pivotaltracker.com/"

secrets = configparser.ConfigParser()
secrets.read("secrets.ini")

API_TOKEN = secrets["general"]["pt"]


class Pagination:
    def __init__(self, resp: requests.Response):
        self.limit = int(resp.headers["X-Tracker-Pagination-Limit"])
        self.offset = int(resp.headers["X-Tracker-Pagination-Offset"])
        self.returned = int(resp.headers["X-Tracker-Pagination-Returned"])
        self.total = int(resp.headers["X-Tracker-Pagination-Total"])
        # print(f"offset: {self.offset}, limit: {self.limit}, returned: {self.returned}, total: {self.total}")

    @property
    def next_offset(self) -> int:
        return self.offset + self.returned


def get(path, base=BASE, **kwargs):
    resp = requests.get(
        base + path,
        headers={
            "Content-Type": "application.json",
            "X-TrackerToken": API_TOKEN,
        },
        **kwargs,
    )
    if resp.status_code != 200:
        raise RuntimeError(resp.content)
    return resp


def pages(func, start_offset):
    offset = start_offset
    while True:
        out = func(offset)
        page_info = Pagination(out)
        yield out
        offset = page_info.next_offset
        print(offset)
        if offset >= page_info.total:
            break


def stories(project_id, start_offset):
    fields = ",".join([
        "kind",
        "name",
        "description",
        "labels",
        "created_at",
        "updated_at",
        "requested_by_id",
        "accepted_at",
        "current_state",
        "tasks",
    ])

    def story_page(offset):
        return get(f"/projects/{project_id}/stories?offset={offset}&fields={fields}")

    for page in pages(story_page, start_offset):
        stories_list = page.json()
        for story in stories_list:
            yield story


def comments(project_id, story):
    # No pagination for this endpoint
    fields = ",".join([
        "file_attachments",
        "text",
        "person_id",
        "created_at",
        "updated_at",
    ])
    comments_list = get(
        f"/projects/{project_id}/stories/{story['id']}/comments?fields={fields}")
    for comment in comments_list.json():
        yield comment


def get_attachment(attachment, tempfile):
    with get(attachment["download_url"], base=RAW_BASE, stream=True) as resp:
        if resp.status_code == 200:
            for c in resp.iter_content(chunk_size=None):  # stream as it comes in
                tempfile.write(c)
            return
        else:
            raise RuntimeError(f"getting attachment: {resp.status_code} {resp.content}")
