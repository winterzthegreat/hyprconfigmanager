"""
General settings page: gaps, border, layout, colors, etc.
"""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw


class GeneralPage(Gtk.ScrolledWindow):
    def __init__(self, parser):
        super().__init__()
        self.parser = parser
        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

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

        # ── Gaps ─────────────────────────────────────────────────────────────
        gaps_group = Adw.PreferencesGroup()
        gaps_group.set_title("Window Gaps (Spacing)")
        gaps_group.set_description("Control the amount of empty space between your windows")
        box.append(gaps_group)

        self.gaps_in_row = Adw.SpinRow.new_with_range(0, 100, 1)
        self.gaps_in_row.set_title("Inner Gaps")
        self.gaps_in_row.set_subtitle("Space between two adjacent windows")
        gaps_group.add(self.gaps_in_row)

        self.gaps_out_row = Adw.SpinRow.new_with_range(0, 100, 1)
        self.gaps_out_row.set_title("Outer Gaps")
        self.gaps_out_row.set_subtitle("Space between windows and the edge of your screen")
        gaps_group.add(self.gaps_out_row)

        # ── Border ───────────────────────────────────────────────────────────
        border_group = Adw.PreferencesGroup()
        border_group.set_title("Window Borders")
        border_group.set_description("Visual borders around window edges")
        box.append(border_group)

        self.border_size_row = Adw.SpinRow.new_with_range(0, 20, 1)
        self.border_size_row.set_title("Border Thickness")
        self.border_size_row.set_subtitle("Width of the highlighted border in pixels")
        border_group.add(self.border_size_row)

        self.resize_on_border_row = Adw.SwitchRow()
        self.resize_on_border_row.set_title("Resize by Dragging Borders")
        self.resize_on_border_row.set_subtitle("Easier window resizing without using mod keys")
        border_group.add(self.resize_on_border_row)

        # ── Layout ───────────────────────────────────────────────────────────
        layout_group = Adw.PreferencesGroup()
        layout_group.set_title("Window Layout Engine")
        layout_group.set_description("The algorithm used to arrange windows on screen")
        box.append(layout_group)

        self.layout_row = Adw.ComboRow()
        self.layout_row.set_title("Default Tiling Style")
        self.layout_row.set_subtitle("Dwindle (spiraling squares) or Master (one main window)")
        layout_model = Gtk.StringList.new(["dwindle", "master"])
        self.layout_row.set_model(layout_model)
        layout_group.add(self.layout_row)

        # ── Misc ─────────────────────────────────────────────────────────────
        misc_group = Adw.PreferencesGroup()
        misc_group.set_title("Advanced Display Options")
        box.append(misc_group)

        self.allow_tearing_row = Adw.SwitchRow()
        self.allow_tearing_row.set_title("Allow Screen Tearing")
        self.allow_tearing_row.set_subtitle("Disable VSync for lower input lag in competitive games")
        misc_group.add(self.allow_tearing_row)

        # ── Dwindle ──────────────────────────────────────────────────────────
        dwindle_group = Adw.PreferencesGroup()
        dwindle_group.set_title("Dwindle Style Settings")
        dwindle_group.set_description("Fine-tune the behavior of the spiraling layout")
        box.append(dwindle_group)

        self.pseudotile_row = Adw.SwitchRow()
        self.pseudotile_row.set_title("Pseudotiling Mode")
        self.pseudotile_row.set_subtitle("Allows windows to maintain their requested size while tiled")
        dwindle_group.add(self.pseudotile_row)

        self.preserve_split_row = Adw.SwitchRow()
        self.preserve_split_row.set_title("Preserve Split Direction")
        self.preserve_split_row.set_subtitle("Don't change split orientation when moving windows")
        dwindle_group.add(self.preserve_split_row)

    def refresh(self):
        """Load current values from parser into widgets."""
        p = self.parser

        self.gaps_in_row.set_value(float(p.get("general", "gaps_in", "5")))
        self.gaps_out_row.set_value(float(p.get("general", "gaps_out", "20")))
        self.border_size_row.set_value(float(p.get("general", "border_size", "1")))

        resize = p.get("general", "resize_on_border", "false").lower() == "true"
        self.resize_on_border_row.set_active(resize)

        tearing = p.get("general", "allow_tearing", "false").lower() == "true"
        self.allow_tearing_row.set_active(tearing)

        layout = p.get("general", "layout", "dwindle")
        self.layout_row.set_selected(0 if layout == "dwindle" else 1)

        pseudo = p.get("dwindle", "pseudotile", "false").lower() == "true"
        self.pseudotile_row.set_active(pseudo)

        preserve = p.get("dwindle", "preserve_split", "false").lower() == "true"
        self.preserve_split_row.set_active(preserve)

    def apply_changes(self):
        """Write current widget values back to parser."""
        p = self.parser

        p.set_value("general", "gaps_in", str(int(self.gaps_in_row.get_value())))
        p.set_value("general", "gaps_out", str(int(self.gaps_out_row.get_value())))
        p.set_value("general", "border_size", str(int(self.border_size_row.get_value())))
        p.set_value("general", "resize_on_border", "true" if self.resize_on_border_row.get_active() else "false")
        p.set_value("general", "allow_tearing", "true" if self.allow_tearing_row.get_active() else "false")

        layouts = ["dwindle", "master"]
        p.set_value("general", "layout", layouts[self.layout_row.get_selected()])

        p.set_value("dwindle", "pseudotile", "true" if self.pseudotile_row.get_active() else "false")
        p.set_value("dwindle", "preserve_split", "true" if self.preserve_split_row.get_active() else "false")
