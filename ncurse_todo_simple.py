# minimal_todo.py
import curses


class SimpleTodo:
    def __init__(self):
        self.todos = []
        self.selected = 0

    def draw(self, stdscr):
        stdscr.clear()
        h, w = stdscr.getmaxyx()

        # Title
        title = "Simple TODO"
        stdscr.addstr(0, (w - len(title)) // 2, title, curses.A_BOLD)

        # Instructions
        stdscr.addstr(1, 2, "Press 'a' to add, 'd' to delete, SPACE to toggle")

        # Todos
        for i, todo in enumerate(self.todos):
            # Format
            status = "[✓]" if todo["done"] else "[ ]"
            text = f"{status} {todo['text']}"

            # Highlight selection
            if i == self.selected:
                stdscr.addstr(i + 3, 2, text, curses.A_REVERSE)
            else:
                stdscr.addstr(i + 3, 2, text)

        stdscr.refresh()

    def add_todo(self, stdscr):
        """Simple input dialog"""
        h, w = stdscr.getmaxyx()

        # Show input prompt
        prompt = "New todo: "
        stdscr.addstr(h - 2, 2, prompt)

        # Setup for input
        curses.echo()
        curses.curs_set(1)

        # Get input
        stdscr.refresh()
        try:
            user_input = stdscr.getstr(h - 2, len(prompt) + 2, w - len(prompt) - 4)
            text = user_input.decode("utf-8").strip()
            if text:
                self.todos.append({"text": text, "done": False})
        except:
            pass

        # Restore
        curses.noecho()
        curses.curs_set(0)

    def run(self, stdscr):
        curses.curs_set(0)
        stdscr.clear()

        while True:
            self.draw(stdscr)
            key = stdscr.getch()

            if key == ord("q"):
                break
            elif key == curses.KEY_UP:
                self.selected = max(0, self.selected - 1)
            elif key == curses.KEY_DOWN:
                self.selected = min(len(self.todos) - 1, self.selected + 1)
            elif key == ord(" "):  # Toggle
                if self.todos:
                    self.todos[self.selected]["done"] = not self.todos[self.selected][
                        "done"
                    ]
            elif key == ord("a"):  # Add
                self.add_todo(stdscr)
            elif key == ord("d"):  # Delete
                if self.todos:
                    del self.todos[self.selected]
                    if self.selected >= len(self.todos):
                        self.selected = max(0, len(self.todos) - 1)


# Quick test
if __name__ == "__main__":
    app = SimpleTodo()
    curses.wrapper(app.run)
