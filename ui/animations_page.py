"""
Animations management page: animation= and bezier= entries.
"""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw


ANIMATION_NAMES = [
    "global", "border", "borderangle", "fade", "fadeIn", "fadeOut",
    "fadeSwitch", "fadeShadow", "fadeDim", "fadeLayersIn", "fadeLayersOut",
    "windows", "windowsIn", "windowsOut", "windowsMove",
    "layers", "layersIn", "layersOut",
    "workspaces", "workspacesIn", "workspacesOut",
    "specialWorkspace", "specialWorkspaceIn", "specialWorkspaceOut",
    "zoomFactor",
]

ANIMATION_STYLES = {
    "windows": ["", "slide", "popin", "fade"],
    "windowsIn": ["", "slide", "popin", "fade"],
    "windowsOut": ["", "slide", "popin", "fade"],
    "layers": ["", "slide", "popin", "fade"],
    "layersIn": ["", "slide", "popin", "fade"],
    "layersOut": ["", "slide", "popin", "fade"],
    "workspaces": ["", "slide", "slidevert", "fade"],
    "workspacesIn": ["", "slide", "slidevert", "fade"],
    "workspacesOut": ["", "slide", "slidevert", "fade"],
    "specialWorkspace": ["", "slide", "slidevert", "fade"],
}


class AnimationsPage(Gtk.Box):
    def __init__(self, parser):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.parser = parser
        self._animations: list[dict] = []
        self._beziers: list[dict] = []

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        # Master enable switch
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        header_box.set_margin_top(12)
        header_box.set_margin_bottom(8)
        header_box.set_margin_start(16)
        header_box.set_margin_end(16)
        self.append(header_box)

        title = Gtk.Label(label="Animations")
        title.add_css_class("title-3")
        title.set_hexpand(True)
        title.set_xalign(0)
        header_box.append(title)

        # Scrollable content
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)
        scroll.set_margin_start(16)
        scroll.set_margin_end(16)
        scroll.set_margin_bottom(16)
        self.append(scroll)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        content.set_margin_top(8)
        content.set_margin_bottom(8)
        scroll.set_child(content)

        # Global enable
        global_group = Adw.PreferencesGroup()
        global_group.set_title("Global")
        content.append(global_group)

        self.global_enabled_row = Adw.SwitchRow()
        self.global_enabled_row.set_title("Global Animation Switch")
        self.global_enabled_row.set_subtitle("Enable or disable all window and workspace animations instantly")
        global_group.add(self.global_enabled_row)

        # Bezier curves section
        bezier_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        bezier_header.set_margin_top(8)
        content.append(bezier_header)

        bezier_title = Gtk.Label(label="Bezier Curves")
        bezier_title.add_css_class("title-4")
        bezier_title.set_hexpand(True)
        bezier_title.set_xalign(0)
        bezier_header.append(bezier_title)

        add_bezier_btn = Gtk.Button(label="Add Curve")
        add_bezier_btn.add_css_class("pill")
        add_bezier_btn.set_icon_name("list-add-symbolic")
        add_bezier_btn.connect("clicked", self._on_add_bezier)
        bezier_header.append(add_bezier_btn)

        self.bezier_list = Gtk.ListBox()
        self.bezier_list.set_selection_mode(Gtk.SelectionMode.NONE)
        self.bezier_list.add_css_class("boxed-list")
        content.append(self.bezier_list)

        # Animations section
        anim_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        anim_header.set_margin_top(8)
        content.append(anim_header)

        anim_title = Gtk.Label(label="Animation Entries")
        anim_title.add_css_class("title-4")
        anim_title.set_hexpand(True)
        anim_title.set_xalign(0)
        anim_header.append(anim_title)

        add_anim_btn = Gtk.Button(label="Add Animation")
        add_anim_btn.add_css_class("suggested-action")
        add_anim_btn.add_css_class("pill")
        add_anim_btn.set_icon_name("list-add-symbolic")
        add_anim_btn.connect("clicked", self._on_add_anim)
        anim_header.append(add_anim_btn)

        self.anim_list = Gtk.ListBox()
        self.anim_list.set_selection_mode(Gtk.SelectionMode.NONE)
        self.anim_list.add_css_class("boxed-list")
        content.append(self.anim_list)

    def _rebuild_bezier_list(self):
        child = self.bezier_list.get_first_child()
        while child:
            nxt = child.get_next_sibling()
            self.bezier_list.remove(child)
            child = nxt

        if not self._beziers:
            empty = Adw.ActionRow()
            empty.set_title("No bezier curves")
            self.bezier_list.append(empty)
            return

        for i, b in enumerate(self._beziers):
            row = Adw.ActionRow()
            row.set_title(b.get("name", ""))
            row.set_subtitle(f"({b.get('x0','0')}, {b.get('y0','0')}, {b.get('x1','1')}, {b.get('y1','1')})")

            edit_btn = Gtk.Button()
            edit_btn.set_icon_name("document-edit-symbolic")
            edit_btn.add_css_class("flat")
            edit_btn.set_valign(Gtk.Align.CENTER)
            edit_btn.connect("clicked", lambda btn, idx=i: self._on_edit_bezier(idx))
            row.add_suffix(edit_btn)

            del_btn = Gtk.Button()
            del_btn.set_icon_name("list-remove-symbolic")
            del_btn.add_css_class("flat")
            del_btn.add_css_class("destructive-action")
            del_btn.set_valign(Gtk.Align.CENTER)
            del_btn.connect("clicked", lambda btn, idx=i: self._on_delete_bezier(idx))
            row.add_suffix(del_btn)

            self.bezier_list.append(row)

    def _rebuild_anim_list(self):
        child = self.anim_list.get_first_child()
        while child:
            nxt = child.get_next_sibling()
            self.anim_list.remove(child)
            child = nxt

        if not self._animations:
            empty = Adw.ActionRow()
            empty.set_title("No animations")
            self.anim_list.append(empty)
            return

        for i, a in enumerate(self._animations):
            row = Adw.ActionRow()
            name = a.get("name", "")
            onoff = "on" if a.get("onoff", "1") == "1" else "off"
            speed = a.get("speed", "1")
            curve = a.get("curve", "default")
            style = a.get("style", "")

            row.set_title(name)
            subtitle = f"{onoff}  |  speed: {speed}  |  curve: {curve}"
            if style:
                subtitle += f"  |  style: {style}"
            row.set_subtitle(subtitle)

            # Toggle on/off
            toggle = Gtk.Switch()
            toggle.set_active(a.get("onoff", "1") == "1")
            toggle.set_valign(Gtk.Align.CENTER)
            toggle.connect("state-set", lambda sw, state, idx=i: self._toggle_anim(idx, state))
            row.add_suffix(toggle)

            edit_btn = Gtk.Button()
            edit_btn.set_icon_name("document-edit-symbolic")
            edit_btn.add_css_class("flat")
            edit_btn.set_valign(Gtk.Align.CENTER)
            edit_btn.connect("clicked", lambda btn, idx=i: self._on_edit_anim(idx))
            row.add_suffix(edit_btn)

            del_btn = Gtk.Button()
            del_btn.set_icon_name("list-remove-symbolic")
            del_btn.add_css_class("flat")
            del_btn.add_css_class("destructive-action")
            del_btn.set_valign(Gtk.Align.CENTER)
            del_btn.connect("clicked", lambda btn, idx=i: self._on_delete_anim(idx))
            row.add_suffix(del_btn)

            self.anim_list.append(row)

    def _toggle_anim(self, idx: int, state: bool):
        self._animations[idx]["onoff"] = "1" if state else "0"

    def _on_add_bezier(self, btn):
        self._show_bezier_dialog(None, -1)

    def _on_edit_bezier(self, idx):
        self._show_bezier_dialog(self._beziers[idx], idx)

    def _on_delete_bezier(self, idx):
        self._beziers.pop(idx)
        self._rebuild_bezier_list()

    def _on_add_anim(self, btn):
        self._show_anim_dialog(None, -1)

    def _on_edit_anim(self, idx):
        self._show_anim_dialog(self._animations[idx], idx)

    def _on_delete_anim(self, idx):
        self._animations.pop(idx)
        self._rebuild_anim_list()

    def _show_bezier_dialog(self, bezier: dict | None, idx: int):
        dialog = Adw.Dialog()
        dialog.set_title("Bezier Curve")
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
        group.set_title("Curve Shape")
        group.set_description("Define the 'feel' of the animation using control points")
        form.append(group)

        name_row = Adw.EntryRow()
        name_row.set_title("Name")
        name_row.set_text(bezier.get("name", "") if bezier else "")
        group.add(name_row)

        def make_spin(label, val, lo=-2.0, hi=2.0):
            row = Adw.SpinRow.new_with_range(lo, hi, 0.01)
            row.set_title(label)
            row.set_digits(2)
            row.set_value(float(val))
            return row

        x0_row = make_spin("X0", bezier.get("x0", "0") if bezier else "0")
        y0_row = make_spin("Y0", bezier.get("y0", "0") if bezier else "0")
        x1_row = make_spin("X1", bezier.get("x1", "1") if bezier else "1")
        y1_row = make_spin("Y1", bezier.get("y1", "1") if bezier else "1")
        group.add(x0_row)
        group.add(y0_row)
        group.add(x1_row)
        group.add(y1_row)

        # Presets
        presets_group = Adw.PreferencesGroup()
        presets_group.set_title("Animation Presets")
        presets_group.set_description("Quickly pick a pre-defined animation style")
        form.append(presets_group)

        presets = [
            ("linear", 0, 0, 1, 1),
            ("easeOutQuint", 0.23, 1, 0.32, 1),
            ("easeInOutCubic", 0.65, 0.05, 0.36, 1),
            ("easeOutExpo", 0.16, 1, 0.3, 1),
            ("easeInOutQuart", 0.76, 0, 0.24, 1),
        ]
        for pname, px0, py0, px1, py1 in presets:
            prow = Adw.ActionRow()
            prow.set_title(pname)
            prow.set_subtitle(f"({px0}, {py0}, {px1}, {py1})")
            prow.set_activatable(True)
            prow.connect("activated", lambda r, n=pname, a=px0, b=py0, c=px1, d=py1: (
                name_row.set_text(n),
                x0_row.set_value(a), y0_row.set_value(b),
                x1_row.set_value(c), y1_row.set_value(d),
            ))
            presets_group.add(prow)

        save_btn = Gtk.Button(label="Save")
        save_btn.add_css_class("suggested-action")
        save_btn.add_css_class("pill")
        save_btn.set_margin_top(8)
        save_btn.set_margin_start(16)
        save_btn.set_margin_end(16)
        save_btn.set_margin_bottom(16)
        content.append(save_btn)

        def on_save(btn):
            new_b = {
                "name": name_row.get_text().strip(),
                "x0": f"{x0_row.get_value():.2f}",
                "y0": f"{y0_row.get_value():.2f}",
                "x1": f"{x1_row.get_value():.2f}",
                "y1": f"{y1_row.get_value():.2f}",
            }
            if idx >= 0:
                self._beziers[idx] = new_b
            else:
                self._beziers.append(new_b)
            self._rebuild_bezier_list()
            dialog.close()

        save_btn.connect("clicked", on_save)
        dialog.present(self)

    def _show_anim_dialog(self, anim: dict | None, idx: int):
        dialog = Adw.Dialog()
        dialog.set_title("Animation Entry")
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
        group.set_title("Component Settings")
        group.set_description("Which UI element should animate, and how fast")
        form.append(group)

        name_row = Adw.ComboRow()
        name_row.set_title("Animation Name")
        name_model = Gtk.StringList.new(ANIMATION_NAMES)
        name_row.set_model(name_model)
        if anim:
            n = anim.get("name", "global")
            if n in ANIMATION_NAMES:
                name_row.set_selected(ANIMATION_NAMES.index(n))
        group.add(name_row)

        enabled_row = Adw.SwitchRow()
        enabled_row.set_title("Enabled")
        enabled_row.set_active(anim.get("onoff", "1") == "1" if anim else True)
        group.add(enabled_row)

        speed_row = Adw.SpinRow.new_with_range(0.1, 20.0, 0.1)
        speed_row.set_title("Speed")
        speed_row.set_digits(2)
        speed_row.set_value(float(anim.get("speed", "1")) if anim else 1.0)
        group.add(speed_row)

        # Curve: list bezier names + default
        curve_names = ["default"] + [b.get("name", "") for b in self._beziers if b.get("name")]
        curve_row = Adw.ComboRow()
        curve_row.set_title("Curve (Bezier)")
        curve_model = Gtk.StringList.new(curve_names)
        curve_row.set_model(curve_model)
        if anim:
            c = anim.get("curve", "default")
            if c in curve_names:
                curve_row.set_selected(curve_names.index(c))
        group.add(curve_row)

        style_row = Adw.EntryRow()
        style_row.set_title("Style (optional)")
        style_row.set_tooltip_text("e.g. slide, popin 87%, fade")
        if anim:
            style_row.set_text(anim.get("style", ""))
        group.add(style_row)

        save_btn = Gtk.Button(label="Save")
        save_btn.add_css_class("suggested-action")
        save_btn.add_css_class("pill")
        save_btn.set_margin_top(8)
        save_btn.set_margin_start(16)
        save_btn.set_margin_end(16)
        save_btn.set_margin_bottom(16)
        content.append(save_btn)

        def on_save(btn):
            new_a = {
                "name": ANIMATION_NAMES[name_row.get_selected()],
                "onoff": "1" if enabled_row.get_active() else "0",
                "speed": f"{speed_row.get_value():.2f}",
                "curve": curve_names[curve_row.get_selected()],
                "style": style_row.get_text().strip(),
            }
            if idx >= 0:
                self._animations[idx] = new_a
            else:
                self._animations.append(new_a)
            self._rebuild_anim_list()
            dialog.close()

        save_btn.connect("clicked", on_save)
        dialog.present(self)

    def refresh(self):
        p = self.parser
        self._animations = p.get_animations()
        self._beziers = p.get_beziers()

        # Check global enabled from first animation named "global"
        global_on = True
        for a in self._animations:
            if a.get("name") == "global":
                global_on = a.get("onoff", "1") == "1"
                break
        self.global_enabled_row.set_active(global_on)

        self._rebuild_bezier_list()
        self._rebuild_anim_list()

    def apply_changes(self):
        # Update global animation onoff
        global_on = "1" if self.global_enabled_row.get_active() else "0"
        for a in self._animations:
            if a.get("name") == "global":
                a["onoff"] = global_on
                break

        self.parser.set_animations(self._animations, self._beziers)
