"""
Keybindings management page — with variable resolution, undo/redo, and expanded dispatchers.
"""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GLib
import copy


MODIFIERS = [
    "SUPER", "SHIFT", "CTRL", "ALT",
    "SUPER SHIFT", "SUPER CTRL", "SUPER ALT",
    "CTRL SHIFT", "ALT SHIFT", "CTRL ALT",
    "SUPER CTRL SHIFT", "SUPER ALT SHIFT",
    "",
]

# Dispatcher name → (short label, description)
DISPATCHERS: list[tuple[str, str]] = [
    # ── Applications ──────────────────────────────────────────────────────────
    ("exec",                    "Run a program or shell command"),
    ("execr",                   "Run a program (raw, no shell)"),
    # ── Windows ───────────────────────────────────────────────────────────────
    ("killactive",              "Close the focused window"),
    ("closewindow",             "Close a specific window by address"),
    ("togglefloating",          "Toggle floating mode for the focused window"),
    ("fullscreen",              "Toggle fullscreen (0=full, 1=maximize, 2=fullscreen no bar)"),
    ("fakefullscreen",          "Toggle fake fullscreen (stays in tiled layout)"),
    ("pseudo",                  "Toggle pseudotiling for the focused window"),
    ("pin",                     "Pin a floating window so it stays on all workspaces"),
    ("centerwindow",            "Center the focused floating window on screen"),
    ("resizeactive",            "Resize the active window (e.g. 10 0 or exact 800 600)"),
    ("moveactive",              "Move the active floating window (e.g. 10 0)"),
    ("resizewindowpixel",       "Resize a window to exact pixel size"),
    ("movewindowpixel",         "Move a window to exact pixel position"),
    ("setfloatingsize",         "Set the size of a floating window"),
    ("toggleopaque",            "Toggle opacity override for the focused window"),
    # ── Focus ─────────────────────────────────────────────────────────────────
    ("movefocus",               "Move keyboard focus (l/r/u/d)"),
    ("focuswindow",             "Focus a window by class or title"),
    ("focusmonitor",            "Focus a monitor by name or number"),
    ("focusurgentorlast",       "Focus the urgent window or the previously focused one"),
    ("alterzorder",             "Change the Z-order of the focused window (top/bottom)"),
    # ── Moving Windows ────────────────────────────────────────────────────────
    ("movewindow",              "Move the focused window in a direction (l/r/u/d)"),
    ("swapwindow",              "Swap the focused window with one in a direction"),
    ("swapnext",                "Swap the focused window with the next in the layout"),
    # ── Workspaces ────────────────────────────────────────────────────────────
    ("workspace",               "Switch to a workspace (1-10, +1, -1, name:foo)"),
    ("movetoworkspace",         "Move the focused window to a workspace"),
    ("movetoworkspacesilent",   "Move window to workspace without switching to it"),
    ("togglespecialworkspace",  "Toggle the special (scratchpad) workspace"),
    ("movetoworkspace",         "Move window to a workspace (number or name)"),
    ("swapactiveworkspaces",    "Swap the active workspaces of two monitors"),
    ("renameworkspace",         "Rename a workspace"),
    # ── Layout ────────────────────────────────────────────────────────────────
    ("togglesplit",             "Toggle the split direction in dwindle layout"),
    ("layoutmsg",               "Send a message to the current layout (e.g. swapwithmaster)"),
    ("cyclenext",               "Cycle focus to the next window in the layout"),
    ("cycleprev",               "Cycle focus to the previous window in the layout"),
    # ── Groups ────────────────────────────────────────────────────────────────
    ("togglegroup",             "Toggle the focused window into/out of a group"),
    ("changegroupactive",       "Switch the active tab in a group (f=forward, b=backward)"),
    ("moveintogroup",           "Move the focused window into a group in a direction"),
    ("moveoutofgroup",          "Move the focused window out of its group"),
    # ── System ────────────────────────────────────────────────────────────────
    ("exit",                    "Exit Hyprland (logout)"),
    ("forcerendererreload",     "Force a full renderer reload (fixes glitches)"),
    ("dpms",                    "Toggle display power (on/off/toggle)"),
    ("hyprexpo:expo",           "Toggle the workspace overview (hyprexpo plugin)"),
    ("pass",                    "Pass the key event to the focused window"),
    ("global",                  "Invoke a global shortcut (for other apps)"),
    ("submap",                  "Enter a keybind submap (like a mode)"),
    ("bringactivetotop",        "Bring the active floating window to the top"),
    ("lockgroups",              "Lock all groups (prevent adding/removing tabs)"),
    ("lockactivegroup",         "Lock the active group"),
    ("mouse:272",               "Mouse button action (272=left, 273=right)"),
]

DISPATCHER_NAMES = [d[0] for d in DISPATCHERS]
DISPATCHER_DESCS = {d[0]: d[1] for d in DISPATCHERS}

BIND_TYPES = ["bind", "bindel", "bindl", "bindm"]
BIND_TYPE_DESCS = {
    "bind":   "Normal keybind — fires once on key press",
    "bindel": "Repeat + locked — fires repeatedly while held, works on lock screen",
    "bindl":  "Locked — works even on lock screen",
    "bindm":  "Mouse bind — use with mouse buttons",
}


class KeybindsPage(Gtk.Box):
    def __init__(self, parser, undo_manager=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.parser = parser
        self.undo_manager = undo_manager
        self._binds: list[dict] = []

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

        title_label = Gtk.Label(label="Keybindings")
        title_label.add_css_class("title-3")
        title_label.set_hexpand(True)
        title_label.set_xalign(0)
        toolbar.append(title_label)

        add_btn = Gtk.Button(label="Add Keybind")
        add_btn.add_css_class("suggested-action")
        add_btn.add_css_class("pill")
        add_btn.set_icon_name("list-add-symbolic")
        add_btn.connect("clicked", self._on_add_bind)
        toolbar.append(add_btn)

        # Info banner
        info_label = Gtk.Label()
        info_label.set_markup(
            '<span size="small" foreground="#888">'
            'Format: <b>Modifier + Key → Dispatcher [params]</b>  '
            '· Variables like <tt>$terminal</tt> are shown resolved to their actual value'
            '</span>'
        )
        info_label.set_margin_start(16)
        info_label.set_margin_end(16)
        info_label.set_margin_bottom(8)
        info_label.set_xalign(0)
        info_label.set_wrap(True)
        self.append(info_label)

        # Search bar
        search_bar_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        search_bar_box.set_margin_start(16)
        search_bar_box.set_margin_end(16)
        search_bar_box.set_margin_bottom(8)
        self.append(search_bar_box)

        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Search keybinds by key, action, or command…")
        self.search_entry.set_hexpand(True)
        self.search_entry.connect("search-changed", self._on_search_changed)
        search_bar_box.append(self.search_entry)

        # Scrollable list
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)
        scroll.set_margin_start(16)
        scroll.set_margin_end(16)
        scroll.set_margin_bottom(16)
        self.append(scroll)

        self.binds_list = Gtk.ListBox()
        self.binds_list.set_selection_mode(Gtk.SelectionMode.NONE)
        self.binds_list.add_css_class("boxed-list")
        self.binds_list.set_filter_func(self._filter_func)
        scroll.set_child(self.binds_list)

        self._search_query = ""

    def _filter_func(self, row):
        if not self._search_query:
            return True
        q = self._search_query.lower()
        if hasattr(row, "_bind_data"):
            b = row._bind_data
            text = (
                f"{b.get('mod','')} {b.get('key','')} "
                f"{b.get('dispatcher','')} {b.get('params','')}"
            ).lower()
            # Also search resolved params
            resolved = self.parser.resolve(b.get("params", "")).lower()
            return q in text or q in resolved
        return True

    def _on_search_changed(self, entry):
        self._search_query = entry.get_text()
        self.binds_list.invalidate_filter()

    def _rebuild_list(self):
        child = self.binds_list.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.binds_list.remove(child)
            child = next_child

        if not self._binds:
            empty = Adw.ActionRow()
            empty.set_title("No keybindings yet")
            empty.set_subtitle("Click 'Add Keybind' to create your first one")
            self.binds_list.append(empty)
            return

        for i, bind in enumerate(self._binds):
            row = self._make_bind_row(bind, i)
            self.binds_list.append(row)

    def _make_bind_row(self, bind: dict, idx: int) -> Adw.ActionRow:
        row = Adw.ActionRow()
        row._bind_data = bind

        mod = bind.get("mod", "").strip()
        key = bind.get("key", "").strip()
        dispatcher = bind.get("dispatcher", "").strip()
        params = bind.get("params", "").strip()
        btype = bind.get("type", "bind")

        # Title: MOD + KEY
        if mod:
            row.set_title(f"{mod} + {key}")
        else:
            row.set_title(key or "(no key)")

        # Subtitle: dispatcher → resolved params
        resolved_params = self.parser.resolve(params)
        subtitle = dispatcher
        if resolved_params:
            subtitle += f"  →  {resolved_params}"
            # Show original if different
            if resolved_params != params:
                subtitle += f"  <span size='small' foreground='#888'>({params})</span>"
        row.set_subtitle(subtitle)
        row.set_use_markup(True)

        # Bind type badge
        if btype != "bind":
            badge = Gtk.Label(label=btype)
            badge.add_css_class("caption")
            badge.add_css_class("dim-label")
            badge.set_tooltip_text(BIND_TYPE_DESCS.get(btype, btype))
            row.add_prefix(badge)

        # Edit button
        edit_btn = Gtk.Button()
        edit_btn.set_icon_name("document-edit-symbolic")
        edit_btn.add_css_class("flat")
        edit_btn.set_valign(Gtk.Align.CENTER)
        edit_btn.set_tooltip_text("Edit this keybinding")
        edit_btn.connect("clicked", lambda btn, idx=idx: self._on_edit_bind(idx))
        row.add_suffix(edit_btn)

        # Delete button
        del_btn = Gtk.Button()
        del_btn.set_icon_name("list-remove-symbolic")
        del_btn.add_css_class("flat")
        del_btn.add_css_class("destructive-action")
        del_btn.set_valign(Gtk.Align.CENTER)
        del_btn.set_tooltip_text("Delete this keybinding")
        del_btn.connect("clicked", lambda btn, idx=idx: self._on_delete_bind(idx))
        row.add_suffix(del_btn)

        return row

    def _on_add_bind(self, btn):
        self._show_bind_dialog(None, -1)

    def _on_edit_bind(self, idx: int):
        self._show_bind_dialog(self._binds[idx], idx)

    def _on_delete_bind(self, idx: int):
        old_bind = copy.deepcopy(self._binds[idx])
        old_idx = idx

        self._binds.pop(idx)
        self._rebuild_list()

        if self.undo_manager:
            def undo():
                self._binds.insert(old_idx, old_bind)
                self._rebuild_list()
            def redo():
                self._binds.pop(old_idx)
                self._rebuild_list()
            self.undo_manager.push(
                f"Delete keybind {old_bind.get('mod','')}+{old_bind.get('key','')}",
                undo, redo
            )

    def _show_bind_dialog(self, bind: dict | None, idx: int):
        dialog = Adw.Dialog()
        dialog.set_title("Add Keybinding" if bind is None else "Edit Keybinding")
        dialog.set_content_width(620)
        dialog.set_content_height(720)

        toolbar_view = Adw.ToolbarView()
        dialog.set_child(toolbar_view)

        header = Adw.HeaderBar()
        header.add_css_class("flat")
        toolbar_view.add_top_bar(header)

        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        toolbar_view.set_content(content_box)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)
        content_box.append(scroll)

        clamp = Adw.Clamp()
        clamp.set_maximum_size(580)
        clamp.set_margin_top(16)
        clamp.set_margin_bottom(16)
        clamp.set_margin_start(16)
        clamp.set_margin_end(16)
        scroll.set_child(clamp)

        form_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        clamp.set_child(form_box)

        # ── How it works ──────────────────────────────────────────────────────
        help_group = Adw.PreferencesGroup()
        help_group.set_title("How Keybindings Work")
        form_box.append(help_group)

        help_label = Gtk.Label()
        help_label.set_markup(
            "A keybinding has three parts:\n"
            "  <b>1. Modifier</b> — the key you hold (e.g. SUPER/Win)\n"
            "  <b>2. Key</b> — the key you press (e.g. T, Return, F1)\n"
            "  <b>3. Action</b> — what happens (e.g. exec kitty)\n\n"
            "<i>Tip: run <tt>wev</tt> in a terminal to find exact key names.</i>"
        )
        help_label.set_wrap(True)
        help_label.set_xalign(0)
        help_label.set_margin_start(8)
        help_label.set_margin_end(8)
        help_label.set_margin_top(4)
        help_label.set_margin_bottom(4)
        help_group.add(help_label)

        # ── Bind type ─────────────────────────────────────────────────────────
        type_group = Adw.PreferencesGroup()
        type_group.set_title("Bind Type")
        type_group.set_description("Controls when the keybind fires")
        form_box.append(type_group)

        type_row = Adw.ComboRow()
        type_row.set_title("Type")
        type_model = Gtk.StringList.new(BIND_TYPES)
        type_row.set_model(type_model)
        if bind:
            bt = bind.get("type", "bind")
            type_row.set_selected(BIND_TYPES.index(bt) if bt in BIND_TYPES else 0)
        type_group.add(type_row)

        # Dynamic type description label
        type_desc_label = Gtk.Label()
        type_desc_label.set_wrap(True)
        type_desc_label.set_xalign(0)
        type_desc_label.add_css_class("dim-label")
        type_desc_label.add_css_class("caption")
        type_desc_label.set_margin_start(8)
        type_desc_label.set_margin_end(8)
        type_desc_label.set_margin_bottom(4)
        type_group.add(type_desc_label)

        def update_type_desc(*_):
            bt = BIND_TYPES[type_row.get_selected()]
            type_desc_label.set_text(BIND_TYPE_DESCS.get(bt, ""))
        type_row.connect("notify::selected", update_type_desc)
        update_type_desc()

        # ── Modifier + Key ────────────────────────────────────────────────────
        mod_group = Adw.PreferencesGroup()
        mod_group.set_title("Keyboard Combination")
        mod_group.set_description("Which keys trigger this binding")
        form_box.append(mod_group)

        mod_row = Adw.ComboRow()
        mod_row.set_title("Modifier Key")
        mod_row.set_subtitle("The key you hold down (usually SUPER = Windows key)")
        mod_model = Gtk.StringList.new(MODIFIERS)
        mod_row.set_model(mod_model)
        if bind:
            mod_val = bind.get("mod", "SUPER").strip()
            if mod_val in MODIFIERS:
                mod_row.set_selected(MODIFIERS.index(mod_val))
        mod_group.add(mod_row)

        key_row = Adw.EntryRow()
        key_row.set_title("Key Name")
        key_row.set_tooltip_text(
            "Examples: T, Return, space, F1, left, right, up, down, "
            "XF86AudioRaiseVolume, Print\n"
            "Run 'wev' in a terminal to find exact key names."
        )
        if bind:
            key_row.set_text(bind.get("key", "").strip())
        mod_group.add(key_row)

        # ── Action ────────────────────────────────────────────────────────────
        disp_group = Adw.PreferencesGroup()
        disp_group.set_title("Action to Perform")
        disp_group.set_description("What happens when you press the key combination")
        form_box.append(disp_group)

        disp_row = Adw.ComboRow()
        disp_row.set_title("Dispatcher (Action)")
        disp_model = Gtk.StringList.new(DISPATCHER_NAMES)
        disp_row.set_model(disp_model)
        if bind:
            d = bind.get("dispatcher", "exec").strip()
            if d in DISPATCHER_NAMES:
                disp_row.set_selected(DISPATCHER_NAMES.index(d))
        disp_group.add(disp_row)

        # Dynamic dispatcher description
        disp_desc_label = Gtk.Label()
        disp_desc_label.set_wrap(True)
        disp_desc_label.set_xalign(0)
        disp_desc_label.add_css_class("dim-label")
        disp_desc_label.add_css_class("caption")
        disp_desc_label.set_margin_start(8)
        disp_desc_label.set_margin_end(8)
        disp_desc_label.set_margin_bottom(4)
        disp_group.add(disp_desc_label)

        def update_disp_desc(*_):
            name = DISPATCHER_NAMES[disp_row.get_selected()]
            disp_desc_label.set_text(DISPATCHER_DESCS.get(name, ""))
        disp_row.connect("notify::selected", update_disp_desc)
        update_disp_desc()

        # Custom dispatcher entry (for unlisted ones)
        custom_disp_row = Adw.EntryRow()
        custom_disp_row.set_title("Custom Dispatcher (optional)")
        custom_disp_row.set_tooltip_text(
            "If your dispatcher is not in the list above, type it here.\n"
            "This overrides the dropdown selection."
        )
        if bind:
            d = bind.get("dispatcher", "").strip()
            if d not in DISPATCHER_NAMES:
                custom_disp_row.set_text(d)
        disp_group.add(custom_disp_row)

        params_row = Adw.EntryRow()
        params_row.set_title("Parameters / Command")
        params_row.set_tooltip_text(
            "For 'exec': the program to run (e.g. kitty, firefox, $terminal)\n"
            "For 'workspace': the workspace number (e.g. 1, 2, special)\n"
            "For 'movefocus': direction (l, r, u, d)\n"
            "For 'fullscreen': 0=full, 1=maximize, 2=fullscreen no bar"
        )
        if bind:
            params_row.set_text(bind.get("params", "").strip())
        disp_group.add(params_row)

        # ── Save button ───────────────────────────────────────────────────────
        save_btn = Gtk.Button(label="Save Keybinding")
        save_btn.add_css_class("suggested-action")
        save_btn.add_css_class("pill")
        save_btn.set_margin_top(8)
        save_btn.set_margin_start(16)
        save_btn.set_margin_end(16)
        save_btn.set_margin_bottom(24)
        content_box.append(save_btn)

        def on_save(btn):
            # Custom dispatcher overrides combo if filled
            custom_disp = custom_disp_row.get_text().strip()
            dispatcher = custom_disp if custom_disp else DISPATCHER_NAMES[disp_row.get_selected()]

            new_bind = {
                "type": BIND_TYPES[type_row.get_selected()],
                "mod": MODIFIERS[mod_row.get_selected()],
                "key": key_row.get_text().strip(),
                "dispatcher": dispatcher,
                "params": params_row.get_text().strip(),
            }

            if idx >= 0:
                old_bind = copy.deepcopy(self._binds[idx])
                self._binds[idx] = new_bind
                self._rebuild_list()
                if self.undo_manager:
                    def undo(old=old_bind, new=new_bind, i=idx):
                        self._binds[i] = old
                        self._rebuild_list()
                    def redo(old=old_bind, new=new_bind, i=idx):
                        self._binds[i] = new
                        self._rebuild_list()
                    self.undo_manager.push(
                        f"Edit keybind {new_bind.get('mod','')}+{new_bind.get('key','')}",
                        undo, redo
                    )
            else:
                self._binds.append(new_bind)
                self._rebuild_list()
                if self.undo_manager:
                    new_idx = len(self._binds) - 1
                    def undo(i=new_idx):
                        self._binds.pop(i)
                        self._rebuild_list()
                    def redo(b=new_bind):
                        self._binds.append(b)
                        self._rebuild_list()
                    self.undo_manager.push(
                        f"Add keybind {new_bind.get('mod','')}+{new_bind.get('key','')}",
                        undo, redo
                    )

            dialog.close()

        save_btn.connect("clicked", on_save)
        dialog.present(self)

    def refresh(self):
        self._binds = self.parser.get_binds()
        self._rebuild_list()

    def apply_changes(self):
        self.parser.set_binds(self._binds)
