from __future__ import annotations

import json
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

APP_NAME = "darktable-launcher"
DATA_DIR = Path.home() / ".local" / "share" / APP_NAME
RECENTS_FILE = DATA_DIR / "recent_catalogues.json"
MAX_RECENT_CATALOGUES = 32


def _normalize_path(value: str | Path) -> str:
    path = Path(value).expanduser()
    try:
        return str(path.resolve())
    except OSError:
        return str(path.absolute())


class RecentCatalogues:
    def __init__(self, storage_file: Path) -> None:
        self.storage_file = storage_file
        self.entries: list[str] = []
        self._load()

    def _load(self) -> None:
        if not self.storage_file.exists():
            self.entries = []
            return
        try:
            raw = json.loads(self.storage_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            self.entries = []
            return
        if isinstance(raw, list):
            normalized: list[str] = []
            for item in raw:
                if isinstance(item, str):
                    normalized.append(_normalize_path(item))
            self.entries = normalized
        else:
            self.entries = []

    def save(self) -> None:
        try:
            self.storage_file.parent.mkdir(parents=True, exist_ok=True)
            self.storage_file.write_text(
                json.dumps(self.entries, indent=2),
                encoding="utf-8",
            )
        except OSError:
            messagebox.showerror(APP_NAME, "Unable to save recent catalogues list")

    def remove(self, path: str | Path) -> None:
        normalized = _normalize_path(path)
        self.entries = [entry for entry in self.entries if entry != normalized]
        self.save()

    def move_to_front(self, path: Path) -> str:
        normalized = _normalize_path(path)
        self.entries = [entry for entry in self.entries if entry != normalized]
        self.entries.insert(0, normalized)
        if len(self.entries) > MAX_RECENT_CATALOGUES:
            self.entries = self.entries[:MAX_RECENT_CATALOGUES]
        self.save()
        return normalized


class LauncherApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(APP_NAME)
        self.root.minsize(520, 360)

        self.recents = RecentCatalogues(RECENTS_FILE)

        self._build_widgets()
        self.refresh_list(select_target=self.recents.entries[0] if self.recents.entries else None)

    def _build_widgets(self) -> None:
        self.list_frame = tk.Frame(self.root, padx=12, pady=12)
        self.list_frame.pack(fill=tk.BOTH, expand=True)

        self.listbox = tk.Listbox(
            self.list_frame,
            activestyle="none",
            selectmode=tk.SINGLE,
            exportselection=False,
        )
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollbar = tk.Scrollbar(self.list_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=self.scrollbar.set)

        self.listbox.bind("<<ListboxSelect>>", lambda _: self.update_open_button_state())
        self.listbox.bind("<Double-Button-1>", lambda _: self.open_selected_catalogue())
        self.listbox.bind("<Button-3>", self.show_context_menu)

        self.list_menu = tk.Menu(self.listbox, tearoff=0)
        self.list_menu.add_command(label="Delete", command=self.delete_selected_catalogue)

        self.button_frame = tk.Frame(self.root, padx=12, pady=12)
        self.button_frame.pack(fill=tk.X)

        self.open_button = tk.Button(self.button_frame, text="Open", width=12, command=self.open_selected_catalogue)
        self.open_button.pack(side=tk.RIGHT, padx=(8, 0))

        self.select_button = tk.Button(
            self.button_frame,
            text="Select another",
            width=14,
            command=self.select_existing_catalogue,
        )
        self.select_button.pack(side=tk.RIGHT, padx=(8, 0))

        self.new_button = tk.Button(self.button_frame, text="New", width=12, command=self.create_new_catalogue)
        self.new_button.pack(side=tk.RIGHT)

        self.update_open_button_state()

    def refresh_list(self, select_target: str | None = None) -> None:
        self.listbox.delete(0, tk.END)
        for entry in self.recents.entries:
            self.listbox.insert(tk.END, entry)
        if select_target and select_target in self.recents.entries:
            index = self.recents.entries.index(select_target)
            self.listbox.selection_set(index)
            self.listbox.see(index)
        elif self.recents.entries:
            self.listbox.selection_set(0)
            self.listbox.see(0)
        self.update_open_button_state()

    def show_context_menu(self, event: tk.Event) -> None:
        if self.listbox.size() == 0:
            return
        index = self.listbox.nearest(event.y)
        if index < 0 or index >= self.listbox.size():
            return
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(index)
        self.listbox.activate(index)
        self.update_open_button_state()
        try:
            self.list_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.list_menu.grab_release()

    def get_selected_path(self) -> Path | None:
        selection = self.listbox.curselection()
        if not selection:
            return None
        return Path(self.listbox.get(selection[0]))

    def update_open_button_state(self) -> None:
        path = self.get_selected_path()
        if path and path.exists():
            self.open_button.config(state=tk.NORMAL)
        else:
            self.open_button.config(state=tk.DISABLED)

    def open_selected_catalogue(self) -> None:
        path = self.get_selected_path()
        if path is None:
            return
        if not path.exists():
            messagebox.showerror(APP_NAME, "Selected catalogue does not exist anymore")
            self.update_open_button_state()
            return
        normalized = self.recents.move_to_front(path)
        self.refresh_list(select_target=normalized)
        if self._launch_darktable(Path(normalized)):
            self.root.after(100, self.root.destroy)

    def delete_selected_catalogue(self) -> None:
        path = self.get_selected_path()
        if path is None:
            return
        self.recents.remove(path)
        self.refresh_list()

    def create_new_catalogue(self) -> None:
        filepath = filedialog.asksaveasfilename(
            title="Create Darktable Catalogue",
            defaultextension=".db",
            filetypes=[("Darktable Catalogue", "*.db")],
        )
        if not filepath:
            return
        path = Path(filepath)
        if path.suffix.lower() != ".db":
            path = path.with_suffix(".db")
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch(exist_ok=True)
        except OSError as exc:
            messagebox.showerror(APP_NAME, f"Cannot create catalogue: {exc}")
            return
        normalized = self.recents.move_to_front(path)
        self.refresh_list(select_target=normalized)
        if self._launch_darktable(Path(normalized)):
            self.root.after(100, self.root.destroy)

    def select_existing_catalogue(self) -> None:
        filepath = filedialog.askopenfilename(
            title="Select Darktable Catalogue",
            filetypes=[("Darktable Catalogue", "*.db")],
        )
        if not filepath:
            return
        path = Path(filepath)
        if path.suffix.lower() != ".db":
            messagebox.showerror(APP_NAME, "Please select a .db catalogue file")
            return
        if not path.exists():
            messagebox.showerror(APP_NAME, "Selected catalogue does not exist anymore")
            return
        normalized = self.recents.move_to_front(path)
        self.refresh_list(select_target=normalized)
        if self._launch_darktable(Path(normalized)):
            self.root.after(100, self.root.destroy)

    def _launch_darktable(self, catalogue: Path) -> bool:
        try:
            subprocess.Popen(
                ["darktable", "--library", str(catalogue)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True,
                start_new_session=True
            )
        except FileNotFoundError:
            messagebox.showerror(APP_NAME, "darktable executable was not found on PATH")
            return False
        except OSError as exc:
            messagebox.showerror(APP_NAME, f"Unable to start darktable: {exc}")
            return False
        return True


def main() -> None:
    root = tk.Tk()
    LauncherApp(root)
    root.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover - safety net for GUI entrypoint
        print(f"darktable-launcher failed: {exc}", file=sys.stderr)
        raise
