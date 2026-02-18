"""
Gestures management page.
"""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw


FINGER_COUNTS = ["3", "4", "5"]
DIRECTIONS = ["horizontal", "vertical", "up", "down", "left", "right"]
GESTURE_ACTIONS = [
    "workspace",
    "exec",
    "fullscreen",
    "killactive",
    "togglefloating",
    "movefocus",
]


class GesturesPage(Gtk.Box):
    def __init__(self, parser):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.parser = parser
        self._gestures: list[dict] = []

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        toolbar.set_margin_top(12)
        toolbar.set_margin_bottom(8)
        toolbar.set_margin_start(16)
        toolbar.set_margin_end(16)
        self.append(toolbar)

        title = Gtk.Label(label="Gestures")
        title.add_css_class("title-3")
        title.set_hexpand(True)
        title.set_xalign(0)
        toolbar.append(title)

        add_btn = Gtk.Button(label="Add Gesture")
        add_btn.add_css_class("suggested-action")
        add_btn.add_css_class("pill")
        add_btn.set_icon_name("list-add-symbolic")
        add_btn.connect("clicked", self._on_add)
        toolbar.append(add_btn)

        info = Gtk.Label()
        info.set_markup('<span size="small" foreground="#888">Format: gesture = fingers, direction, action[, params]</span>')
        info.set_margin_start(16)
        info.set_margin_end(16)
        info.set_margin_bottom(8)
        info.set_xalign(0)
        self.append(info)

        # Touchpad gestures settings
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)
        scroll.set_margin_start(16)
        scroll.set_margin_end(16)
        scroll.set_margin_bottom(16)
        self.append(scroll)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        content.set_margin_top(8)
        scroll.set_child(content)

        # Built-in touchpad gesture settings
        tp_group = Adw.PreferencesGroup()
        tp_group.set_title("Auto Workspace Swiping")
        tp_group.set_description("Easily switch between workspaces using touchpad gestures")
        content.append(tp_group)

        self.workspace_swipe_row = Adw.SwitchRow()
        self.workspace_swipe_row.set_title("Enable Workspace Swiping")
        self.workspace_swipe_row.set_subtitle("Use 3 fingers to slide between adjacent workspaces")
        tp_group.add(self.workspace_swipe_row)

        self.workspace_swipe_fingers_row = Adw.SpinRow.new_with_range(3, 5, 1)
        self.workspace_swipe_fingers_row.set_title("Number of Fingers")
        self.workspace_swipe_fingers_row.set_subtitle("How many fingers to use for the swipe (default is 3)")
        tp_group.add(self.workspace_swipe_fingers_row)

        self.workspace_swipe_distance_row = Adw.SpinRow.new_with_range(50, 1000, 10)
        self.workspace_swipe_distance_row.set_title("Swipe Sensitivity (Distance)")
        self.workspace_swipe_distance_row.set_subtitle("Distance in pixels you need to travel to switch")
        tp_group.add(self.workspace_swipe_distance_row)

        self.workspace_swipe_cancel_ratio_row = Adw.SpinRow.new_with_range(0.0, 1.0, 0.05)
        self.workspace_swipe_cancel_ratio_row.set_title("Commit Threshold")
        self.workspace_swipe_cancel_ratio_row.set_subtitle("How far to swipe before the switch is 'locked in'")
        self.workspace_swipe_cancel_ratio_row.set_digits(2)
        tp_group.add(self.workspace_swipe_cancel_ratio_row)

        self.workspace_swipe_invert_row = Adw.SwitchRow()
        self.workspace_swipe_invert_row.set_title("Invert Swipe Direction")
        self.workspace_swipe_invert_row.set_subtitle("Switch direction (natural vs classical)")
        tp_group.add(self.workspace_swipe_invert_row)

        self.workspace_swipe_forever_row = Adw.SwitchRow()
        self.workspace_swipe_forever_row.set_title("Loop Workspace Switching")
        self.workspace_swipe_forever_row.set_subtitle("Keep swiping past the last workspace to jump back to the first")
        tp_group.add(self.workspace_swipe_forever_row)

        # Custom gesture= lines
        gest_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        gest_header.set_margin_top(8)
        content.append(gest_header)

        gest_title = Gtk.Label(label="Custom Gestures")
        gest_title.add_css_class("title-4")
        gest_title.set_hexpand(True)
        gest_title.set_xalign(0)
        gest_header.append(gest_title)

        self.gest_list = Gtk.ListBox()
        self.gest_list.set_selection_mode(Gtk.SelectionMode.NONE)
        self.gest_list.add_css_class("boxed-list")
        content.append(self.gest_list)

    def _rebuild_list(self):
        child = self.gest_list.get_first_child()
        while child:
            nxt = child.get_next_sibling()
            self.gest_list.remove(child)
            child = nxt

        if not self._gestures:
            empty = Adw.ActionRow()
            empty.set_title("No custom gestures")
            empty.set_subtitle("Click 'Add Gesture' to add one")
            self.gest_list.append(empty)
            return

        for i, g in enumerate(self._gestures):
            row = Adw.ActionRow()
            fingers = g.get("fingers", "3")
            direction = g.get("direction", "horizontal")
            action = g.get("action", "workspace")
            params = g.get("params", "")

            row.set_title(f"{fingers}-finger {direction}")
            subtitle = action
            if params:
                subtitle += f"  →  {params}"
            row.set_subtitle(subtitle)

            edit_btn = Gtk.Button()
            edit_btn.set_icon_name("document-edit-symbolic")
            edit_btn.add_css_class("flat")
            edit_btn.set_valign(Gtk.Align.CENTER)
            edit_btn.connect("clicked", lambda btn, idx=i: self._on_edit(idx))
            row.add_suffix(edit_btn)

            del_btn = Gtk.Button()
            del_btn.set_icon_name("list-remove-symbolic")
            del_btn.add_css_class("flat")
            del_btn.add_css_class("destructive-action")
            del_btn.set_valign(Gtk.Align.CENTER)
            del_btn.connect("clicked", lambda btn, idx=i: self._on_delete(idx))
            row.add_suffix(del_btn)

            self.gest_list.append(row)

    def _on_add(self, btn):
        self._show_dialog(None, -1)

    def _on_edit(self, idx):
        self._show_dialog(self._gestures[idx], idx)

    def _on_delete(self, idx):
        self._gestures.pop(idx)
        self._rebuild_list()

    def _show_dialog(self, gest: dict | None, idx: int):
        dialog = Adw.Dialog()
        dialog.set_title("Gesture")
        dialog.set_content_width(420)

        tv = Adw.ToolbarView()
        dialog.set_child(tv)
        tv.add_top_bar(Adw.HeaderBar())

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        tv.set_content(content)

        clamp = Adw.Clamp()
        clamp.set_maximum_size(380)
        clamp.set_margin_top(16)
        clamp.set_margin_bottom(8)
        clamp.set_margin_start(16)
        clamp.set_margin_end(16)
        content.append(clamp)

        form = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        clamp.set_child(form)

        group = Adw.PreferencesGroup()
        group.set_title("Gesture")
        form.append(group)

        fingers_row = Adw.ComboRow()
        fingers_row.set_title("Fingers")
        fingers_model = Gtk.StringList.new(FINGER_COUNTS)
        fingers_row.set_model(fingers_model)
        if gest:
            f = gest.get("fingers", "3")
            if f in FINGER_COUNTS:
                fingers_row.set_selected(FINGER_COUNTS.index(f))
        group.add(fingers_row)

        dir_row = Adw.ComboRow()
        dir_row.set_title("Direction")
        dir_model = Gtk.StringList.new(DIRECTIONS)
        dir_row.set_model(dir_model)
        if gest:
            d = gest.get("direction", "horizontal")
            if d in DIRECTIONS:
                dir_row.set_selected(DIRECTIONS.index(d))
        group.add(dir_row)

        action_row = Adw.ComboRow()
        action_row.set_title("Action")
        action_model = Gtk.StringList.new(GESTURE_ACTIONS)
        action_row.set_model(action_model)
        if gest:
            a = gest.get("action", "workspace")
            if a in GESTURE_ACTIONS:
                action_row.set_selected(GESTURE_ACTIONS.index(a))
        group.add(action_row)

        params_row = Adw.EntryRow()
        params_row.set_title("Params (optional)")
        params_row.set_tooltip_text("e.g. for workspace: leave empty (uses swipe direction)")
        if gest:
            params_row.set_text(gest.get("params", ""))
        group.add(params_row)

        save_btn = Gtk.Button(label="Save")
        save_btn.add_css_class("suggested-action")
        save_btn.add_css_class("pill")
        save_btn.set_margin_top(8)
        save_btn.set_margin_start(16)
        save_btn.set_margin_end(16)
        save_btn.set_margin_bottom(16)
        content.append(save_btn)

        def on_save(btn):
            new_g = {
                "fingers": FINGER_COUNTS[fingers_row.get_selected()],
                "direction": DIRECTIONS[dir_row.get_selected()],
                "action": GESTURE_ACTIONS[action_row.get_selected()],
                "params": params_row.get_text().strip(),
            }
            if idx >= 0:
                self._gestures[idx] = new_g
            else:
                self._gestures.append(new_g)
            self._rebuild_list()
            dialog.close()

        save_btn.connect("clicked", on_save)
        dialog.present(self)

    def refresh(self):
        p = self.parser
        self._gestures = p.get_gestures()

        # Load touchpad gesture settings
        self.workspace_swipe_row.set_active(
            p.get("input.gestures", "workspace_swipe", "false").lower() == "true")
        self.workspace_swipe_fingers_row.set_value(
            float(p.get("input.gestures", "workspace_swipe_fingers", "3")))
        self.workspace_swipe_distance_row.set_value(
            float(p.get("input.gestures", "workspace_swipe_distance", "300")))
        self.workspace_swipe_cancel_ratio_row.set_value(
            float(p.get("input.gestures", "workspace_swipe_cancel_ratio", "0.5")))
        self.workspace_swipe_invert_row.set_active(
            p.get("input.gestures", "workspace_swipe_invert", "true").lower() == "true")
        self.workspace_swipe_forever_row.set_active(
            p.get("input.gestures", "workspace_swipe_forever", "false").lower() == "true")

        self._rebuild_list()

    def apply_changes(self):
        p = self.parser
        p.set_value("input.gestures", "workspace_swipe",
                    "true" if self.workspace_swipe_row.get_active() else "false")
        p.set_value("input.gestures", "workspace_swipe_fingers",
                    str(int(self.workspace_swipe_fingers_row.get_value())))
        p.set_value("input.gestures", "workspace_swipe_distance",
                    str(int(self.workspace_swipe_distance_row.get_value())))
        p.set_value("input.gestures", "workspace_swipe_cancel_ratio",
                    f"{self.workspace_swipe_cancel_ratio_row.get_value():.2f}")
        p.set_value("input.gestures", "workspace_swipe_invert",
                    "true" if self.workspace_swipe_invert_row.get_active() else "false")
        p.set_value("input.gestures", "workspace_swipe_forever",
                    "true" if self.workspace_swipe_forever_row.get_active() else "false")
        p.set_gestures(self._gestures)
