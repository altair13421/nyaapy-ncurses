# nyaapy-ncurses

## Terminal UI

Run the interactive interface with `python ui.py`. It opens the torrent queue and
Nyaa search screens; press `T` to switch between them.

- Use `Up`/`Down` to move through results and `PgUp`/`PgDn` to move a screen at a time.
- On the search screen, `s` searches, `f` filters, `P` switches between Nyaa and
  Sukebei, `r` resets, and `d` starts the add-torrent flow.
- Search results color category and subcategory labels separately; colors adapt
  to the terminal's available palette. The UI inherits the terminal background
  (so it follows your dark terminal theme) and marks the selected result with a
  subtle `>` instead of a bright inverted row.
- Press `f` to open the category picker, then choose a subcategory from the
  second menu. Both menus show the available names and use their matching
  category/subcategory colors; choose the “All” option to clear that level.
- On the queue screen, `s` starts/stops the selected torrent, `S` starts or stops
  all torrents, `a` adds a magnet, and `d` removes the selected torrent.
- Press `Esc` to cancel any active prompt. Adding a torrent requires typing `y`
  at the final confirmation.
