"""
Monitor management page: add/edit/remove monitor configurations.
Format: name, resolution@refreshrate, position, scale
"""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw


COMMON_RESOLUTIONS = [
    "1920x1080", "2560x1440", "3840x2160", "1280x720",
    "1366x768", "1600x900", "2560x1080", "3440x1440",
    "1920x1200", "2560x1600", "1440x900", "1280x1024",
]

COMMON_REFRESH_RATES = ["60", "75", "120", "144", "165", "240", "360"]

COMMON_SCALES = ["1", "1.25", "1.5", "1.75", "2", "2.5", "3"]


def parse_monitor_str(raw: str) -> dict:
    """Parse a monitor= value string into a dict."""
    parts = [p.strip() for p in raw.split(",")]
    name = parts[0] if len(parts) > 0 else ""
    res_rate = parts[1] if len(parts) > 1 else "1920x1080@60"
    pos = parts[2] if len(parts) > 2 else "auto"
    scale = parts[3] if len(parts) > 3 else "1"

    # Parse resolution@refreshrate
    if "@" in res_rate:
        res, rate = res_rate.split("@", 1)
    else:
        res, rate = res_rate, "60"

    return {"name": name, "resolution": res, "refresh_rate": rate.rstrip("0").rstrip(".") if "." in rate else rate,
            "position": pos, "scale": scale}


def monitor_dict_to_str(d: dict) -> str:
    name = d.get("name", "")
    res = d.get("resolution", "1920x1080")
    rate = d.get("refresh_rate", "60")
    pos = d.get("position", "auto")
    scale = d.get("scale", "1")
    return f"{name},{res}@{rate},{pos},{scale}"


class MonitorPage(Gtk.Box):
    def __init__(self, parser):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.parser = parser
        self._monitors: list[dict] = []

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        toolbar.set_margin_top(12)
        toolbar.set_margin_bottom(8)
        toolbar.set_margin_start(16)
        toolbar.set_margin_end(16)
        self.append(toolbar)

        title = Gtk.Label(label="Monitors")
        title.add_css_class("title-3")
        title.set_hexpand(True)
        title.set_xalign(0)
        toolbar.append(title)

        add_btn = Gtk.Button(label="Add Monitor")
        add_btn.add_css_class("suggested-action")
        add_btn.add_css_class("pill")
        add_btn.set_icon_name("list-add-symbolic")
        add_btn.connect("clicked", self._on_add)
        toolbar.append(add_btn)

        info = Gtk.Label()
        info.set_markup('<span size="small" foreground="#888">Format: name, resolution@refreshrate, position, scale</span>')
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

        self.mon_list = Gtk.ListBox()
        self.mon_list.set_selection_mode(Gtk.SelectionMode.NONE)
        self.mon_list.add_css_class("boxed-list")
        scroll.set_child(self.mon_list)

    def _rebuild_list(self):
        child = self.mon_list.get_first_child()
        while child:
            nxt = child.get_next_sibling()
            self.mon_list.remove(child)
            child = nxt

        if not self._monitors:
            empty = Adw.ActionRow()
            empty.set_title("No monitors configured")
            empty.set_subtitle("Click 'Add Monitor' to add one")
            self.mon_list.append(empty)
            return

        for i, mon in enumerate(self._monitors):
            name = mon.get("name", "") or "(default)"
            res = mon.get("resolution", "")
            rate = mon.get("refresh_rate", "")
            pos = mon.get("position", "auto")
            scale = mon.get("scale", "1")

            row = Adw.ActionRow()
            row.set_title(f"{name}  —  {res}@{rate}Hz")
            row.set_subtitle(f"Position: {pos}  |  Scale: {scale}×")

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

            self.mon_list.append(row)

    def _on_add(self, btn):
        self._show_dialog(None, -1)

    def _on_edit(self, idx):
        self._show_dialog(self._monitors[idx], idx)

    def _on_delete(self, idx):
        self._monitors.pop(idx)
        self._rebuild_list()

    def _show_dialog(self, mon: dict | None, idx: int):
        dialog = Adw.Dialog()
        dialog.set_title("Add Monitor" if mon is None else "Edit Monitor")
        dialog.set_content_width(620)
        dialog.set_content_height(680)

        tv = Adw.ToolbarView()
        dialog.set_child(tv)
        tv.add_top_bar(Adw.HeaderBar())

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        tv.set_content(content)

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        content.append(scroll)

        clamp = Adw.Clamp()
        clamp.set_maximum_size(560)
        clamp.set_margin_top(16)
        clamp.set_margin_bottom(8)
        clamp.set_margin_start(16)
        clamp.set_margin_end(16)
        scroll.set_child(clamp)

        form = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        clamp.set_child(form)

        # Monitor name
        id_group = Adw.PreferencesGroup()
        id_group.set_title("Monitor Identifier")
        id_group.set_description("Leave empty for default (,) or use output name like HDMI-A-1, DP-1")
        form.append(id_group)

        name_row = Adw.EntryRow()
        name_row.set_title("Output Name")
        name_row.set_tooltip_text("e.g. HDMI-A-1, DP-1, eDP-1, or leave empty")
        if mon:
            name_row.set_text(mon.get("name", ""))
        id_group.add(name_row)

        # Resolution
        res_group = Adw.PreferencesGroup()
        res_group.set_title("Resolution & Refresh Rate")
        res_group.set_description("Size of the screen followed by the smoothness (Hz)")
        form.append(res_group)

        res_row = Adw.ComboRow()
        res_row.set_title("Resolution")
        res_row.set_subtitle("Common desktop resolutions")
        res_model = Gtk.StringList.new(COMMON_RESOLUTIONS + ["preferred"])
        res_row.set_model(res_model)
        if mon:
            r = mon.get("resolution", "1920x1080")
            if r in COMMON_RESOLUTIONS:
                res_row.set_selected(COMMON_RESOLUTIONS.index(r))
        res_group.add(res_row)

        custom_res_row = Adw.EntryRow()
        custom_res_row.set_title("Custom Resolution (e.g. 2560x1440)")
        custom_res_row.set_tooltip_text("Overrides the dropdown choice if filled")
        if mon:
            r = mon.get("resolution", "")
            if r not in COMMON_RESOLUTIONS and r != "preferred":
                custom_res_row.set_text(r)
        res_group.add(custom_res_row)

        rate_row = Adw.ComboRow()
        rate_row.set_title("Refresh Rate (Hz)")
        rate_row.set_subtitle("Frames per second (higher is smoother)")
        rate_model = Gtk.StringList.new(COMMON_REFRESH_RATES)
        rate_row.set_model(rate_model)
        if mon:
            rate = mon.get("refresh_rate", "60").split(".")[0]
            if rate in COMMON_REFRESH_RATES:
                rate_row.set_selected(COMMON_REFRESH_RATES.index(rate))
        res_group.add(rate_row)

        custom_rate_row = Adw.EntryRow()
        custom_rate_row.set_title("Custom Refresh Rate (e.g. 144.0)")
        if mon:
            rate = mon.get("refresh_rate", "")
            if rate.split(".")[0] not in COMMON_REFRESH_RATES:
                custom_rate_row.set_text(rate)
        res_group.add(custom_rate_row)

        # Position & Scale
        pos_group = Adw.PreferencesGroup()
        pos_group.set_title("Position &amp; Scale")
        pos_group.set_description("Where the monitor sits in your multi-display setup")
        form.append(pos_group)

        pos_row = Adw.EntryRow()
        pos_row.set_title("Screen Position (auto or 1920x0)")
        pos_row.set_text(mon.get("position", "auto") if mon else "auto")
        pos_group.add(pos_row)

        scale_row = Adw.ComboRow()
        scale_row.set_title("Interface Scale")
        scale_row.set_subtitle("1 = Normal, 2 = High DPI (Retina)")
        scale_model = Gtk.StringList.new(COMMON_SCALES)
        scale_row.set_model(scale_model)
        if mon:
            s = mon.get("scale", "1")
            if s in COMMON_SCALES:
                scale_row.set_selected(COMMON_SCALES.index(s))
        pos_group.add(scale_row)

        custom_scale_row = Adw.EntryRow()
        custom_scale_row.set_title("Custom Scale (e.g. 1.25)")
        if mon:
            s = mon.get("scale", "1")
            if s not in COMMON_SCALES:
                custom_scale_row.set_text(s)
        pos_group.add(custom_scale_row)

        save_btn = Gtk.Button(label="Save")
        save_btn.add_css_class("suggested-action")
        save_btn.add_css_class("pill")
        save_btn.set_margin_top(8)
        save_btn.set_margin_start(16)
        save_btn.set_margin_end(16)
        save_btn.set_margin_bottom(16)
        content.append(save_btn)

        def on_save(btn):
            name = name_row.get_text().strip()
            res = custom_res_row.get_text().strip() or COMMON_RESOLUTIONS[res_row.get_selected()]
            rate = custom_rate_row.get_text().strip() or COMMON_REFRESH_RATES[rate_row.get_selected()]
            pos = pos_row.get_text().strip() or "auto"
            scale = custom_scale_row.get_text().strip() or COMMON_SCALES[scale_row.get_selected()]

            new_mon = {"name": name, "resolution": res, "refresh_rate": rate,
                       "position": pos, "scale": scale}
            if idx >= 0:
                self._monitors[idx] = new_mon
            else:
                self._monitors.append(new_mon)
            self._rebuild_list()
            dialog.close()

        save_btn.connect("clicked", on_save)
        dialog.present(self)

    def refresh(self):
        raw = self.parser.get_monitors()
        self._monitors = [parse_monitor_str(r) for r in raw]
        self._rebuild_list()

    def apply_changes(self):
        self.parser.set_monitors([monitor_dict_to_str(m) for m in self._monitors])
