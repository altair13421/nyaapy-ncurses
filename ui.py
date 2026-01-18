# nyaa_tui.py
import curses
import json
import os
from typing import Any, Literal
from automator.nyaa import search_torrent
from automator import get_categories
from automator.downloader import TorrentClient, Status

client = TorrentClient(download_dir=".")

CONFIG_FILE = os.path.join(".", "configs.json")


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
        self, stdscr, height, width, selected_idx: int, magnet: str = None
    ):
        if magnet:
            data = {
                "magnet": magnet,
                "labels": ["manual"],
            }
        selected_torrent = self.torrents[selected_idx]
        data = {
            "title": selected_torrent["title"],
            "size": selected_torrent["size"],
            "labels": selected_torrent["category"].strip().split("-"),
            "magnet": selected_torrent["magnet"],
        }
        datah, dw = height - 3, 2
        prompth = height - 1
        numh = height - 2
        prompts = [
            "[Separator: ','] Labels: ",
            f"[Relative/Absolute, ] Save Location: {self.config['download_dir']}",
            "[y/n] Finalize:",
        ]
        for i, prompt in enumerate(prompts):
            if data.get("title", "") != "" and data.get("size", 0) != 0:
                stdscr.addstr(
                    datah,
                    dw,
                    f"Size: {data['size']}\t|\t{data['title']}\t|\t{data['labels']}",
                )
            stdscr.addstr(numh, dw, f"{i + 1}/{len(prompts)}")

            stdscr.addstr(prompth, dw, prompt)
            # the input be like
            curses.echo()
            curses.curs_set(1)
            # getting the actual input
            stdscr.refresh()
            try:
                user_input = stdscr.getstr(
                    height - 1, len(prompt) + 2, width - len(prompt) - 4
                )
                text = user_input.decode("utf-8").strip()
                if "Save Location" in prompt:
                    data["download_dir"] = text if text else self.config["download_dir"]
                elif "Labels" in prompt:
                    if text:
                        data["labels"].append(text.split(","))
                elif "Finalize" in prompt:
                    if text in ["y", "Y", "yes", "Yes"]:
                        self.add_torrent(data)
            except Exception:
                pass
            curses.noecho()
            curses.curs_set(0)


class Torrenting(UniversalTorrentor):
    def __init__(self):
        self.torrents = []
        self.selected = 0
        self.current_state: Literal["active", "stopped"] = "stopped"

    def stop_torrents(self):
        client.stop_all_torrents()
        self.current_state = "stopped"

    def stop_torrent(self, torrent_idx):
        client.stop_torrent(torrent_idx)

    def start_torrent(self, torrent_idx):
        client.start_torrent(torrent_idx)

    def start_torrents(self):
        client.start_all()
        self.current_state = "active"

    def delete(self, stdscr, selected_idx):
        """Simple input dialog"""
        h, w = stdscr.getmaxyx()
        torrent = self.torrents[selected_idx]
        # Show input prompt
        prompt = "Delete data? (y/N): "
        stdscr.addstr(h - 3, 2, prompt, curses.A_BOLD)

        # Setup for input
        curses.echo()
        curses.curs_set(1)

        # Get input
        stdscr.refresh()
        try:
            user_input = stdscr.getstr(h - 3, len(prompt) + 2, w - len(prompt) - 4)
            text = user_input.decode("utf-8").strip()
            client.remove_torrent(torrent["id"], delete_data=text in ["y", "Y", "yes", "Yes"] if text else False)
        except Exception:
            pass
        curses.noecho()
        curses.curs_set(0)


    def draw_header(self, stdscr, height, width):
        """Draw application header"""
        # Title
        title = " Torrentor "
        stdscr.addstr(1, (width - len(title)) // 2, title, curses.A_BOLD)

        # Stats
        total = len(self.torrents)
        stats = f"Torrent-or| Total: {total} | {self.current_state}"
        stdscr.addstr(2, (width - len(stats)) // 2, stats)

        # Separator
        stdscr.addstr(3, 0, "=" * width)

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
        max_height = height - 7
        for i, torrent in enumerate(self.torrents[:max_height]):
            text = f"{torrent['id']}|\t Rate: {torrent['get_speed'][0]:.2f} {torrent['get_speed'][1]}|\tStatus: {torrent['status']}  \t| Progress: {torrent['progress']} out of {torrent['formatted_size'][0]:.3f} {torrent['formatted_size'][1]}  \t| ETA:{torrent['eta']}\t| Download Location: {torrent['download_dir']} |\t{torrent['name'][:50]}"
            if i == self.selected:
                color = self.get_color_on_status(torrent["status"])
                attr = curses.A_REVERSE
                if color is not None:
                    attr |= color
                stdscr.addstr(
                    i + 4,
                    2,
                    text,
                    attr,
                )
            else:
                color = self.get_color_on_status(torrent["status"])
                attr = color if color is not None else 0
                stdscr.addstr(i + 4, 2, text, attr)

    # this is for when you are adding a magnet link, will use the same logic for the main Torrent Adding
    def add_torrent_dialog(self, stdscr, height, width):
        dimh, dimw = 10, 100
        dh, dw = (height - dimh) // 2, (width - dimw) // 2
        stdscr.addstr(0, 0, f"{dh}, {dw}")
        # stdscr.addstr(dimh-1, dimw, "Enter IM message: (hit Ctrl-G to send)")

        editwin = curses.newwin(dimh, dimw, dh, dw)
        prompt = "(Enter to Finish) Enter Magnet: "
        editwin.addstr(1, 1, prompt)
        stdscr.refresh()

        # box = Textbox(editwin)

        # box.edit()
        # message = box.gather().strip().replace("\n", "").replace(prompt, "")
        message = editwin.getstr()
        text = message.encode("utf-8").strip()
        if text and "magnet" in text:
            self.draw_finalizing_dialog(stdscr, height, width, magnet=text)
        stdscr.refresh()

    def draw_footer(self, stdscr, height, width):
        """Draw help/status footer"""
        # Separator
        stdscr.addstr(height - 4, 0, "-" * width)

        # Help text
        help_items = [
            ("a", "Add Magnet"),
            ("s", "Stop/Start"),
            ("S", "Start All/Stop All"),
            ("d", "Delete Single"),
            ("o", "Open (Linux Only)"),
            ("T", "Change Screen"),
            ("q", "Quit"),
        ]

        help_text = " | ".join([f"{key}: {desc}" for key, desc in help_items])
        stdscr.addstr(height - 2, (width - len(help_text)) // 2, help_text)

    def draw_ui(self, stdscr):
        """Main UI drawing function"""
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        # Title
        title = "Torrenting Screen"
        win = curses.initscr()
        win.addstr(0, (width - len(title)) // 2, title, curses.A_BOLD)

        # Setup colors (if supported)
        if curses.has_colors():
            curses.start_color()
            curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Pending
            curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)  # Completed
            curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Highlight

        self.draw_header(win, height, width)
        self.draw_torrents(win, height, width)
        self.draw_footer(win, height, width)

    def handle_input(self, stdscr, key):
        if key == curses.KEY_UP:
            self.selected = max(0, self.selected - 1)
        elif key == curses.KEY_DOWN:
            self.selected = min(len(self.torrents) - 1, self.selected + 1)
        elif key == ord("S"):
            if self.current_state == "active":
                self.stop_torrents()
            if self.current_state == "stopped":
                self.start_torrents()
        elif key == ord("s"):
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
        super(NyaaHelper).__init__()
        super(UniversalTorrentor).__init__()
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
        self.startup()
        self.filter_mode = ""  # Added missing attribute filter_mode
        self.start_index = 0

    def draw_header(self, stdscr, height, width):
        """Draw application header"""
        # Title
        title = " Nyaa App (ncurses) "
        stdscr.addstr(1, (width - len(title)) // 2, title, curses.A_BOLD)

        # Stats
        total = len(self.torrents)
        stats = f"Torrent-or| Total: {total} | Searching: {self.query if self.query != '' else 'Nothing'} | Filtering: {self.get_category(f'{self.category}_{self.sub_category}')}"
        stdscr.addstr(2, (width - len(stats)) // 2, stats)

        # Separator
        stdscr.addstr(3, 0, "=" * width)

    def draw_footer(self, stdscr, height, width):
        """Draw help/status footer"""
        # Separator
        stdscr.addstr(height - 4, 0, "-" * width)

        # Filter status
        # filter_text = f"Filter: {self.filter_mode}"
        # stdscr.addstr(height - 3, 2, filter_text, curses.A_BOLD)

        # Help text
        help_items = [
            ("s", "search"),
            ("f", "Filter"),
            ("r", "Reset"),
            ("Space", "Toggle"),
            ("d", "Download"),
            ("T", "Change Screen"),
            ("q", "Quit"),
        ]

        help_text = " | ".join([f"{key}: {desc}" for key, desc in help_items])
        stdscr.addstr(height - 2, (width - len(help_text)) // 2, help_text)

    def draw_torrents(self, stdscr, height, width):
        # Torrents
        max_torrents = (
            height - 7
        )  # Leave space for header (4 lines) and footer (3 lines)
        for i, torrent in enumerate(self.torrents[:max_torrents]):
            text = f"{torrent['size']}\t|\tSeeds:{torrent['seeders']}  \t|\t{torrent['category']}\t|\t{torrent['title']} | "
            # Truncate text if it's too long for the width
            if len(text) > width - 4:
                text = text[: width - 7] + "..."

            # Highlight selection
            if i == self.selected:
                stdscr.addstr(i + 4, 2, text, curses.A_REVERSE)
            else:
                stdscr.addstr(i + 4, 2, text)

    def handle_input(self, stdscr, key):
        height, width = stdscr.getmaxyx()
        # Navigation
        if key == curses.KEY_UP:
            self.selected = max(0, self.selected - 1)
            if self.selected <= 3:
                stdscr.scroll(-1)
        elif key == curses.KEY_DOWN:
            self.selected = min(len(self.torrents) - 1, self.selected + 1)
            if self.selected >= height - 3 - 4:
                stdscr.scroll(1)

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
        elif key == ord("f"):
            self.handle_filter(stdscr)
        elif key == ord("d"):
            self.draw_finalizing_dialog(stdscr, height, width, self.selected)
        elif key == ord("r"):
            self.query = ""
            self.category = 0
            self.sub_category = 0
            self.torrents = self.search()

    def handle_filter(self, stdscr):
        h, w = stdscr.getmaxyx()

        category = " | ".join(
            [f"{key}: {desc['name']}" for key, desc in self.categories.items()]
        )
        stdscr.addstr(h - 3, 2, category)

        prompt = "Filter: "
        stdscr.addstr(h - 2, 2, prompt)

        # Setting up for input
        curses.echo()
        curses.curs_set(1)

        # Get input
        stdscr.refresh()
        try:
            user_input = stdscr.getstr(h - 2, len(prompt) + 2, w - len(prompt) - 4)
            text = user_input.decode("utf-8").strip()
            if text:
                self.category = text
                if self.category == 0:
                    self.torrents = self.search()
                else:
                    sub_cat = " | ".join(
                        [
                            f"{key}: {desc}"
                            for key, desc in self.categories[text]["sub_cats"].items()
                        ]
                    )
                    stdscr.addstr(h - 3, 2, sub_cat)
                    try:
                        user_input = stdscr.getstr(
                            h - 2, len(prompt) + 2, w - len(prompt) - 4
                        )
                        text = user_input.decode("utf-8").strip()
                        if text:
                            self.sub_category = text
                            self.torrents = self.search()
                    except Exception:
                        pass
        except Exception:
            pass
        curses.noecho()
        curses.curs_set(0)

    def handle_search(self, stdscr):
        """Simple input dialog"""
        h, w = stdscr.getmaxyx()

        # Show input prompt
        prompt = "New Search: "
        stdscr.addstr(h - 3, 2, prompt)

        # Setup for input
        curses.echo()
        curses.curs_set(1)

        # Get input
        stdscr.refresh()
        try:
            user_input = stdscr.getstr(h - 3, len(prompt) + 2, w - len(prompt) - 4)
            text = user_input.decode("utf-8").strip()
            if text:
                self.query = text
                self.torrents = self.search()
        except Exception:
            pass
        curses.noecho()
        curses.curs_set(0)

    def draw_ui(self, stdscr):
        """Main UI drawing function"""
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        stdscr.scrollok(True)
        # Title
        title = "Simple NYAA Interpreter"
        win = curses.initscr()
        win.addstr(0, (width - len(title)) // 2, title, curses.A_BOLD)
        # Setup colors (if supported)
        if curses.has_colors():
            curses.start_color()
            curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Pending
            curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)  # Completed
            curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Highlight

        # Draw all UI components
        self.draw_header(win, height, width)
        self.draw_torrents(win, height, width)
        self.draw_footer(win, height, width)

        stdscr.refresh()


class TerminalUI:
    def __init__(self):
        self.running = True
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
        else:
            self.running = True
        if self.running:
            h, w = stdscr.getmaxyx()

            # Show input prompt
            prompt = "Sure you want to Quit? There are active torrents in the Work: (y/N)"
            stdscr.addstr(h - 3, 2, prompt)

            # Setup for input
            curses.echo()
            curses.curs_set(1)

            # Get input
            stdscr.refresh()
            try:
                user_input = stdscr.getstr(h - 3, len(prompt) + 2, w - len(prompt) - 4)
                text = user_input.decode("utf-8").strip()
                if text in ["y", 'Y', "yes", "Yes"]:
                    self.running = False
            except Exception:
                pass
            curses.noecho()
            curses.curs_set(0)
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
        stdscr.clear()

        # Initial draw
        self.draw_ui(stdscr)

        # Main loop
        while self.running:
            # Draw UI
            self.draw_ui(stdscr)

            # Get input
            try:
                key = stdscr.getch()
                self.handle_input(stdscr, key)
            except KeyboardInterrupt:
                self.running = False
            except Exception as e:
                self.draw_error(stdscr, str(e))

        # Cleanup
        curses.curs_set(1)

    def draw_error(self, stdscr, message):
        """Draw error message on the screen"""
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        error_msg = f"Error: {message}"
        stdscr.addstr(
            height // 2,
            (width - len(error_msg)) // 2,
            error_msg,
            curses.A_BOLD | curses.color_pair(3),
        )
        stdscr.refresh()
        stdscr.getch()  # Wait for user to acknowledge
        self.running = False


def main():
    app = TerminalUI()
    curses.wrapper(app.run)


if __name__ == "__main__":
    main()
