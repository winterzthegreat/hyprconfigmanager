"""
Autostart management page (exec-once entries).
"""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

import copy

from gi.repository import Gtk, Adw

class AutostartPage(Gtk.Box):
    def __init__(self, parser, undo_manager=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.parser = parser
        self.undo_manager = undo_manager
        self._commands: list[str] = []

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        # Toolbar
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        toolbar.set_margin_top(12)
        toolbar.set_margin_bottom(8)
        toolbar.set_margin_start(16)
        toolbar.set_margin_end(16)
        self.append(toolbar)

        title_label = Gtk.Label(label="Autostart Programs")
        title_label.add_css_class("title-3")
        title_label.set_hexpand(True)
        title_label.set_xalign(0)
        toolbar.append(title_label)

        add_btn = Gtk.Button(label="Add Program")
        add_btn.add_css_class("suggested-action")
        add_btn.add_css_class("pill")
        add_btn.set_icon_name("list-add-symbolic")
        add_btn.connect("clicked", self._on_add)
        toolbar.append(add_btn)

        # Info banner
        info_label = Gtk.Label()
        info_label.set_markup(
            '<span size="small" foreground="#888">Hyprland will run these commands automatically every time you log in.</span>'
        )
        info_label.set_margin_start(16)
        info_label.set_margin_end(16)
        info_label.set_margin_bottom(8)
        info_label.set_xalign(0)
        self.append(info_label)

        # Scrollable list
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)
        scroll.set_margin_start(16)
        scroll.set_margin_end(16)
        scroll.set_margin_bottom(16)
        self.append(scroll)

        self.cmd_list = Gtk.ListBox()
        self.cmd_list.set_selection_mode(Gtk.SelectionMode.NONE)
        self.cmd_list.add_css_class("boxed-list")
        scroll.set_child(self.cmd_list)

    def _rebuild_list(self):
        child = self.cmd_list.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.cmd_list.remove(child)
            child = next_child

        if not self._commands:
            empty_row = Adw.ActionRow()
            empty_row.set_title("No autostart entries")
            empty_row.set_subtitle("Click 'Add Program' to add one")
            self.cmd_list.append(empty_row)
            return

        for i, cmd in enumerate(self._commands):
            row = Adw.ActionRow()
            resolved = self.parser.resolve(cmd)
            row.set_title(resolved)
            if resolved != cmd:
                row.set_subtitle(f"Raw: {cmd}")
            else:
                row.set_subtitle("exec-once")

            # Edit button
            edit_btn = Gtk.Button()
            edit_btn.set_icon_name("document-edit-symbolic")
            edit_btn.add_css_class("flat")
            edit_btn.set_valign(Gtk.Align.CENTER)
            edit_btn.set_tooltip_text("Edit")
            edit_btn.connect("clicked", lambda btn, idx=i: self._on_edit(idx))
            row.add_suffix(edit_btn)

            # Delete button
            del_btn = Gtk.Button()
            del_btn.set_icon_name("list-remove-symbolic")
            del_btn.add_css_class("flat")
            del_btn.add_css_class("destructive-action")
            del_btn.set_valign(Gtk.Align.CENTER)
            del_btn.set_tooltip_text("Remove")
            del_btn.connect("clicked", lambda btn, idx=i: self._on_delete(idx))
            row.add_suffix(del_btn)

            self.cmd_list.append(row)

    def _on_add(self, btn):
        self._show_dialog(None, -1)

    def _on_edit(self, idx: int):
        self._show_dialog(self._commands[idx], idx)

    def _on_delete(self, idx: int):
        old_cmd = self._commands[idx]
        self._commands.pop(idx)
        self._rebuild_list()
        if self.undo_manager:
            def undo(i=idx, c=old_cmd):
                self._commands.insert(i, c)
                self._rebuild_list()
            def redo(i=idx):
                self._commands.pop(i)
                self._rebuild_list()
            self.undo_manager.push(f"Delete autostart: {old_cmd[:40]}", undo, redo)

    def _show_dialog(self, current_cmd: str | None, idx: int):
        dialog = Adw.Dialog()
        dialog.set_title("Add Autostart Entry" if current_cmd is None else "Edit Autostart Entry")
        dialog.set_content_width(460)

        toolbar_view = Adw.ToolbarView()
        dialog.set_child(toolbar_view)

        header = Adw.HeaderBar()
        header.add_css_class("flat")
        toolbar_view.add_top_bar(header)

        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        toolbar_view.set_content(content_box)

        clamp = Adw.Clamp()
        clamp.set_maximum_size(420)
        clamp.set_margin_top(16)
        clamp.set_margin_bottom(8)
        clamp.set_margin_start(16)
        clamp.set_margin_end(16)
        content_box.append(clamp)

        form_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        clamp.set_child(form_box)

        group = Adw.PreferencesGroup()
        group.set_title("Startup Command")
        group.set_description("The shell command or script to execute at login")
        form_box.append(group)

        cmd_row = Adw.EntryRow()
        cmd_row.set_title("Command Path/Name")
        cmd_row.set_tooltip_text("Example: waybar, hyprpaper, nm-applet &")
        if current_cmd:
            cmd_row.set_text(current_cmd)
        group.add(cmd_row)

        # Common suggestions
        suggestions_group = Adw.PreferencesGroup()
        suggestions_group.set_title("Suggested Startup Services")
        suggestions_group.set_description("Frequently used background programs and bars")
        form_box.append(suggestions_group)

        common = [
            ("waybar", "Status bar"),
            ("hyprpaper", "Wallpaper daemon"),
            ("nm-applet &", "Network manager tray"),
            ("dunst", "Notification daemon"),
            ("swaync", "Notification center"),
            ("blueman-applet", "Bluetooth tray"),
            ("wl-paste --watch cliphist store", "Clipboard history"),
        ]

        for prog, desc in common:
            suggestion_row = Adw.ActionRow()
            suggestion_row.set_title(prog.replace("&", "&amp;"))
            suggestion_row.set_subtitle(desc)
            suggestion_row.set_activatable(True)
            suggestion_row.connect("activated", lambda row, p=prog: cmd_row.set_text(p))
            suggestions_group.add(suggestion_row)

        save_btn = Gtk.Button(label="Save")
        save_btn.add_css_class("suggested-action")
        save_btn.add_css_class("pill")
        save_btn.set_margin_top(8)
        save_btn.set_margin_start(16)
        save_btn.set_margin_end(16)
        save_btn.set_margin_bottom(16)
        content_box.append(save_btn)

        def on_save(btn):
            cmd = cmd_row.get_text().strip()
            if not cmd:
                return
            if idx >= 0:
                self._commands[idx] = cmd
            else:
                self._commands.append(cmd)
            self._rebuild_list()
            dialog.close()

        save_btn.connect("clicked", on_save)
        dialog.present(self)

    def refresh(self):
        self._commands = self.parser.get_exec_once()
        self._rebuild_list()

    def apply_changes(self):
        self.parser.set_exec_once(self._commands)
