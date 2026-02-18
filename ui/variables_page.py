"""
Variables management page: $VAR = value definitions.
"""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw


class VariablesPage(Gtk.Box):
    def __init__(self, parser):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.parser = parser
        self._variables: dict[str, str] = {}  # name (without $) -> value

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        toolbar.set_margin_top(12)
        toolbar.set_margin_bottom(8)
        toolbar.set_margin_start(16)
        toolbar.set_margin_end(16)
        self.append(toolbar)

        title = Gtk.Label(label="Variables")
        title.add_css_class("title-3")
        title.set_hexpand(True)
        title.set_xalign(0)
        toolbar.append(title)

        add_btn = Gtk.Button(label="Add Variable")
        add_btn.add_css_class("suggested-action")
        add_btn.add_css_class("pill")
        add_btn.set_icon_name("list-add-symbolic")
        add_btn.connect("clicked", self._on_add)
        toolbar.append(add_btn)

        info = Gtk.Label()
        info.set_markup('<span size="small" foreground="#888">Variables allow you to define a value once and use it multiple times using the <b>$name</b> syntax.</span>')
        info.set_margin_start(16)
        info.set_margin_end(16)
        info.set_margin_bottom(8)
        info.set_xalign(0)
        self.append(info)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)
        scroll.set_margin_start(16)
        scroll.set_margin_end(16)
        scroll.set_margin_bottom(16)
        self.append(scroll)

        self.var_list = Gtk.ListBox()
        self.var_list.set_selection_mode(Gtk.SelectionMode.NONE)
        self.var_list.add_css_class("boxed-list")
        scroll.set_child(self.var_list)

    def _rebuild_list(self):
        child = self.var_list.get_first_child()
        while child:
            nxt = child.get_next_sibling()
            self.var_list.remove(child)
            child = nxt

        if not self._variables:
            empty = Adw.ActionRow()
            empty.set_title("No variables defined")
            empty.set_subtitle("Click 'Add Variable' to define one")
            self.var_list.append(empty)
            return

        for name, value in list(self._variables.items()):
            row = Adw.ActionRow()
            row.set_title(f"${name}")
            row.set_subtitle(value)

            edit_btn = Gtk.Button()
            edit_btn.set_icon_name("document-edit-symbolic")
            edit_btn.add_css_class("flat")
            edit_btn.set_valign(Gtk.Align.CENTER)
            edit_btn.connect("clicked", lambda btn, n=name: self._on_edit(n))
            row.add_suffix(edit_btn)

            del_btn = Gtk.Button()
            del_btn.set_icon_name("list-remove-symbolic")
            del_btn.add_css_class("flat")
            del_btn.add_css_class("destructive-action")
            del_btn.set_valign(Gtk.Align.CENTER)
            del_btn.connect("clicked", lambda btn, n=name: self._on_delete(n))
            row.add_suffix(del_btn)

            self.var_list.append(row)

    def _on_add(self, btn):
        self._show_dialog(None, None)

    def _on_edit(self, name: str):
        self._show_dialog(name, self._variables[name])

    def _on_delete(self, name: str):
        self._variables.pop(name, None)
        self._rebuild_list()

    def _show_dialog(self, old_name: str | None, old_value: str | None):
        dialog = Adw.Dialog()
        dialog.set_title("Add Variable" if old_name is None else "Edit Variable")
        dialog.set_content_width(440)

        tv = Adw.ToolbarView()
        dialog.set_child(tv)
        tv.add_top_bar(Adw.HeaderBar())

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        tv.set_content(content)

        clamp = Adw.Clamp()
        clamp.set_maximum_size(400)
        clamp.set_margin_top(16)
        clamp.set_margin_bottom(8)
        clamp.set_margin_start(16)
        clamp.set_margin_end(16)
        content.append(clamp)

        form = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        clamp.set_child(form)

        group = Adw.PreferencesGroup()
        group.set_title("Variable Definition")
        group.set_description("Define a reusable constant (e.g., your terminal or main modifier key)")
        form.append(group)

        name_row = Adw.EntryRow()
        name_row.set_title("Variable Name (Reference using $)")
        if old_name:
            name_row.set_text(old_name)
        group.add(name_row)

        value_row = Adw.EntryRow()
        value_row.set_title("Assigned Value")
        value_row.set_tooltip_text("Example: kitty, SUPER, waybar")
        if old_value:
            value_row.set_text(old_value)
        group.add(value_row)

        # Common suggestions
        suggestions_group = Adw.PreferencesGroup()
        suggestions_group.set_title("Frequently Used Variables")
        suggestions_group.set_description("Commonly used placeholders for core apps and keys")
        form.append(suggestions_group)

        common = [
            ("terminal", "kitty", "Terminal emulator"),
            ("fileManager", "dolphin", "File manager"),
            ("menu", "rofi -show drun", "App launcher"),
            ("mainMod", "SUPER", "Main modifier key"),
            ("browser", "firefox", "Web browser"),
        ]
        for vname, vval, desc in common:
            srow = Adw.ActionRow()
            srow.set_title(f"${vname} = {vval}")
            srow.set_subtitle(desc)
            srow.set_activatable(True)
            srow.connect("activated", lambda r, n=vname, v=vval: (
                name_row.set_text(n), value_row.set_text(v)
            ))
            suggestions_group.add(srow)

        save_btn = Gtk.Button(label="Save")
        save_btn.add_css_class("suggested-action")
        save_btn.add_css_class("pill")
        save_btn.set_margin_top(8)
        save_btn.set_margin_start(16)
        save_btn.set_margin_end(16)
        save_btn.set_margin_bottom(16)
        content.append(save_btn)

        def on_save(btn):
            name = name_row.get_text().strip().lstrip("$")
            value = value_row.get_text().strip()
            if not name:
                return
            if old_name and old_name != name:
                self._variables.pop(old_name, None)
            self._variables[name] = value
            self._rebuild_list()
            dialog.close()

        save_btn.connect("clicked", on_save)
        dialog.present(self)

    def refresh(self):
        raw = self.parser.get_variables()
        # Strip leading $ from keys
        self._variables = {k.lstrip("$"): v for k, v in raw.items()}
        self._rebuild_list()

    def apply_changes(self):
        self.parser.set_variables(self._variables)
