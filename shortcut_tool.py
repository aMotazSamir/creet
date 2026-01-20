import json
import os
import tkinter as tk
from dataclasses import dataclass, field
from tkinter import messagebox, simpledialog, ttk

import keyboard


CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")


@dataclass
class ShortcutItem:
    title: str
    description: str


@dataclass
class AppConfig:
    hotkey: str = "ctrl+shift+s"
    shortcuts: list[ShortcutItem] = field(default_factory=list)


class ConfigManager:
    def __init__(self, path: str) -> None:
        self.path = path

    def load(self) -> AppConfig:
        if not os.path.exists(self.path):
            return AppConfig(
                shortcuts=[
                    ShortcutItem(title="Win+E", description="Open File Explorer"),
                    ShortcutItem(title="Win+L", description="Lock the PC"),
                ]
            )

        with open(self.path, "r", encoding="utf-8") as handle:
            data = json.load(handle)

        shortcuts = [
            ShortcutItem(title=item["title"], description=item["description"])
            for item in data.get("shortcuts", [])
        ]
        return AppConfig(hotkey=data.get("hotkey", "ctrl+shift+s"), shortcuts=shortcuts)

    def save(self, config: AppConfig) -> None:
        payload = {
            "hotkey": config.hotkey,
            "shortcuts": [
                {"title": item.title, "description": item.description}
                for item in config.shortcuts
            ],
        }
        with open(self.path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)


class ShortcutOverlay:
    def __init__(self, root: tk.Tk, config: AppConfig) -> None:
        self.root = root
        self.config = config
        self.window = tk.Toplevel(root)
        self.window.title("Windows Shortcuts")
        self.window.geometry("420x360")
        self.window.withdraw()
        self.window.attributes("-topmost", True)
        self.window.protocol("WM_DELETE_WINDOW", self.hide)
        self.window.bind("<Escape>", lambda _event: self.hide())

        header = ttk.Label(
            self.window,
            text="Shortcut Cheat Sheet",
            font=("Segoe UI", 14, "bold"),
        )
        header.pack(pady=(16, 6))

        self.tree = ttk.Treeview(self.window, columns=("title", "description"), show="headings")
        self.tree.heading("title", text="Shortcut")
        self.tree.heading("description", text="Description")
        self.tree.column("title", width=120, anchor="center")
        self.tree.column("description", width=260, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=16, pady=8)

        close_button = ttk.Button(self.window, text="Hide", command=self.hide)
        close_button.pack(pady=(0, 16))

    def refresh(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        for shortcut in self.config.shortcuts:
            self.tree.insert("", "end", values=(shortcut.title, shortcut.description))

    def toggle(self) -> None:
        if self.window.state() == "withdrawn":
            self.show()
        else:
            self.hide()

    def show(self) -> None:
        self.refresh()
        self.window.deiconify()
        self.window.lift()
        self.window.focus_force()

    def hide(self) -> None:
        self.window.withdraw()


class SettingsWindow:
    def __init__(self, root: tk.Tk, config: AppConfig, on_save) -> None:
        self.root = root
        self.config = config
        self.on_save = on_save

        self.window = tk.Toplevel(root)
        self.window.title("Shortcut Settings")
        self.window.geometry("520x460")
        self.window.protocol("WM_DELETE_WINDOW", self.window.withdraw)

        hotkey_frame = ttk.Frame(self.window)
        hotkey_frame.pack(fill="x", padx=16, pady=(16, 8))

        ttk.Label(hotkey_frame, text="Hotkey to show shortcuts:").pack(side="left")
        self.hotkey_var = tk.StringVar(value=config.hotkey)
        ttk.Entry(hotkey_frame, textvariable=self.hotkey_var, width=30).pack(
            side="left", padx=8
        )

        ttk.Label(
            self.window,
            text="Windows shortcuts you want to show:",
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", padx=16, pady=(10, 6))

        self.tree = ttk.Treeview(self.window, columns=("title", "description"), show="headings")
        self.tree.heading("title", text="Shortcut")
        self.tree.heading("description", text="Description")
        self.tree.column("title", width=120, anchor="center")
        self.tree.column("description", width=300, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=16, pady=8)

        controls = ttk.Frame(self.window)
        controls.pack(pady=8)

        ttk.Button(controls, text="Add", command=self.add_item).pack(side="left", padx=4)
        ttk.Button(controls, text="Edit", command=self.edit_item).pack(side="left", padx=4)
        ttk.Button(controls, text="Remove", command=self.remove_item).pack(side="left", padx=4)

        save_button = ttk.Button(self.window, text="Save Settings", command=self.save)
        save_button.pack(pady=(8, 16))

        self.refresh()

    def refresh(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        for shortcut in self.config.shortcuts:
            self.tree.insert("", "end", values=(shortcut.title, shortcut.description))

    def add_item(self) -> None:
        title = simpledialog.askstring("Shortcut", "Enter shortcut (e.g. Win+E):")
        if not title:
            return
        description = simpledialog.askstring(
            "Description", "What does this shortcut do?"
        )
        if description is None:
            return
        self.config.shortcuts.append(ShortcutItem(title=title, description=description))
        self.refresh()

    def edit_item(self) -> None:
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Select", "Please select a shortcut to edit.")
            return
        index = self.tree.index(selected[0])
        current = self.config.shortcuts[index]
        title = simpledialog.askstring(
            "Shortcut", "Edit shortcut:", initialvalue=current.title
        )
        if not title:
            return
        description = simpledialog.askstring(
            "Description", "Edit description:", initialvalue=current.description
        )
        if description is None:
            return
        self.config.shortcuts[index] = ShortcutItem(title=title, description=description)
        self.refresh()

    def remove_item(self) -> None:
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Select", "Please select a shortcut to remove.")
            return
        index = self.tree.index(selected[0])
        del self.config.shortcuts[index]
        self.refresh()

    def save(self) -> None:
        hotkey = self.hotkey_var.get().strip()
        if not hotkey:
            messagebox.showerror("Hotkey", "Please enter a valid hotkey.")
            return
        self.config.hotkey = hotkey
        self.on_save()
        messagebox.showinfo("Saved", "Settings saved. New hotkey is active now.")


class ShortcutApp:
    def __init__(self, root: tk.Tk, config_manager: ConfigManager) -> None:
        self.root = root
        self.config_manager = config_manager
        self.config = self.config_manager.load()

        self.root.title("Shortcut Assistant")
        self.root.geometry("520x200")

        header = ttk.Label(
            root,
            text="Shortcut Assistant",
            font=("Segoe UI", 16, "bold"),
        )
        header.pack(pady=(20, 6))

        description = ttk.Label(
            root,
            text=(
                "Press your chosen hotkey to show the Windows shortcuts list.\n"
                "Use Settings to customize the hotkey and the list."
            ),
            justify="center",
        )
        description.pack()

        controls = ttk.Frame(root)
        controls.pack(pady=12)

        ttk.Button(controls, text="Settings", command=self.open_settings).pack(
            side="left", padx=6
        )
        ttk.Button(controls, text="Show Shortcuts", command=self.show_overlay).pack(
            side="left", padx=6
        )

        self.overlay = ShortcutOverlay(root, self.config)
        self.settings_window = SettingsWindow(root, self.config, self.on_save)
        self.settings_window.window.withdraw()

        self.register_hotkey()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def register_hotkey(self) -> None:
        keyboard.unhook_all()
        keyboard.add_hotkey(self.config.hotkey, lambda: self.root.after(0, self.toggle))

    def toggle(self) -> None:
        self.overlay.toggle()

    def show_overlay(self) -> None:
        self.overlay.show()

    def open_settings(self) -> None:
        self.settings_window.refresh()
        self.settings_window.window.deiconify()
        self.settings_window.window.lift()

    def on_save(self) -> None:
        self.config_manager.save(self.config)
        self.register_hotkey()

    def on_close(self) -> None:
        keyboard.unhook_all()
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    style = ttk.Style(root)
    if "vista" in style.theme_names():
        style.theme_use("vista")
    app = ShortcutApp(root, ConfigManager(CONFIG_PATH))
    root.mainloop()


if __name__ == "__main__":
    main()
