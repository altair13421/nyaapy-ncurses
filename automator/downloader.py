import os
from typing import Any
from transmission_rpc import Client, Torrent, Status
from transmission_rpc.utils import format_size, format_speed
from pathlib import Path
from datetime import timedelta, datetime

if os.name in ["nt", "Nt", "NT"]:
    home_dir = "."
else:
    home_dir = os.environ.get("HOME")


def create_dir_if_not(dirname: str):
    os.makedirs(dirname, exist_ok=True)
    return True


class TorrentMapper:
    def __init__(self, *args, **kwargs):
        self.id: str = kwargs.get("id")
        self.name: str = kwargs.get("name")
        self.is_finished: bool = kwargs.get("is_finished")
        self.seeding: bool = kwargs.get("seeding")
        self.downloading: bool = kwargs.get("downloading")
        self.checking: bool = kwargs.get("checking")
        self.status: Status = kwargs.get("status")
        self.rate_download: float = kwargs.get("rate_download")
        self.total_size: float = kwargs.get("total_size")
        self.progress: float = kwargs.get("progress")
        self.download_dir: Path = kwargs.get("download_dir")
        self.added_date: datetime = kwargs.get("added_date")
        self.done_date: datetime | None = kwargs.get("done_date")
        self.eta: timedelta | None = kwargs.get("eta")
        self.json = {}
        for (
            kw,
            val,
        ) in kwargs.items():
            if hasattr(self, kw):
                self.json[kw] = val
        self.json["formatted_size"] = self.formatted_size
        self.json["get_speed"] = self.get_speed

    @property
    def formatted_size(self) -> tuple[float, str]:
        return format_size(self.total_size)

    @property
    def get_speed(self) -> tuple[float, str]:
        return format_speed(self.rate_download)



class TorrentClient:
    def __init__(
        self,
        download_dir: str = os.path.join(home_dir, "Downloads"),
        host: str = None,
        port: int = None,
        username: str = None,
        password: str = None,
        log_file: Path = os.path.join(".", "torrent_logs.txt"),
    ):
        self.upload_limit = 10 * 1024
        self.download_dir = download_dir
        create_dir_if_not(self.download_dir)
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.log_file = log_file

        self.client = Client()

    def map_torrent(self, torrent: Torrent) -> TorrentMapper:
        return TorrentMapper(
            **{
                "id": torrent.id,
                "name": torrent.name,
                "is_finished": torrent.is_finished,
                "seeding": torrent.seeding,
                "downloading": torrent.downloading,
                "status": torrent.status,
                "rate_download": torrent.rate_download,
                "total_size": torrent.total_size,
                "progress": torrent.progress,
                "download_dir": torrent.download_dir,
                "added_date": torrent.added_date,
                "done_date": torrent.done_date,
                "eta": torrent.eta,
            }
        )

    def add_torrent(
        self,
        torrent_: str,  # Only magnet right now
        labels: list[str] = [],
        download_dir: str | None = None,
        paused=False,
    ) -> TorrentMapper:
        self.client.add_torrent(
            torrent_,
            download_dir=download_dir or self.download_dir,
            labels=labels,
            paused=paused,
        )
        torrent: Torrent = self.client.get_torrents()[-1]
        return self.map_torrent(torrent)

    def get_current_torrent_data(self, torrent_id: str | int) -> TorrentMapper: ...

    def get_torrents(self) -> list[TorrentMapper]:
        torrents_mapped = []
        torrents = self.client.get_torrents()
        for torrent in torrents:
            torrents_mapped.append(self.map_torrent(torrent).json)
        torrents_mapped.reverse()
        return torrents_mapped

    def start_torrent(self, torrent_id: str | int):
        self.client.start_torrent(torrent_id)
        return self.client.get_torrent(torrent_id).status

    def start_all(self):
        self.client.start_all()

    def set_download_limit(self): ...

    def remove_torrent(self, torrent_id, delete_data: bool = False):
        self.client.remove_torrent(torrent_id, delete_data)

    def move_up_queue(self, torrent_id): ...
    def move_down_queue(self, torrent_id): ...
    def stop_torrent(self, torrent_id):
        self.client.stop_torrent(torrent_id)

    def stop_all_torrents(self):
        for torrent in self.client.get_torrents():
            self.stop_torrent(torrent.id)
