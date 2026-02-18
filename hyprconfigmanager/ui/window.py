"""
Main application window with sidebar navigation, undo/redo support, and robust error handling.
"""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GLib, Gdk
from pathlib import Path

from hypr_parser import HyprParser, DEFAULT_CONFIG_PATH
from ui.undo_manager import UndoManager
from ui.general_page import GeneralPage
from ui.decoration_page import DecorationPage
from ui.input_page import InputPage
from ui.keybinds_page import KeybindsPage
from ui.autostart_page import AutostartPage
from ui.monitor_page import MonitorPage
from ui.variables_page import VariablesPage
from ui.animations_page import AnimationsPage
from ui.gestures_page import GesturesPage


class HyprConfigWindow(Adw.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.parser = HyprParser()
        self.undo_manager = UndoManager()
        self._load_error = None
        self._load_error_type = None

        self.set_title("Hyprland Config Manager")
        self.set_default_size(1100, 750)
        self.set_size_request(860, 560)

        self._try_load_config()
        self._build_ui()
        self._setup_shortcuts()

    # ── Config loading ────────────────────────────────────────────────────────

    def _try_load_config(self):
        """Attempt to load the config, capturing any error."""
        try:
            self.parser.load()
            self._load_error = None
            self._load_error_type = None
        except FileNotFoundError as e:
            self._load_error = str(e)
            self._load_error_type = "missing"
        except PermissionError as e:
            self._load_error = str(e)
            self._load_error_type = "permission"
        except (ValueError, IsADirectoryError) as e:
            self._load_error = str(e)
            self._load_error_type = "invalid"
        except Exception as e:
            self._load_error = f"Unexpected error: {e}"
            self._load_error_type = "unknown"

    # ── Keyboard shortcuts ────────────────────────────────────────────────────

    def _setup_shortcuts(self):
        """Wire Ctrl+Z / Ctrl+Y for undo/redo."""
        key_ctrl = Gtk.EventControllerKey()
        key_ctrl.connect("key-pressed", self._on_key_pressed)
        self.add_controller(key_ctrl)

    def _on_key_pressed(self, ctrl, keyval, keycode, state):
        ctrl_held = bool(state & Gdk.ModifierType.CONTROL_MASK)
        shift_held = bool(state & Gdk.ModifierType.SHIFT_MASK)

        if ctrl_held and keyval == ord('z') and not shift_held:
            self._do_undo()
            return True
        if ctrl_held and (keyval == ord('y') or (keyval == ord('z') and shift_held)):
            self._do_redo()
            return True
        return False

    def _do_undo(self):
        desc = self.undo_manager.undo()
        if desc:
            self._show_toast(f"↩ Undone: {desc}")
        self._update_undo_buttons()

    def _do_redo(self):
        desc = self.undo_manager.redo()
        if desc:
            self._show_toast(f"↪ Redone: {desc}")
        self._update_undo_buttons()

    def _update_undo_buttons(self):
        self.undo_btn.set_sensitive(self.undo_manager.can_undo)
        self.redo_btn.set_sensitive(self.undo_manager.can_redo)
        self.undo_btn.set_tooltip_text(
            f"Undo: {self.undo_manager.undo_description} (Ctrl+Z)"
            if self.undo_manager.can_undo else "Nothing to undo (Ctrl+Z)"
        )
        self.redo_btn.set_tooltip_text(
            f"Redo: {self.undo_manager.redo_description} (Ctrl+Y)"
            if self.undo_manager.can_redo else "Nothing to redo (Ctrl+Y)"
        )

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        outer_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(outer_box)

        # ── Header bar ───────────────────────────────────────────────────────
        header = Adw.HeaderBar()
        header.add_css_class("flat")

        config_path_str = str(DEFAULT_CONFIG_PATH)
        title_widget = Adw.WindowTitle(
            title="Hyprland Config Manager",
            subtitle=config_path_str,
        )
        header.set_title_widget(title_widget)

        # Apply & Reload button (right side)
        self.apply_btn = Gtk.Button(label="Apply & Reload")
        self.apply_btn.add_css_class("suggested-action")
        self.apply_btn.add_css_class("pill")
        self.apply_btn.set_tooltip_text(
            "Save all changes to hyprland.conf and ask Hyprland to reload.\n"
            "A backup is created automatically before saving."
        )
        self.apply_btn.connect("clicked", self._on_apply)
        header.pack_end(self.apply_btn)

        # Undo / Redo (left side, linked pair)
        undo_redo_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        undo_redo_box.add_css_class("linked")

        self.undo_btn = Gtk.Button()
        self.undo_btn.set_icon_name("edit-undo-symbolic")
        self.undo_btn.set_tooltip_text("Nothing to undo (Ctrl+Z)")
        self.undo_btn.set_sensitive(False)
        self.undo_btn.connect("clicked", lambda _: self._do_undo())
        undo_redo_box.append(self.undo_btn)

        self.redo_btn = Gtk.Button()
        self.redo_btn.set_icon_name("edit-redo-symbolic")
        self.redo_btn.set_tooltip_text("Nothing to redo (Ctrl+Y)")
        self.redo_btn.set_sensitive(False)
        self.redo_btn.connect("clicked", lambda _: self._do_redo())
        undo_redo_box.append(self.redo_btn)

        header.pack_start(undo_redo_box)

        # Reload from disk button
        reload_btn = Gtk.Button()
        reload_btn.set_icon_name("view-refresh-symbolic")
        reload_btn.set_tooltip_text("Reload config from disk — discards any unsaved changes")
        reload_btn.connect("clicked", self._on_reload_from_disk)
        header.pack_start(reload_btn)

        outer_box.append(header)

        # Wire undo manager → update buttons whenever stack changes
        self.undo_manager.connect_changed(self._update_undo_buttons)

        # ── Toast overlay ────────────────────────────────────────────────────
        self.toast_overlay = Adw.ToastOverlay()
        outer_box.append(self.toast_overlay)
        self.toast_overlay.set_vexpand(True)

        # ── Error state: show a friendly dialog instead of blank UI ──────────
        if self._load_error:
            self._build_error_ui()
            return

        # ── Normal UI ────────────────────────────────────────────────────────
        self._build_main_ui()

    def _build_error_ui(self):
        """Show a friendly error page when the config can't be loaded."""
        error_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        error_box.set_valign(Gtk.Align.CENTER)
        error_box.set_halign(Gtk.Align.CENTER)
        error_box.set_margin_top(48)
        error_box.set_margin_bottom(48)
        error_box.set_margin_start(48)
        error_box.set_margin_end(48)
        self.toast_overlay.set_child(error_box)

        # Icon
        icon = Gtk.Image.new_from_icon_name("dialog-warning-symbolic")
        icon.set_pixel_size(64)
        icon.add_css_class("dim-label")
        error_box.append(icon)

        # Title
        title = Gtk.Label()
        title.add_css_class("title-2")
        if self._load_error_type == "missing":
            title.set_label("Config File Not Found")
        elif self._load_error_type == "permission":
            title.set_label("Permission Denied")
        elif self._load_error_type == "invalid":
            title.set_label("Config File Invalid")
        else:
            title.set_label("Could Not Load Config")
        error_box.append(title)

        # Description
        desc = Gtk.Label()
        desc.set_wrap(True)
        desc.set_max_width_chars(60)
        desc.set_justify(Gtk.Justification.CENTER)
        desc.add_css_class("dim-label")
        # Show a clean, friendly message
        first_line = self._load_error.split("\n")[0]
        desc.set_label(first_line)
        error_box.append(desc)

        # Path info
        path_label = Gtk.Label()
        path_label.set_markup(
            f'<span font_family="monospace" size="small">{DEFAULT_CONFIG_PATH}</span>'
        )
        path_label.add_css_class("dim-label")
        error_box.append(path_label)

        # Action buttons
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        btn_box.set_halign(Gtk.Align.CENTER)
        error_box.append(btn_box)

        if self._load_error_type == "missing":
            create_btn = Gtk.Button(label="Create Default Config")
            create_btn.add_css_class("suggested-action")
            create_btn.add_css_class("pill")
            create_btn.set_tooltip_text(
                f"Creates a minimal hyprland.conf at:\n{DEFAULT_CONFIG_PATH}"
            )
            create_btn.connect("clicked", self._on_create_default_config)
            btn_box.append(create_btn)

        retry_btn = Gtk.Button(label="Retry")
        retry_btn.add_css_class("pill")
        retry_btn.set_tooltip_text("Try loading the config file again")
        retry_btn.connect("clicked", self._on_retry_load)
        btn_box.append(retry_btn)

        # Detail expander
        if "\n" in self._load_error:
            detail_expander = Gtk.Expander(label="Technical Details")
            detail_expander.set_margin_top(8)
            detail_label = Gtk.Label(label=self._load_error)
            detail_label.add_css_class("monospace")
            detail_label.add_css_class("dim-label")
            detail_label.set_wrap(True)
            detail_label.set_xalign(0)
            detail_expander.set_child(detail_label)
            error_box.append(detail_expander)

    def _on_create_default_config(self, btn):
        """Create a default config and reload the UI."""
        try:
            self.parser.create_default_config()
            self._load_error = None
            self._load_error_type = None
            # Rebuild the full UI
            child = self.toast_overlay.get_child()
            if child:
                self.toast_overlay.set_child(None)
            self._build_main_ui()
            self._show_toast("Default config created! ✓")
        except Exception as e:
            self._show_toast(f"Failed to create config: {e}", timeout=6)

    def _on_retry_load(self, btn):
        """Retry loading the config."""
        self._try_load_config()
        if not self._load_error:
            child = self.toast_overlay.get_child()
            if child:
                self.toast_overlay.set_child(None)
            self._build_main_ui()
            self._show_toast("Config loaded successfully ✓")
        else:
            self._show_toast(f"Still failing: {self._load_error.split(chr(10))[0]}", timeout=5)

    def _build_main_ui(self):
        """Build the normal navigation UI (called after config loads successfully)."""
        # ── Navigation split view ────────────────────────────────────────────
        split_view = Adw.NavigationSplitView()
        split_view.set_min_sidebar_width(210)
        split_view.set_max_sidebar_width(250)
        self.toast_overlay.set_child(split_view)

        # Sidebar
        sidebar_nav = Adw.NavigationPage(title="Sections")
        sidebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sidebar_nav.set_child(sidebar_box)
        split_view.set_sidebar(sidebar_nav)

        sidebar_header = Adw.HeaderBar()
        sidebar_header.add_css_class("flat")
        sidebar_header.set_show_end_title_buttons(False)
        sidebar_box.append(sidebar_header)

        # Sidebar list
        self.sidebar_list = Gtk.ListBox()
        self.sidebar_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.sidebar_list.add_css_class("navigation-sidebar")
        self.sidebar_list.connect("row-selected", self._on_sidebar_selected)

        sidebar_scroll = Gtk.ScrolledWindow()
        sidebar_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        sidebar_scroll.set_vexpand(True)
        sidebar_scroll.set_child(self.sidebar_list)
        sidebar_box.append(sidebar_scroll)

        # Content area
        self.content_nav = Adw.NavigationPage(title="Config")
        split_view.set_content(self.content_nav)

        self.content_stack = Gtk.Stack()
        self.content_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.content_nav.set_child(self.content_stack)

        # ── Pages — organized logically ──────────────────────────────────────
        self.pages = {}

        # ── System & Startup ─────────────────────────────────────────────────
        self._add_sidebar_header("System &amp; Startup")
        self._add_page("monitors",  "Monitors",        "video-display-symbolic",      MonitorPage)
        self._add_page("autostart", "Autostart Apps",  "system-run-symbolic",         AutostartPage)
        self._add_page("variables", "Variables",       "text-x-script-symbolic",      VariablesPage)

        # ── Appearance ───────────────────────────────────────────────────────
        self._add_sidebar_header("Appearance")
        self._add_page("general",    "General",        "preferences-system-symbolic", GeneralPage)
        self._add_page("decoration", "Decoration",     "applications-graphics-symbolic", DecorationPage)
        self._add_page("animations", "Animations",     "media-playback-start-symbolic", AnimationsPage)

        # ── Input ────────────────────────────────────────────────────────────
        self._add_sidebar_header("Input")
        self._add_page("input",    "Keyboard &amp; Mouse", "input-keyboard-symbolic",     InputPage)
        self._add_page("gestures", "Gestures",         "input-touchpad-symbolic",     GesturesPage)
        self._add_page("keybinds", "Keybindings",      "input-gaming-symbolic",       KeybindsPage)

        # Select first real page (index 1 = Monitors, index 0 = header)
        self.sidebar_list.select_row(self.sidebar_list.get_row_at_index(1))

    def _add_sidebar_header(self, title: str):
        """Add a non-selectable section header to the sidebar."""
        label = Gtk.Label()
        label.set_markup(f"<b>{title}</b>")
        label.add_css_class("heading")
        label.set_margin_top(14)
        label.set_margin_bottom(4)
        label.set_margin_start(12)
        label.set_xalign(0)

        row = Gtk.ListBoxRow()
        row.set_child(label)
        row.set_activatable(False)
        row.set_selectable(False)
        row._is_header = True
        self.sidebar_list.append(row)

    def _add_page(self, page_id: str, label: str, icon: str, page_class):
        """Add a sidebar entry and corresponding stack page."""
        row = Adw.ActionRow()
        row.set_title(label)
        row.add_prefix(Gtk.Image.new_from_icon_name(icon))
        row.set_activatable(True)
        row._page_id = page_id
        row._is_header = False
        self.sidebar_list.append(row)

        # Pass undo_manager to pages that accept it
        try:
            page = page_class(self.parser, self.undo_manager)
        except TypeError:
            page = page_class(self.parser)

        self.content_stack.add_named(page, page_id)
        self.pages[page_id] = page

    def _on_sidebar_selected(self, listbox, row):
        if row is None or getattr(row, "_is_header", False):
            return
        page_id = getattr(row, "_page_id", None)
        if page_id:
            self.content_stack.set_visible_child_name(page_id)

    # ── Actions ───────────────────────────────────────────────────────────────

    def _on_apply(self, btn):
        """Collect all changes, write config, reload Hyprland."""
        try:
            for page in self.pages.values():
                if hasattr(page, "apply_changes"):
                    page.apply_changes()

            self.parser.save(backup=True)
            ok, msg = self.parser.reload_hyprland()

            if ok:
                self._show_toast("Config saved and Hyprland reloaded ✓")
            else:
                self._show_toast(f"Saved — but reload failed: {msg}", timeout=6)

        except PermissionError as e:
            self._show_error_dialog(
                "Permission Denied",
                f"Cannot write to config file:\n{e}\n\n"
                "Try: chmod 644 ~/.config/hypr/hyprland.conf"
            )
        except Exception as e:
            self._show_error_dialog("Save Failed", str(e))

    def _on_reload_from_disk(self, btn):
        """Reload config from disk and refresh all pages."""
        self._try_load_config()
        if self._load_error:
            self._show_toast(
                f"Reload failed: {self._load_error.split(chr(10))[0]}", timeout=5
            )
            return
        if hasattr(self, "pages"):
            for page in self.pages.values():
                if hasattr(page, "refresh"):
                    page.refresh()
        self._show_toast("Config reloaded from disk")

    def _show_toast(self, message: str, timeout: int = 3):
        toast = Adw.Toast()
        toast.set_title(message)
        toast.set_timeout(timeout)
        self.toast_overlay.add_toast(toast)

    def _show_error_dialog(self, title: str, message: str):
        """Show a modal error dialog."""
        dialog = Adw.AlertDialog()
        dialog.set_heading(title)
        dialog.set_body(message)
        dialog.add_response("ok", "OK")
        dialog.set_default_response("ok")
        dialog.present(self)
