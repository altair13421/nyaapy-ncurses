# todo_tui.py
import curses
import json
import os
from datetime import datetime


class TodoApp:
    def __init__(self, data_file="todos.json"):
        self.data_file = data_file
        self.todos = []
        self.selected_index = 0
        self.running = True
        self.filter_mode = "all"  # all, active, completed
        self.load_todos()

    def load_todos(self):
        """Load todos from JSON file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r") as f:
                    self.todos = json.load(f)
            except:
                self.todos = []
        else:
            self.todos = []

    def save_todos(self):
        """Save todos to JSON file"""
        with open(self.data_file, "w") as f:
            json.dump(self.todos, f, indent=2)

    def add_todo(self, text):
        """Add a new todo"""
        if text.strip():
            self.todos.append(
                {
                    "id": len(self.todos),
                    "text": text.strip(),
                    "completed": False,
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                }
            )
            self.save_todos()

    def delete_todo(self, index):
        """Delete a todo"""
        if 0 <= index < len(self.todos):
            del self.todos[index]
            self.save_todos()
            # Adjust selected index
            if self.selected_index >= len(self.todos):
                self.selected_index = max(0, len(self.todos) - 1)

    def toggle_todo(self, index):
        """Toggle todo completion status"""
        if 0 <= index < len(self.todos):
            self.todos[index]["completed"] = not self.todos[index]["completed"]
            self.save_todos()

    def get_filtered_todos(self):
        """Get todos based on current filter"""
        if self.filter_mode == "active":
            return [todo for todo in self.todos if not todo["completed"]]
        elif self.filter_mode == "completed":
            return [todo for todo in self.todos if todo["completed"]]
        else:
            return self.todos

    def draw_header(self, stdscr, height, width):
        """Draw application header"""
        # Title
        title = " 📝 TODO App (ncurses) "
        stdscr.addstr(1, (width - len(title)) // 2, title, curses.A_BOLD)

        # Stats
        total = len(self.todos)
        completed = sum(1 for todo in self.todos if todo["completed"])
        stats = f"Total: {total} | Done: {completed} | Pending: {total - completed}"
        stdscr.addstr(2, (width - len(stats)) // 2, stats)

        # Separator
        stdscr.addstr(3, 0, "=" * width)

    def draw_todos(self, stdscr, start_y, height, width):
        """Draw todo list"""
        filtered_todos = self.get_filtered_todos()
        max_items = height - start_y - 3  # Leave space for footer

        for i in range(max_items):
            row = start_y + i
            if i < len(filtered_todos):
                todo = filtered_todos[i]

                # Calculate the actual index in self.todos
                actual_index = self.todos.index(todo) if todo in self.todos else -1

                # Selection highlight
                attr = curses.A_REVERSE if i == self.selected_index else curses.A_NORMAL

                # Status indicator
                status = "✓" if todo["completed"] else "○"
                status_color = (
                    curses.color_pair(2) if todo["completed"] else curses.color_pair(1)
                )

                # Text with possible strike-through
                text = todo["text"]
                if todo["completed"]:
                    text = f"[{status}] {text}"
                    attr |= curses.A_DIM
                else:
                    text = f"[{status}] {text}"

                # Truncate if too long
                if len(text) > width - 4:
                    text = text[: width - 7] + "..."

                stdscr.addstr(row, 2, text, attr | status_color)
            else:
                # Clear unused rows
                stdscr.addstr(row, 0, " " * width)

    def draw_footer(self, stdscr, height, width):
        """Draw help/status footer"""
        # Separator
        stdscr.addstr(height - 4, 0, "-" * width)

        # Filter status
        filter_text = f"Filter: {self.filter_mode}"
        stdscr.addstr(height - 3, 2, filter_text, curses.A_BOLD)

        # Help text
        help_items = [
            ("←/→", "Filter"),
            ("a", "Add"),
            ("d", "Delete"),
            ("Space", "Toggle"),
            ("q", "Quit"),
        ]

        help_text = " | ".join([f"{key}: {desc}" for key, desc in help_items])
        stdscr.addstr(height - 2, (width - len(help_text)) // 2, help_text)

    def draw_add_dialog(self, stdscr, height, width):
        """Draw todo addition dialog"""
        # Dialog box
        d_height, d_width = 5, 50
        d_y = (height - d_height) // 2
        d_x = (width - d_width) // 2

        # Box border
        stdscr.addstr(d_y, d_x, "+" + "-" * (d_width - 2) + "+")
        for i in range(1, d_height - 1):
            stdscr.addstr(d_y + i, d_x, "|" + " " * (d_width - 2) + "|")
        stdscr.addstr(d_y + d_height - 1, d_x, "+" + "-" * (d_width - 2) + "+")

        # Title
        title = " Add New Todo "
        stdscr.addstr(d_y, d_x + (d_width - len(title)) // 2, title, curses.A_BOLD)

        # Input prompt
        prompt = "Enter task: "
        stdscr.addstr(d_y + 2, d_x + 2, prompt)

        # Show cursor and enable echo
        curses.curs_set(1)
        curses.echo()

        # Get input
        stdscr.move(d_y + 2, d_x + len(prompt) + 2)
        stdscr.refresh()

        try:
            user_input = stdscr.getstr(
                d_y + 2, d_x + len(prompt) + 2, d_width - len(prompt) - 4
            ).decode("utf-8")
        except:
            user_input = ""

        # Restore cursor and echo settings
        curses.curs_set(0)
        curses.noecho()

        return user_input.strip()

    def draw_ui(self, stdscr):
        """Main UI drawing function"""
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        # Setup colors (if supported)
        if curses.has_colors():
            curses.start_color()
            curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Pending
            curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)  # Completed
            curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Highlight

        # Draw all UI components
        self.draw_header(stdscr, height, width)
        self.draw_todos(stdscr, 5, height, width)
        self.draw_footer(stdscr, height, width)

        stdscr.refresh()

    def handle_input(self, stdscr, key):
        """Handle keyboard input"""
        filtered_todos = self.get_filtered_todos()

        if key == ord("q"):
            self.running = False

        elif key == curses.KEY_UP:
            self.selected_index = max(0, self.selected_index - 1)

        elif key == curses.KEY_DOWN:
            self.selected_index = min(len(filtered_todos) - 1, self.selected_index + 1)

        elif key == ord(" "):  # Space to toggle
            if filtered_todos:
                # Find actual index in self.todos
                todo = filtered_todos[self.selected_index]
                actual_index = self.todos.index(todo)
                self.toggle_todo(actual_index)

        elif key == ord("a"):  # Add new todo
            new_todo = self.draw_add_dialog(stdscr, *stdscr.getmaxyx())
            if new_todo:
                self.add_todo(new_todo)
                # Select the new todo
                self.selected_index = len(self.get_filtered_todos()) - 1

        elif key == ord("d"):  # Delete todo
            if filtered_todos:
                todo = filtered_todos[self.selected_index]
                actual_index = self.todos.index(todo)
                self.delete_todo(actual_index)

        elif key == ord("c"):  # Clear completed
            self.todos = [todo for todo in self.todos if not todo["completed"]]
            self.save_todos()
            self.selected_index = min(
                self.selected_index, len(self.get_filtered_todos()) - 1
            )

        elif key == curses.KEY_LEFT:  # Change filter left
            filters = ["all", "active", "completed"]
            current_idx = filters.index(self.filter_mode)
            self.filter_mode = filters[(current_idx - 1) % len(filters)]
            self.selected_index = 0

        elif key == curses.KEY_RIGHT:  # Change filter right
            filters = ["all", "active", "completed"]
            current_idx = filters.index(self.filter_mode)
            self.filter_mode = filters[(current_idx + 1) % len(filters)]
            self.selected_index = 0

        elif key == ord("s"):  # Sort by completed status
            self.todos.sort(key=lambda x: x["completed"])
            self.save_todos()

        elif key == ord("r"):  # Reverse order
            self.todos.reverse()
            self.save_todos()

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
                # Handle any errors gracefully
                self.draw_error(stdscr, str(e))

        # Cleanup
        curses.curs_set(1)

    def draw_error(self, stdscr, error_msg):
        """Display error message"""
        height, width = stdscr.getmaxyx()
        msg = f" Error: {error_msg[: width - 10]} "
        stdscr.addstr(height - 1, 0, msg, curses.A_REVERSE | curses.A_BOLD)
        stdscr.refresh()
        stdscr.getch()  # Wait for keypress


def main():
    app = TodoApp()
    curses.wrapper(app.run)


if __name__ == "__main__":
    main()
