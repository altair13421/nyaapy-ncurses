# nyaa_tui.py
import curses
import json
import os
from typing import Any, Literal
from automator.nyaa import search_torrent
from automator import SUB_CATEGORY_COLORS, get_categories
from automator.downloader import TorrentClient, Status

client = TorrentClient(download_dir=".")

CONFIG_FILE = os.path.join(".", "configs.json")


def _add_text(window, y: int, x: int, text: str, attr: int = 0) -> None:
    height, width = window.getmaxyx()
    if 0 <= y < height and 0 <= x < width - 1:
        window.addnstr(y, x, str(text), width - x - 1, attr)


def _viewport(height: int, count: int, selected: int, start: int) -> tuple[int, int]:
    visible = max(0, height - 8)
    if not count or not visible:
        return 0, visible

    selected = min(max(selected, 0), count - 1)
    start = min(max(start, 0), max(0, count - visible))
    if selected < start:
        start = selected
    elif selected >= start + visible:
        start = selected - visible + 1
    return start, visible


def _terminal_color(rgb: tuple[int, int, int]) -> int:
    basic_colors = [
        (0, 0, 0),
        (128, 0, 0),
        (0, 128, 0),
        (128, 128, 0),
        (0, 0, 128),
        (128, 0, 128),
        (0, 128, 128),
        (192, 192, 192),
        (128, 128, 128),
        (255, 0, 0),
        (0, 255, 0),
        (255, 255, 0),
        (0, 0, 255),
        (255, 0, 255),
        (0, 255, 255),
        (255, 255, 255),
    ]
    candidates = list(enumerate(basic_colors[: min(curses.COLORS, 16)]))
    if curses.COLORS >= 256:
        index = 16
        for red in range(6):
            for green in range(6):
                for blue in range(6):
                    candidates.append(
                        (
                            index,
                            tuple(
                                0 if value == 0 else 55 + value * 40
                                for value in (red, green, blue)
                            ),
                        )
                    )
                    index += 1
        candidates.extend((232 + step, (8 + step * 10,) * 3) for step in range(24))

    def distance(candidate: tuple[int, int, int]) -> int:
        return sum((actual - target) ** 2 for actual, target in zip(rgb, candidate))

    return min(candidates, key=lambda item: distance(item[1]))[0]


def _init_category_colors(
    categories: dict[str, Any], default_background: int = -1
) -> None:
    if not curses.has_colors():
        return
    if curses.COLOR_PAIRS > 4:
        foreground = -1 if default_background == -1 else curses.COLOR_WHITE
        curses.init_pair(4, foreground, default_background)
    eight_color_palette = {
        "1": curses.COLOR_BLUE,
        "2": curses.COLOR_GREEN,
        "3": curses.COLOR_MAGENTA,
        "4": curses.COLOR_RED,
        "5": curses.COLOR_CYAN,
        "6": curses.COLOR_YELLOW,
    }
    basic_category_colors = {
        "1": curses.COLOR_BLUE + 8,
        "2": curses.COLOR_GREEN + 8,
        "3": curses.COLOR_MAGENTA + 8,
        "4": curses.COLOR_RED + 8,
        "5": curses.COLOR_CYAN + 8,
        "6": curses.COLOR_YELLOW + 8,
    }
    for category_id, category in categories.items():
        pair = 4 + int(category_id)
        if pair >= curses.COLOR_PAIRS:
            continue
        if curses.COLORS <= 8:
            foreground = eight_color_palette[category_id]
        elif curses.COLORS <= 16:
            foreground = basic_category_colors[category_id]
        else:
            red, green, blue = (
                int(category["color"][index : index + 2], 16)
                for index in (1, 3, 5)
            )
            foreground = _terminal_color((red, green, blue))
        curses.init_pair(
            pair,
            foreground,
            default_background,
        )
    for subcategory_id, color in SUB_CATEGORY_COLORS.items():
        pair = 10 + int(subcategory_id)
        if pair >= curses.COLOR_PAIRS:
            continue
        if curses.COLORS <= 8:
            foreground = {
                "1": curses.COLOR_CYAN,
                "2": curses.COLOR_GREEN,
                "3": curses.COLOR_MAGENTA,
                "4": curses.COLOR_WHITE,
            }[subcategory_id]
        elif curses.COLORS <= 16:
            foreground = {
                "1": curses.COLOR_CYAN + 8,
                "2": curses.COLOR_GREEN + 8,
                "3": curses.COLOR_MAGENTA + 8,
                "4": curses.COLOR_WHITE,
            }[subcategory_id]
        else:
            rgb = tuple(
                int(color[index : index + 2], 16) for index in (1, 3, 5)
            )
            foreground = _terminal_color(rgb)
        curses.init_pair(pair, foreground, default_background)


def _prompt(stdscr, title: str, prompt: str, initial: str = "") -> str | None:
    height, width = stdscr.getmaxyx()
    if height < 6 or width < 24:
        return None

    box_height = 6
    box_width = min(width - 2, max(40, min(76, len(prompt) + 8)))
    top = max(0, (height - box_height) // 2)
    left = max(0, (width - box_width) // 2)
    dialog = curses.newwin(box_height, box_width, top, left)
    dialog.keypad(True)
    if curses.has_colors():
        dialog.bkgd(" ", curses.color_pair(4))
    value = initial
    field_width = box_width - 4

    try:
        curses.curs_set(1)
        while True:
            dialog.erase()
            dialog.box()
            _add_text(dialog, 1, 2, title)
            _add_text(dialog, 2, 2, prompt)
            _add_text(dialog, 3, 2, value[-field_width:])
            _add_text(dialog, 4, 2, "Enter: confirm  Esc: cancel")
            dialog.move(3, min(2 + len(value), box_width - 2))
            dialog.refresh()

            key = dialog.get_wch()
            if key in ("\x1b", 27):
                return None
            if key in ("\n", "\r", 10, 13, curses.KEY_ENTER):
                return value.strip()
            if key in (curses.KEY_BACKSPACE, "\b", "\x7f", 8, 127):
                value = value[:-1]
            elif key == "\x15":
                value = ""
            elif isinstance(key, str) and key.isprintable() and len(value) < 4096:
                value += key
    finally:
        curses.curs_set(0)


def _select_menu(
    stdscr,
    title: str,
    items: list[tuple[str, int]],
    selected: int = 0,
) -> int | None:
    height, width = stdscr.getmaxyx()
    if height < 7 or width < 24 or not items:
        return None

    menu_height = min(height - 2, len(items) + 4)
    menu_width = min(width - 2, 72)
    top = (height - menu_height) // 2
    left = (width - menu_width) // 2
    menu = curses.newwin(menu_height, menu_width, top, left)
    menu.keypad(True)
    first_visible = 0
    selected = min(max(selected, 0), len(items) - 1)

    while True:
        menu.erase()
        menu.box()
        _add_text(menu, 1, 2, title, curses.A_BOLD)
        visible_count = menu_height - 4
        if selected < first_visible:
            first_visible = selected
        elif selected >= first_visible + visible_count:
            first_visible = selected - visible_count + 1

        for row in range(visible_count):
            index = first_visible + row
            if index >= len(items):
                break
            label, attr = items[index]
            marker = "> " if index == selected else "  "
            _add_text(menu, row + 2, 2, marker + label, attr | (
                curses.A_BOLD if index == selected else curses.A_NORMAL
            ))
        _add_text(menu, menu_height - 2, 2, "Up/Down Select  Enter Confirm  Esc Cancel")
        menu.refresh()

        key = menu.getch()
        if key in (27,):
            return None
        if key in (curses.KEY_ENTER, 10, 13):
            return selected
        if key == curses.KEY_UP:
            selected = max(0, selected - 1)
        elif key == curses.KEY_DOWN:
            selected = min(len(items) - 1, selected + 1)
        elif key == curses.KEY_PPAGE:
            selected = max(0, selected - visible_count)
        elif key == curses.KEY_NPAGE:
            selected = min(len(items) - 1, selected + visible_count)


def get_config() -> dict[str, Any]:
    with open(CONFIG_FILE) as config_read:
        config = json.load(config_read)
    return config


def create_config(config: dict["str", Any]) -> bool:
    try:
        with open(CONFIG_FILE, "w") as config_write:
            config_write.write(json.dumps(config, indent=4, sort_keys=False))
        return True
    except Exception:
        return False


class UniversalTorrentor:
    def __init__(self):
        self.config = get_config()["config"]
        self.selected = 0

    def add_torrent(self, data: dict):
        # get labels and Magnet, only that is Required
        client.add_torrent(
            torrent_=data["magnet"],
            download_dir=data.get("download_dir", None),
            paused=self.config["paused"],
            labels=data.get("labels", []),
        )

    @staticmethod
    def check_if_quitable():
        torrents = client.get_torrents()
        active = []
        for torrent in torrents:
            if torrent["status"] == Status.DOWNLOADING:
                active.append(torrent)
        return len(active) == 0

    def get_torrents(self):
        return client.get_torrents()

    def draw_finalizing_dialog(
        self, stdscr, height, width, selected_idx: int = 0, magnet: str | None = None
    ):
        if magnet is not None:
            data = {
                "magnet": magnet.decode("utf-8") if isinstance(magnet, bytes) else magnet,
                "title": "Manual magnet",
                "size": "Unknown",
                "labels": ["manual"],
                "download_dir": self.config["download_dir"],
            }
        else:
            if not 0 <= selected_idx < len(self.torrents):
                return
            selected_torrent = self.torrents[selected_idx]
            data = {
                "title": selected_torrent["title"],
                "size": selected_torrent["size"],
                "labels": [
                    label.strip()
                    for label in selected_torrent["category"].split("-")
                    if label.strip()
                ],
                "magnet": selected_torrent["magnet"],
                "download_dir": self.config["download_dir"],
            }

        labels = _prompt(
            stdscr,
            f"Add: {data['title']}",
            "Labels (comma-separated):",
            ", ".join(data["labels"]),
        )
        if labels is None:
            return
        data["labels"] = [label.strip() for label in labels.split(",") if label.strip()]

        download_dir = _prompt(
            stdscr,
            "Download location",
            "Path (Enter keeps current):",
            data["download_dir"],
        )
        if download_dir is None:
            return
        data["download_dir"] = download_dir or self.config["download_dir"]

        confirm = _prompt(
            stdscr,
            f"Confirm: {data['title']}",
            "Type y to add this torrent:",
        )
        if confirm is not None and confirm.lower() in ("y", "yes"):
            self.add_torrent(data)


class Torrenting(UniversalTorrentor):
    def __init__(self):
        self.torrents = []
        self.selected = 0
        self.start_index = 0
        self.status_message = ""
        self.config = get_config()["config"]
        self.current_state: Literal["active", "stopped", "finished"] = "stopped"

    def stop_torrents(self):
        client.stop_all_torrents()
        self.current_state = "stopped"

    def stop_torrent(self, torrent_idx):
        client.stop_torrent(torrent_idx)

    def start_torrent(self, torrent_idx):
        client.start_torrent(torrent_idx)

    def finished(self, status, progress):
        return (status in ['stopped'] and float(progress) == 100)

    def start_torrents(self):
        client.start_all()
        self.current_state = "active"

    def delete(self, stdscr, selected_idx):
        if not 0 <= selected_idx < len(self.torrents):
            return
        torrent = self.torrents[selected_idx]
        answer = _prompt(
            stdscr,
            f"Remove: {torrent['name']}",
            "Delete downloaded data? Type y to confirm:",
        )
        if answer is not None:
            client.remove_torrent(
                torrent["id"], delete_data=answer.lower() in ("y", "yes")
            )

    def draw_header(self, stdscr, height, width):
        """Draw application header"""
        # Title
        _add_text(stdscr, 0, 2, "TORRENT QUEUE", curses.A_BOLD)
        stats = f"{len(self.torrents)} torrents  |  {self.current_state}"
        _add_text(stdscr, 1, 2, stats)
        _add_text(stdscr, 2, 2, "=" * (width - 3))

    def get_color_on_status(self, status):
        if status == "seeding":
            return curses.color_pair(2)
        elif status == "downloading":
            return curses.color_pair(1)
        elif status == "stopped":
            return curses.color_pair(3)
        return None

    def draw_torrents(self, stdscr, height, width):
        self.torrents = self.get_torrents()
        self.selected = min(self.selected, max(0, len(self.torrents) - 1))
        self.start_index, visible = _viewport(
            height, len(self.torrents), self.selected, self.start_index
        )
        for row in range(visible):
            index = self.start_index + row
            if index >= len(self.torrents):
                break
            torrent = self.torrents[index]
            speed = torrent["get_speed"]
            progress = float(torrent["progress"])
            text = (
                f"{torrent['status']:<12} {progress:5.1f}%  "
                f"{torrent['formatted_size'][0]:.1f} {torrent['formatted_size'][1]:<3}  "
                f"{speed[0]:.1f} {speed[1]:<3}  {torrent['name']}"
            )
            attr = self.get_color_on_status(torrent["status"]) or 0
            if index == self.selected:
                attr |= curses.A_REVERSE
            _add_text(stdscr, row + 3, 2, text, attr)
        if self.torrents:
            _add_text(
                stdscr,
                height - 5,
                2,
                f"{self.selected + 1}/{len(self.torrents)}",
            )


    # this is for when you are adding a magnet link, will use the same logic for the main Torrent Adding
    def add_torrent_dialog(self, stdscr, height, width):
        magnet = _prompt(stdscr, "Add a torrent", "Magnet URI:")
        if magnet is None or not magnet:
            return
        if not magnet.startswith("magnet:?"):
            self.status_message = "Not added: enter a valid magnet URI."
            return
        self.draw_finalizing_dialog(stdscr, height, width, magnet=magnet)

    def draw_footer(self, stdscr, height, width):
        """Draw help/status footer"""
        # Separator
        _add_text(stdscr, height - 4, 0, "-" * (width - 1))
        help_text = "Up/Down Select  s Start/stop  S All  a Add magnet  d Remove  T Switch screen  q Quit"
        _add_text(stdscr, height - 2, 2, help_text)
        if self.status_message:
            _add_text(stdscr, height - 3, 2, self.status_message)
            self.status_message = ""

    def draw_ui(self, stdscr):
        """Main UI drawing function"""
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        self.draw_header(stdscr, height, width)
        self.draw_torrents(stdscr, height, width)
        self.draw_footer(stdscr, height, width)
        stdscr.refresh()

    def handle_input(self, stdscr, key):
        page_size = max(1, stdscr.getmaxyx()[0] - 8)
        if key == curses.KEY_UP:
            self.selected = max(0, self.selected - 1)
        elif key == curses.KEY_DOWN:
            self.selected = min(max(0, len(self.torrents) - 1), self.selected + 1)
        elif key == curses.KEY_PPAGE:
            self.selected = max(0, self.selected - page_size)
        elif key == curses.KEY_NPAGE:
            self.selected = min(max(0, len(self.torrents) - 1), self.selected + page_size)
        elif key == ord("S"):
            if self.current_state == "active":
                self.stop_torrents()
            elif self.current_state == "stopped":
                self.start_torrents()
        elif key == ord("s"):
            if not self.torrents:
                return
            torrent = self.torrents[self.selected]
            if torrent["status"] == "seeding" or torrent["status"] == "downloading":
                self.stop_torrent(torrent["id"])
            elif torrent["status"] == "stopped" and torrent["progress"] < 100:
                self.start_torrent(torrent["id"])
        elif key == ord("d"):
            self.delete(stdscr, self.selected)

        elif key == ord("a"):
            self.add_torrent_dialog(stdscr, *stdscr.getmaxyx())


class NyaaHelper:
    def __init__(self): ...

    def search(self):
        return search_torrent(
            search=self.query,
            category=self.category,
            sub_category=self.sub_category,
            page=self.page,
            sukebei=self.sukebei,
        )

    def startup(self):
        torrents = self.search()
        self.torrents = torrents

    def get_category(self, cat_string):
        cat, sub_cat = cat_string.split("_")
        if cat == "0" and sub_cat == "0":
            return "All"
        if sub_cat == "0":
            return f"{self.categories[cat]['name']} - All"
        return f"{self.categories[cat]['name']} - {self.categories[cat]['sub_cats'][sub_cat]}"


class NyaaScreen(NyaaHelper, UniversalTorrentor):
    def __init__(self):
        self.categories = get_categories()
        self.config: dict[str, Any] = get_config()["config"]
        self.torrents = []
        self.query = ""
        self.filter = 0
        self.category = 0
        self.sub_category = 0
        self.page = 1
        self.running = True
        self.selected = 0
        self.start_index = 0
        self.status_message = ""
        self.sukebei = False
        self.startup()
        self.filter_mode = ""  # Added missing attribute filter_mode

    def draw_header(self, stdscr, height, width):
        _add_text(stdscr, 0, 2, "NYAA SEARCH", curses.A_BOLD)
        source = "Sukebei" if self.sukebei else "Nyaa"
        search = self.query or "all torrents"
        category = self.get_category(f"{self.category}_{self.sub_category}")
        stats = f"{source}  |  {len(self.torrents)} results  |  Search: {search}  |  Category: {category}"
        _add_text(stdscr, 1, 2, stats)
        _add_text(stdscr, 2, 2, "=" * (width - 3))

    def draw_footer(self, stdscr, height, width):
        """Draw help/status footer"""
        _add_text(stdscr, height - 4, 0, "-" * (width - 1))
        _add_text(
            stdscr,
            height - 2,
            2,
            "Up/Down Navigate  PgUp/PgDn Page  s Search  f Filter  r Reset  P Source  d Download  T Queue  q Quit",
        )
        if self.status_message:
            _add_text(stdscr, height - 3, 2, self.status_message)
            self.status_message = ""


    def draw_torrents(self, stdscr, height, width):
        self.selected = min(self.selected, max(0, len(self.torrents) - 1))
        self.start_index, visible = _viewport(
            height, len(self.torrents), self.selected, self.start_index
        )
        for row in range(visible):
            index = self.start_index + row
            if index >= len(self.torrents):
                break
            torrent = self.torrents[index]
            category_ids = torrent.get("categoryid", [])
            category_id = category_ids[0] if category_ids else None
            subcategory_id = category_ids[1] if len(category_ids) > 1 else None
            category_info = self.categories.get(category_id)
            category_name = (
                category_info["name"]
                if category_info is not None
                else torrent["category"]
            )
            subcategory_name = (
                category_info["sub_cats"].get(subcategory_id)
                if category_info is not None
                else None
            )
            if subcategory_name is None and " - " in torrent["category"]:
                category_name, subcategory_name = torrent["category"].split(" - ", 1)

            prefix = (
                f"{'>' if index == self.selected else ' '} "
                f"{torrent['size']:<10}  S:{torrent['seeders']:>4}  "
                f"L:{torrent.get('leechers', 0):>4}  "
            )
            category_text = (
                f"{category_name} - {subcategory_name}"
                if subcategory_name
                else category_name
            )
            text = f"{prefix}{category_text}  {torrent['title']}"
            attr = curses.A_BOLD if index == self.selected else curses.A_NORMAL
            _add_text(stdscr, row + 3, 2, text, attr)
            category_x = 2 + len(prefix)
            if category_id in self.categories and curses.has_colors():
                category_attr = (
                    curses.color_pair(4 + int(category_id)) | curses.A_BOLD
                )
                _add_text(
                    stdscr,
                    row + 3,
                    category_x,
                    category_name,
                    category_attr,
                )
            if (
                subcategory_name
                and subcategory_id in SUB_CATEGORY_COLORS
                and curses.has_colors()
            ):
                subcategory_attr = (
                    curses.color_pair(10 + int(subcategory_id)) | curses.A_BOLD
                )
                _add_text(
                    stdscr,
                    row + 3,
                    category_x + len(category_name) + 3,
                    subcategory_name,
                    subcategory_attr,
                )
        if self.torrents:
            _add_text(
                stdscr,
                height - 5,
                2,
                f"{self.selected + 1}/{len(self.torrents)}",
            )

    def handle_input(self, stdscr, key):
        page_size = max(1, stdscr.getmaxyx()[0] - 8)
        # Navigation
        if key == curses.KEY_UP:
            self.selected = max(0, self.selected - 1)
        elif key == curses.KEY_DOWN:
            self.selected = min(max(0, len(self.torrents) - 1), self.selected + 1)
        elif key == curses.KEY_PPAGE:
            self.selected = max(0, self.selected - page_size)
        elif key == curses.KEY_NPAGE:
            self.selected = min(max(0, len(self.torrents) - 1), self.selected + page_size)

        # No Page Stuff
        # elif key == curses.KEY_LEFT:
        #     if self.page > 1:
        #         self.page -= 1
        #     self.torrents = self.search()
        # elif key == curses.KEY_RIGHT:
        #     self.page += 1
        #     self.torrents = self.search()
        # main UI
        elif key == ord("s"):
            self.handle_search(stdscr)
        elif key == ord("P"):
            self.sukebei = not self.sukebei
            self.torrents = self.search()
            self.selected = 0
            self.start_index = 0
        elif key == ord("f"):
            self.handle_filter(stdscr)
        elif key == ord("d"):
            height, width = stdscr.getmaxyx()
            self.draw_finalizing_dialog(stdscr, height, width, self.selected)
        elif key == ord("r"):
            self.query = ""
            self.category = 0
            self.sub_category = 0
            self.sukebei = False
            self.torrents = self.search()
            self.selected = 0
            self.start_index = 0

    def handle_filter(self, stdscr):
        category_items = [("All categories", curses.A_NORMAL)]
        category_ids = list(self.categories)
        for category_id in category_ids:
            category = self.categories[category_id]
            attr = (
                curses.color_pair(4 + int(category_id)) | curses.A_BOLD
                if curses.has_colors()
                else curses.A_NORMAL
            )
            category_items.append((category["name"], attr))

        current_category = str(self.category)
        initial_category = (
            category_ids.index(current_category) + 1
            if current_category in category_ids
            else 0
        )
        category_selection = _select_menu(
            stdscr, "Filter by category", category_items, initial_category
        )
        if category_selection is None:
            return

        if category_selection == 0:
            self.category = 0
            self.sub_category = 0
        else:
            category_id = category_ids[category_selection - 1]
            subcategories = self.categories[category_id]["sub_cats"]
            subcategory_items = [("All subcategories", curses.A_NORMAL)]
            for subcategory_id, subcategory in subcategories.items():
                color = SUB_CATEGORY_COLORS.get(subcategory_id)
                attr = curses.A_BOLD
                if color and curses.has_colors():
                    attr |= curses.color_pair(10 + int(subcategory_id))
                subcategory_items.append((subcategory, attr))

            current_subcategory = str(self.sub_category)
            initial_subcategory = (
                list(subcategories).index(current_subcategory) + 1
                if current_category == category_id
                and current_subcategory in subcategories
                else 0
            )
            subcategory_selection = _select_menu(
                stdscr,
                f"{self.categories[category_id]['name']} subcategory",
                subcategory_items,
                initial_subcategory,
            )
            if subcategory_selection is None:
                return
            self.category = int(category_id)
            self.sub_category = (
                int(list(subcategories)[subcategory_selection - 1])
                if subcategory_selection
                else 0
            )

        self.torrents = self.search()
        self.selected = 0
        self.start_index = 0

    def handle_search(self, stdscr):
        text = _prompt(stdscr, "Search Nyaa", "Search terms:")
        if text is None:
            return
        self.query = text
        self.torrents = self.search()
        self.selected = 0
        self.start_index = 0

    def draw_ui(self, stdscr):
        """Main UI drawing function"""
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        self.draw_header(stdscr, height, width)
        self.draw_torrents(stdscr, height, width)
        self.draw_footer(stdscr, height, width)
        stdscr.refresh()


class TerminalUI:
    def __init__(self, offline_mode = False):
        self.running = True
        if offline_mode:
            self.screens = {
                "TorrentScreen": Torrenting()
            }
        else:
            self.screens = {
                "TorrentScreen": Torrenting(),
                "NyaaScreen": NyaaScreen(),
            }
        self.active_screen = self.get_home_screen()

    def get_home_screen(self):
        screen_keys = list(self.screens.keys())
        return screen_keys[0]

    def get_next_screen(self):
        screen_keys = list(self.screens.keys())
        current_idx = screen_keys.index(self.active_screen)
        self.active_screen = screen_keys[(current_idx + 1) % len(screen_keys)]

    def copy_to_clipboard(self, index): ...

    def draw_ui(self, stdscr):
        self.screens[self.active_screen].draw_ui(stdscr)

    def handle_quit(self, stdscr):
        if UniversalTorrentor.check_if_quitable():
            self.running = False
            return
        answer = _prompt(
            stdscr,
            "Active downloads",
            "Quit while torrents are downloading? Type y to confirm:",
        )
        self.running = answer is not None and answer.lower() in ("y", "yes")
        return

    def handle_input(self, stdscr, key):
        if key == ord("q"):
            self.handle_quit(stdscr)

        elif key == ord("T"):
            self.get_next_screen()

        else:
            self.screens[self.active_screen].handle_input(stdscr, key)

    def run(self, stdscr):
        """Main application loop"""
        # Setup
        curses.curs_set(0)  # Hide cursor
        stdscr.nodelay(0)  # Wait for input
        stdscr.keypad(True)
        stdscr.clear()
        if curses.has_colors():
            curses.start_color()
            default_background = curses.COLOR_BLACK
            try:
                curses.use_default_colors()
                default_background = -1
            except curses.error:
                pass
            curses.init_pair(1, curses.COLOR_GREEN, default_background)
            curses.init_pair(2, curses.COLOR_CYAN, default_background)
            curses.init_pair(3, curses.COLOR_YELLOW, default_background)
            _init_category_colors(get_categories(), default_background)
            stdscr.bkgd(" ", curses.color_pair(4))

        # Main loop
        while self.running:
            self.draw_ui(stdscr)

            try:
                key = stdscr.getch()
                self.handle_input(stdscr, key)
            except KeyboardInterrupt:
                self.running = False
            except Exception as e:
                self.draw_error(stdscr, str(e))

        curses.curs_set(1)

    def draw_error(self, stdscr, message):
        """Draw error message on the screen"""
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        error_msg = f"Error: {message}"
        _add_text(stdscr, height // 2, 2, error_msg, curses.A_BOLD)
        stdscr.refresh()
        stdscr.getch()  # Wait for user to acknowledge
        self.running = False


def main(offline_mode = False):
    app = TerminalUI(offline_mode=offline_mode)
    curses.wrapper(app.run)


if __name__ == "__main__":
    main()
