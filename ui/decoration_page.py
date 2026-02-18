"""
Decoration settings page: rounding, opacity, shadow, blur.
"""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw


class DecorationPage(Gtk.ScrolledWindow):
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

        # ── Rounding ─────────────────────────────────────────────────────────
        rounding_group = Adw.PreferencesGroup()
        rounding_group.set_title("Corner Rounding Style")
        rounding_group.set_description("Make your windows look softer with rounded corners")
        box.append(rounding_group)

        self.rounding_row = Adw.SpinRow.new_with_range(0, 30, 1)
        self.rounding_row.set_title("Corner Radius")
        self.rounding_row.set_subtitle("Rounded corner radius in pixels (0 for square)")
        rounding_group.add(self.rounding_row)

        self.rounding_power_row = Adw.SpinRow.new_with_range(1.0, 10.0, 0.1)
        self.rounding_power_row.set_title("Smoothness Curve")
        self.rounding_power_row.set_subtitle("Higher values make corners look 'squiircle' shaped")
        self.rounding_power_row.set_digits(1)
        rounding_group.add(self.rounding_power_row)

        # ── Opacity ───────────────────────────────────────────────────────────
        opacity_group = Adw.PreferencesGroup()
        opacity_group.set_title("Window Transparency")
        opacity_group.set_description("Adjust how see-through windows are")
        box.append(opacity_group)

        self.active_opacity_row = Adw.SpinRow.new_with_range(0.0, 1.0, 0.05)
        self.active_opacity_row.set_title("Focused Window Opacity")
        self.active_opacity_row.set_subtitle("1.0 = fully solid, lower = more transparent")
        self.active_opacity_row.set_digits(2)
        opacity_group.add(self.active_opacity_row)

        self.inactive_opacity_row = Adw.SpinRow.new_with_range(0.0, 1.0, 0.05)
        self.inactive_opacity_row.set_title("Background Window Opacity")
        self.inactive_opacity_row.set_subtitle("Transparency level for non-focused windows")
        self.inactive_opacity_row.set_digits(2)
        opacity_group.add(self.inactive_opacity_row)

        # ── Shadow ───────────────────────────────────────────────────────────
        shadow_group = Adw.PreferencesGroup()
        shadow_group.set_title("Drop Shadow Effects")
        shadow_group.set_description("Settings to give windows a sense of depth")
        box.append(shadow_group)

        self.shadow_enabled_row = Adw.SwitchRow()
        self.shadow_enabled_row.set_title("Enable Drop Shadows")
        self.shadow_enabled_row.set_subtitle("Draw shadows underneath windows")
        shadow_group.add(self.shadow_enabled_row)

        self.shadow_range_row = Adw.SpinRow.new_with_range(0, 100, 1)
        self.shadow_range_row.set_title("Shadow Blur Range")
        self.shadow_range_row.set_subtitle("The softness/size of the shadow in pixels")
        shadow_group.add(self.shadow_range_row)

        self.shadow_render_power_row = Adw.SpinRow.new_with_range(1, 4, 1)
        self.shadow_render_power_row.set_title("Shadow Render Detail")
        self.shadow_render_power_row.set_subtitle("Higher values make shadows look more detailed but heavier")
        shadow_group.add(self.shadow_render_power_row)

        # ── Blur ─────────────────────────────────────────────────────────────
        blur_group = Adw.PreferencesGroup()
        blur_group.set_title("Glass Blur Effects")
        blur_group.set_description("Apply high-quality blur to transparent surfaces")
        box.append(blur_group)

        self.blur_enabled_row = Adw.SwitchRow()
        self.blur_enabled_row.set_title("Activate Back Blur")
        self.blur_enabled_row.set_subtitle("Makes transparent windows look like frosted glass")
        blur_group.add(self.blur_enabled_row)

        self.blur_size_row = Adw.SpinRow.new_with_range(1, 20, 1)
        self.blur_size_row.set_title("Blur Thickness")
        self.blur_size_row.set_subtitle("The radius of the blur effect")
        blur_group.add(self.blur_size_row)

        self.blur_passes_row = Adw.SpinRow.new_with_range(1, 10, 1)
        self.blur_passes_row.set_title("Blur Quality (Passes)")
        self.blur_passes_row.set_subtitle("More passes = smoother blur but uses more GPU")
        blur_group.add(self.blur_passes_row)

        self.blur_vibrancy_row = Adw.SpinRow.new_with_range(0.0, 1.0, 0.01)
        self.blur_vibrancy_row.set_title("Color Vibrancy")
        self.blur_vibrancy_row.set_subtitle("Adjust the color saturation behind blurred windows")
        self.blur_vibrancy_row.set_digits(4)
        blur_group.add(self.blur_vibrancy_row)

    def refresh(self):
        p = self.parser

        self.rounding_row.set_value(float(p.get("decoration", "rounding", "10")))
        self.rounding_power_row.set_value(float(p.get("decoration", "rounding_power", "2")))
        self.active_opacity_row.set_value(float(p.get("decoration", "active_opacity", "1.0")))
        self.inactive_opacity_row.set_value(float(p.get("decoration", "inactive_opacity", "1.0")))

        shadow_en = p.get("decoration.shadow", "enabled", "true").lower() == "true"
        self.shadow_enabled_row.set_active(shadow_en)
        self.shadow_range_row.set_value(float(p.get("decoration.shadow", "range", "4")))
        self.shadow_render_power_row.set_value(float(p.get("decoration.shadow", "render_power", "3")))

        blur_en = p.get("decoration.blur", "enabled", "true").lower() == "true"
        self.blur_enabled_row.set_active(blur_en)
        self.blur_size_row.set_value(float(p.get("decoration.blur", "size", "3")))
        self.blur_passes_row.set_value(float(p.get("decoration.blur", "passes", "1")))
        self.blur_vibrancy_row.set_value(float(p.get("decoration.blur", "vibrancy", "0.1696")))

    def apply_changes(self):
        p = self.parser

        p.set_value("decoration", "rounding", str(int(self.rounding_row.get_value())))
        p.set_value("decoration", "rounding_power", f"{self.rounding_power_row.get_value():.1f}")
        p.set_value("decoration", "active_opacity", f"{self.active_opacity_row.get_value():.2f}")
        p.set_value("decoration", "inactive_opacity", f"{self.inactive_opacity_row.get_value():.2f}")

        p.set_value("decoration.shadow", "enabled", "true" if self.shadow_enabled_row.get_active() else "false")
        p.set_value("decoration.shadow", "range", str(int(self.shadow_range_row.get_value())))
        p.set_value("decoration.shadow", "render_power", str(int(self.shadow_render_power_row.get_value())))

        p.set_value("decoration.blur", "enabled", "true" if self.blur_enabled_row.get_active() else "false")
        p.set_value("decoration.blur", "size", str(int(self.blur_size_row.get_value())))
        p.set_value("decoration.blur", "passes", str(int(self.blur_passes_row.get_value())))
        p.set_value("decoration.blur", "vibrancy", f"{self.blur_vibrancy_row.get_value():.4f}")
