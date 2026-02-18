"""
Input & Keyboard settings page.
"""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GLib


# Common keyboard layouts
COMMON_LAYOUTS = [
    ("us", "English (US)"),
    ("th", "Thai"),
    ("de", "German"),
    ("fr", "French"),
    ("es", "Spanish"),
    ("it", "Italian"),
    ("pt", "Portuguese"),
    ("ru", "Russian"),
    ("uk", "Ukrainian"),
    ("pl", "Polish"),
    ("nl", "Dutch"),
    ("sv", "Swedish"),
    ("no", "Norwegian"),
    ("da", "Danish"),
    ("fi", "Finnish"),
    ("cs", "Czech"),
    ("sk", "Slovak"),
    ("hu", "Hungarian"),
    ("ro", "Romanian"),
    ("tr", "Turkish"),
    ("ar", "Arabic"),
    ("he", "Hebrew"),
    ("ja", "Japanese"),
    ("ko", "Korean"),
    ("zh", "Chinese"),
    ("id", "Indonesian"),
    ("vi", "Vietnamese"),
    ("fa", "Persian"),
    ("hi", "Hindi"),
    ("bn", "Bengali"),
]

COMMON_KB_OPTIONS = [
    ("", "None"),
    ("grp:win_space_toggle", "Win+Space toggle"),
    ("grp:alt_shift_toggle", "Alt+Shift toggle"),
    ("grp:ctrl_shift_toggle", "Ctrl+Shift toggle"),
    ("grp:caps_toggle", "CapsLock toggle"),
    ("grp:shift_caps_toggle", "Shift+CapsLock toggle"),
    ("grp:lalt_lshift_toggle", "Left Alt+Left Shift toggle"),
    ("grp:lctrl_lshift_toggle", "Left Ctrl+Left Shift toggle"),
]


class InputPage(Gtk.ScrolledWindow):
    def __init__(self, parser):
        super().__init__()
        self.parser = parser
        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self._active_layouts: list[str] = []

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        clamp = Adw.Clamp()
        clamp.set_maximum_size(700)
        clamp.set_margin_top(24)
        clamp.set_margin_bottom(24)
        clamp.set_margin_start(12)
        clamp.set_margin_end(12)
        self.set_child(clamp)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        clamp.set_child(box)

        # ── Keyboard Settings ────────────────────────────────────────────────
        kb_group = Adw.PreferencesGroup()
        kb_group.set_title("Keyboard Configuration")
        kb_group.set_description("Manage your keyboard layouts and switching shortcuts")
        box.append(kb_group)

        # Active layouts list
        self.layouts_list = Gtk.ListBox()
        self.layouts_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.layouts_list.add_css_class("boxed-list")
        kb_group.add(self.layouts_list)

        # Add layout row
        add_layout_row = Adw.ActionRow()
        add_layout_row.set_title("Add New Keyboard Layout")
        add_layout_row.set_subtitle("Pick a language/layout to add to your cycle")

        self.layout_combo = Gtk.DropDown()
        layout_names = Gtk.StringList.new([f"{code} — {name}" for code, name in COMMON_LAYOUTS])
        self.layout_combo.set_model(layout_names)
        self.layout_combo.set_valign(Gtk.Align.CENTER)
        add_layout_row.add_suffix(self.layout_combo)

        add_btn = Gtk.Button(label="Add")
        add_btn.add_css_class("suggested-action")
        add_btn.set_valign(Gtk.Align.CENTER)
        add_btn.connect("clicked", self._on_add_layout)
        add_layout_row.add_suffix(add_btn)
        kb_group.add(add_layout_row)

        # ── Layout Toggle ─────────────────────────────────────────────────────
        toggle_group = Adw.PreferencesGroup()
        toggle_group.set_title("How to Switch Layouts")
        toggle_group.set_description("Choose the key combination that rotates through your active layouts")
        box.append(toggle_group)

        self.kb_options_row = Adw.ComboRow()
        self.kb_options_row.set_title("Switching Shortcut")
        self.kb_options_row.set_subtitle("Example: Win + Space")
        options_model = Gtk.StringList.new([label for _, label in COMMON_KB_OPTIONS])
        self.kb_options_row.set_model(options_model)
        toggle_group.add(self.kb_options_row)

        self.kb_options_custom_row = Adw.EntryRow()
        self.kb_options_custom_row.set_title("Custom Shortcut (XKB Option)")
        self.kb_options_custom_row.set_tooltip_text("Advanced: enter raw XKB options (e.g. grp:alt_shift_toggle)")
        toggle_group.add(self.kb_options_custom_row)

        # ── Mouse ─────────────────────────────────────────────────────────────
        mouse_group = Adw.PreferencesGroup()
        mouse_group.set_title("Mouse & Touchpad")
        mouse_group.set_description("Sensitivity and scrolling behavior")
        box.append(mouse_group)

        self.sensitivity_row = Adw.SpinRow.new_with_range(-1.0, 1.0, 0.1)
        self.sensitivity_row.set_title("Speed (Sensitivity)")
        self.sensitivity_row.set_subtitle("Lower is slower, higher is faster")
        self.sensitivity_row.set_digits(1)
        mouse_group.add(self.sensitivity_row)

        self.natural_scroll_row = Adw.SwitchRow()
        self.natural_scroll_row.set_title("Natural Scrolling")
        self.natural_scroll_row.set_subtitle("Swipe up to move content up (touchpad typical style)")
        mouse_group.add(self.natural_scroll_row)

        self.follow_mouse_row = Adw.SwitchRow()
        self.follow_mouse_row.set_title("Focus Follows Mouse")
        self.follow_mouse_row.set_subtitle("Moving the cursor over a window automatically selects it")
        mouse_group.add(self.follow_mouse_row)

    def _rebuild_layouts_list(self):
        """Rebuild the active layouts list widget."""
        # Remove all existing rows
        child = self.layouts_list.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.layouts_list.remove(child)
            child = next_child

        for i, layout in enumerate(self._active_layouts):
            row = Adw.ActionRow()
            row.set_title(layout)
            # Find display name
            for code, name in COMMON_LAYOUTS:
                if code == layout:
                    row.set_subtitle(name)
                    break

            # Remove button
            remove_btn = Gtk.Button()
            remove_btn.set_icon_name("list-remove-symbolic")
            remove_btn.add_css_class("flat")
            remove_btn.add_css_class("destructive-action")
            remove_btn.set_valign(Gtk.Align.CENTER)
            remove_btn.set_tooltip_text("Remove layout")
            idx = i  # capture
            remove_btn.connect("clicked", lambda btn, idx=idx: self._on_remove_layout(idx))
            row.add_suffix(remove_btn)

            # Move up button
            if i > 0:
                up_btn = Gtk.Button()
                up_btn.set_icon_name("go-up-symbolic")
                up_btn.add_css_class("flat")
                up_btn.set_valign(Gtk.Align.CENTER)
                up_btn.connect("clicked", lambda btn, idx=idx: self._on_move_layout(idx, -1))
                row.add_suffix(up_btn)

            self.layouts_list.append(row)

    def _on_add_layout(self, btn):
        selected = self.layout_combo.get_selected()
        code = COMMON_LAYOUTS[selected][0]
        if code not in self._active_layouts:
            self._active_layouts.append(code)
            self._rebuild_layouts_list()

    def _on_remove_layout(self, idx: int):
        if len(self._active_layouts) > 1:
            self._active_layouts.pop(idx)
            self._rebuild_layouts_list()

    def _on_move_layout(self, idx: int, direction: int):
        new_idx = idx + direction
        if 0 <= new_idx < len(self._active_layouts):
            self._active_layouts[idx], self._active_layouts[new_idx] = (
                self._active_layouts[new_idx], self._active_layouts[idx]
            )
            self._rebuild_layouts_list()

    def refresh(self):
        p = self.parser

        # Keyboard layouts
        kb_layout = p.get("input", "kb_layout", "us")
        self._active_layouts = [l.strip() for l in kb_layout.split(",") if l.strip()]
        if not self._active_layouts:
            self._active_layouts = ["us"]
        self._rebuild_layouts_list()

        # kb_options
        kb_options = p.get("input", "kb_options", "")
        found_idx = 0
        for i, (opt, _) in enumerate(COMMON_KB_OPTIONS):
            if opt == kb_options:
                found_idx = i
                break
        self.kb_options_row.set_selected(found_idx)
        self.kb_options_custom_row.set_text(kb_options)

        # Mouse
        sensitivity = float(p.get("input", "sensitivity", "0"))
        self.sensitivity_row.set_value(sensitivity)

        natural = p.get("input.touchpad", "natural_scroll", "false").lower() == "true"
        self.natural_scroll_row.set_active(natural)

        follow = p.get("input", "follow_mouse", "1")
        self.follow_mouse_row.set_active(follow == "1")

    def apply_changes(self):
        p = self.parser

        p.set_input_kb_layout(self._active_layouts)

        # kb_options: prefer custom entry if filled, else combo
        custom = self.kb_options_custom_row.get_text().strip()
        if custom:
            p.set_input_kb_options(custom)
        else:
            selected = self.kb_options_row.get_selected()
            p.set_input_kb_options(COMMON_KB_OPTIONS[selected][0])

        p.set_value("input", "sensitivity", f"{self.sensitivity_row.get_value():.1f}")
        p.set_value("input.touchpad", "natural_scroll",
                    "true" if self.natural_scroll_row.get_active() else "false")
        p.set_value("input", "follow_mouse", "1" if self.follow_mouse_row.get_active() else "0")
