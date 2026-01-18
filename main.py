import argparse
from rich.console import Console
from rich.table import Table

if __name__ == "__main__":
    from automator import nyaa

    parser = argparse.ArgumentParser(
        description="Viewer, Downloader, and Stuff doer for nyaa.si",
    )
    parser.add_argument("-search", help="items To Search", type=str)
    parser.add_argument(
        "-user", help="Provider/User like AkihitoSubsWeeklies, and YuiSubs", type=str
    )
    parser.add_argument(
        "-category",
        help="Get specific Category for it, Check readme for this",
        type=int,
    )
    parser.add_argument(
        "-sub_category",
        help="Get specific sub Category for it, Check readme for this",
        type=int,
    )
    parser.add_argument("-filter", help="Filter", type=int)
    parser.add_argument("-page", help="On page", type=int)
    parser.add_argument(
        "-download",
        nargs="+",
        help="DOWNLOAD this Torrent and Download the Data too, Or Just Start the Magnet, Use Quotations,\
        You can Even Point To a Torrent File, and It will Download, No matter which Porn",
        type=str,
    )

    args = parser.parse_args()
    if not args.download:
        data = nyaa.search_torrent(
            search=args.search if not None else "",
            user=args.user,
            category=args.category if not None else 0,
            sub_category=args.sub_category if not None else 0,
            filter=args.filter if not None else 0,
            page=args.page if not None else 1,
        )
        table = Table(title=f"{args.search}'s Torrents")
        table.add_column("Category", justify="right", style="red")
        table.add_column("Title", style="cyan")
        table.add_column("Size", style="green")
        table.add_column("Link", style="magenta")
        # table.add_column('magenet', style='magenta')
        for item in data:
            if item["title"].__contains__("[/a/nonymous]"):
                item["title"] = item["title"].replace("[/a/nonymous]", "")
            table.add_row(
                item["category"],
                item["title"],
                item["size"],
                item["torrent_link"],
            )
        console = Console()
        console.print(table)
        # Make a selector Using Questionary library?
    else:
        from automator.downloader import download_torrent
        import re

        regex = re.compile(
            r"^(?:http|ftp)s?://"  # http:// or https://
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"  # domain...
            r"localhost|"  # localhost...
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
            r"(?::\d+)?"  # optional port
            r"(?:/?|[/?]\S+)$",
            re.IGNORECASE,
        )
        for download in args.download:
            title = download.split("/")[-1]
            if re.match(regex, download):
                download_torrent(torrent_link=download, title=title, verbose=True)
            else:
                download_torrent(magnet=download, title=title, verbose=True)
