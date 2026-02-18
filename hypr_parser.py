"""
Hyprland config file parser.
Reads and writes ~/.config/hypr/hyprland.conf preserving comments and structure.
"""

import os
import re
import shutil
from datetime import datetime
from pathlib import Path


DEFAULT_CONFIG_PATH = Path.home() / ".config" / "hypr" / "hyprland.conf"


class HyprParser:
    """
    Parses Hyprland config files.
    Supports nested sections, key=value pairs, bind lines, exec-once lines.
    Preserves comments and whitespace on write.
    """

    def __init__(self, config_path: Path = DEFAULT_CONFIG_PATH):
        self.config_path = config_path
        self.lines: list[str] = []
        self._data: dict = {}  # section -> {key: value}
        self._binds: list[dict] = []  # list of bind dicts
        self._exec_once: list[str] = []  # list of exec-once commands
        self._variables: dict[str, str] = {}  # $VAR -> value
        self._monitors: list[str] = []  # raw monitor= lines
        self._gestures: list[dict] = []  # gesture= lines
        self._animations: list[dict] = []  # animation= lines
        self._beziers: list[dict] = []  # bezier= lines

    def load(self):
        """Load and parse the config file. Raises descriptive errors on failure."""
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Config file not found: {self.config_path}\n"
                f"Expected location: {self.config_path}\n"
                "You can create a default config from the app."
            )
        if not self.config_path.is_file():
            raise IsADirectoryError(
                f"Config path is a directory, not a file: {self.config_path}"
            )
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.lines = f.readlines()
        except PermissionError:
            raise PermissionError(
                f"No permission to read: {self.config_path}\n"
                "Try: chmod 644 ~/.config/hypr/hyprland.conf"
            )
        except UnicodeDecodeError:
            raise ValueError(
                f"Config file is not valid UTF-8: {self.config_path}\n"
                "Try opening it in a text editor and re-saving as UTF-8."
            )
        self._parse()

    def create_default_config(self):
        """Create a minimal default hyprland.conf at the configured path."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        default = """# Hyprland config — created by Hyprland Config Manager

# Variables
$terminal = kitty
$browser = firefox
$filemanager = nautilus

# Autostart
exec-once = waybar
exec-once = hyprpaper

# Monitor (auto-detect)
monitor = ,preferred,auto,1

general {
    gaps_in = 5
    gaps_out = 20
    border_size = 2
    layout = dwindle
}

decoration {
    rounding = 10
    active_opacity = 1.0
    inactive_opacity = 1.0

    shadow {
        enabled = true
        range = 4
        render_power = 3
    }

    blur {
        enabled = true
        size = 3
        passes = 1
    }
}

animations {
    enabled = true
    bezier = myBezier, 0.05, 0.9, 0.1, 1.05
    animation = windows, 1, 7, myBezier
    animation = windowsOut, 1, 7, default, popin 80%
    animation = fade, 1, 7, default
    animation = workspaces, 1, 6, default
}

dwindle {
    pseudotile = false
    preserve_split = true
}

input {
    kb_layout = us
    sensitivity = 0
    follow_mouse = 1

    touchpad {
        natural_scroll = false
    }
}

# Keybindings
bind = SUPER, Return, exec, $terminal
bind = SUPER, Q, killactive
bind = SUPER, M, exit
bind = SUPER, E, exec, $filemanager
bind = SUPER, V, togglefloating
bind = SUPER, R, exec, wofi --show drun
bind = SUPER, P, pseudo
bind = SUPER, J, togglesplit
bind = SUPER, left, movefocus, l
bind = SUPER, right, movefocus, r
bind = SUPER, up, movefocus, u
bind = SUPER, down, movefocus, d
bind = SUPER, 1, workspace, 1
bind = SUPER, 2, workspace, 2
bind = SUPER, 3, workspace, 3
bind = SUPER, 4, workspace, 4
bind = SUPER, 5, workspace, 5
bind = SUPER SHIFT, 1, movetoworkspace, 1
bind = SUPER SHIFT, 2, movetoworkspace, 2
bind = SUPER SHIFT, 3, movetoworkspace, 3
bind = SUPER SHIFT, 4, movetoworkspace, 4
bind = SUPER SHIFT, 5, movetoworkspace, 5
bindm = SUPER, mouse:272, movewindow
bindm = SUPER, mouse:273, resizewindow
"""
        with open(self.config_path, "w", encoding="utf-8") as f:
            f.write(default)
        self.load()


    def _parse(self):
        """Parse lines into structured data."""
        self._data = {}
        self._binds = []
        self._exec_once = []
        self._variables = {}
        self._monitors = []
        self._gestures = []
        self._animations = []
        self._beziers = []

        section_stack = []

        for line in self.lines:
            stripped = line.strip()

            # Skip comments and empty lines
            if not stripped or stripped.startswith("#"):
                continue

            # Section open
            if stripped.endswith("{"):
                section_name = stripped[:-1].strip()
                section_stack.append(section_name)
                current = self._data
                for s in section_stack:
                    if s not in current:
                        current[s] = {}
                    current = current[s]
                continue

            # Section close
            if stripped == "}":
                if section_stack:
                    section_stack.pop()
                continue

            # Variable definition: $VAR = value
            var_match = re.match(r'^\$(\w+)\s*=\s*(.*)$', stripped)
            if var_match:
                self._variables[f"${var_match.group(1)}"] = var_match.group(2).strip()
                continue

            # monitor= lines (top-level)
            monitor_match = re.match(r'^monitor\s*=\s*(.*)$', stripped)
            if monitor_match and not section_stack:
                self._monitors.append(monitor_match.group(1).strip())
                continue

            # gesture= lines (top-level)
            gesture_match = re.match(r'^gesture\s*=\s*(.*)$', stripped)
            if gesture_match and not section_stack:
                parts = [p.strip() for p in gesture_match.group(1).split(",")]
                self._gestures.append({
                    "fingers": parts[0] if len(parts) > 0 else "",
                    "direction": parts[1] if len(parts) > 1 else "",
                    "action": parts[2] if len(parts) > 2 else "",
                    "params": parts[3] if len(parts) > 3 else "",
                })
                continue

            # bind / bindel / bindl / bindm lines (top-level)
            bind_match = re.match(r'^(bind[elm]?)\s*=\s*(.*)$', stripped)
            if bind_match and not section_stack:
                bind_type = bind_match.group(1)
                rest = bind_match.group(2)
                parts = [p.strip() for p in rest.split(",", 3)]
                bind_dict = {
                    "type": bind_type,
                    "mod": parts[0] if len(parts) > 0 else "",
                    "key": parts[1] if len(parts) > 1 else "",
                    "dispatcher": parts[2] if len(parts) > 2 else "",
                    "params": parts[3] if len(parts) > 3 else "",
                }
                self._binds.append(bind_dict)
                continue

            # exec-once lines
            exec_match = re.match(r'^exec-once\s*=\s*(.*)$', stripped)
            if exec_match and not section_stack:
                self._exec_once.append(exec_match.group(1).strip())
                continue

            # animation= lines inside animations section
            if section_stack == ["animations"]:
                anim_match = re.match(r'^animation\s*=\s*(.*)$', stripped)
                if anim_match:
                    parts = [p.strip() for p in anim_match.group(1).split(",")]
                    self._animations.append({
                        "name": parts[0] if len(parts) > 0 else "",
                        "onoff": parts[1] if len(parts) > 1 else "1",
                        "speed": parts[2] if len(parts) > 2 else "1",
                        "curve": parts[3] if len(parts) > 3 else "default",
                        "style": parts[4] if len(parts) > 4 else "",
                    })
                    continue
                bezier_match = re.match(r'^bezier\s*=\s*(.*)$', stripped)
                if bezier_match:
                    parts = [p.strip() for p in bezier_match.group(1).split(",")]
                    self._beziers.append({
                        "name": parts[0] if len(parts) > 0 else "",
                        "x0": parts[1] if len(parts) > 1 else "0",
                        "y0": parts[2] if len(parts) > 2 else "0",
                        "x1": parts[3] if len(parts) > 3 else "1",
                        "y1": parts[4] if len(parts) > 4 else "1",
                    })
                    continue

            # Key = value inside a section
            kv_match = re.match(r'^([^=]+?)\s*=\s*(.*)$', stripped)
            if kv_match and section_stack:
                key = kv_match.group(1).strip()
                value = kv_match.group(2).strip()
                if "#" in value:
                    value = value[:value.index("#")].strip()
                current = self._data
                for s in section_stack:
                    if s not in current:
                        current[s] = {}
                    current = current[s]
                current[key] = value
                continue

            # Top-level key = value (not in a section)
            kv_match = re.match(r'^([^=]+?)\s*=\s*(.*)$', stripped)
            if kv_match and not section_stack:
                key = kv_match.group(1).strip()
                value = kv_match.group(2).strip()
                if "#" in value:
                    value = value[:value.index("#")].strip()
                if "__top__" not in self._data:
                    self._data["__top__"] = {}
                self._data["__top__"][key] = value

    def get(self, section: str, key: str, default="") -> str:
        """Get a value from a section. Use '.' for nested sections."""
        parts = section.split(".")
        current = self._data
        for p in parts:
            if p not in current:
                return default
            current = current[p]
        if isinstance(current, dict):
            return current.get(key, default)
        return default

    def get_top(self, key: str, default="") -> str:
        """Get a top-level key=value."""
        return self._data.get("__top__", {}).get(key, default)

    def get_binds(self) -> list[dict]:
        return list(self._binds)

    def get_exec_once(self) -> list[str]:
        return list(self._exec_once)

    def get_variables(self) -> dict[str, str]:
        return dict(self._variables)

    def get_monitors(self) -> list[str]:
        return list(self._monitors)

    def get_gestures(self) -> list[dict]:
        return list(self._gestures)

    def get_animations(self) -> list[dict]:
        return list(self._animations)

    def get_beziers(self) -> list[dict]:
        return list(self._beziers)

    def resolve(self, text: str) -> str:
        """Replace all $VAR references in text with their actual values."""
        if not text or "$" not in text:
            return text
        # Sort by length descending so longer names are replaced first
        for var, val in sorted(self._variables.items(), key=lambda x: -len(x[0])):
            text = text.replace(var, val)
        return text

    # ─── Write helpers ────────────────────────────────────────────────────────

    def set_value(self, section: str, key: str, value: str):
        """
        Update a key=value inside a section in self.lines.
        section: dot-separated path, e.g. 'general' or 'decoration.blur'
        """
        section_parts = section.split(".")
        new_lines = []
        section_depth = []
        found = False

        i = 0
        while i < len(self.lines):
            line = self.lines[i]
            stripped = line.strip()

            # Track section open
            if stripped.endswith("{") and not stripped.startswith("#"):
                sec_name = stripped[:-1].strip()
                section_depth.append(sec_name)

            # Track section close
            elif stripped == "}":
                if section_depth:
                    section_depth.pop()

            # Check if we're in the right section and this is the key
            elif not found and section_depth == section_parts:
                kv_match = re.match(r'^(\s*)([^=\s#][^=]*?)\s*=\s*(.*)$', line)
                if kv_match:
                    line_key = kv_match.group(2).strip()
                    if line_key == key:
                        indent = kv_match.group(1)
                        # Preserve inline comment if any
                        rest = kv_match.group(3)
                        comment = ""
                        if "#" in rest:
                            comment = " " + rest[rest.index("#"):]
                        new_lines.append(f"{indent}{key} = {value}{comment}\n")
                        found = True
                        i += 1
                        continue

            new_lines.append(line)
            i += 1

        if found:
            self.lines = new_lines
        else:
            # Key not found — insert before the closing brace of the section
            self._insert_in_section(section_parts, key, value)

    def _insert_in_section(self, section_parts: list[str], key: str, value: str):
        """Insert a new key=value before the closing brace of a section."""
        new_lines = []
        section_depth = []
        inserted = False

        for line in self.lines:
            stripped = line.strip()

            if stripped.endswith("{") and not stripped.startswith("#"):
                sec_name = stripped[:-1].strip()
                section_depth.append(sec_name)

            elif stripped == "}":
                if not inserted and section_depth == section_parts:
                    indent = "    "
                    new_lines.append(f"{indent}{key} = {value}\n")
                    inserted = True
                if section_depth:
                    section_depth.pop()

            new_lines.append(line)

        self.lines = new_lines

    def set_binds(self, binds: list[dict]):
        """Replace all bind lines with new list."""
        self._binds = binds
        # Remove all existing bind lines
        new_lines = []
        for line in self.lines:
            stripped = line.strip()
            if re.match(r'^bind[elm]?\s*=', stripped) and not stripped.startswith("#"):
                continue
            new_lines.append(line)

        # Find insertion point (after last keybinding comment block or at end)
        insert_idx = len(new_lines)
        for i, line in enumerate(new_lines):
            if "KEYBINDINGS" in line or "keybind" in line.lower():
                insert_idx = i + 1

        bind_lines = []
        for b in binds:
            mod = b.get("mod", "")
            key = b.get("key", "")
            dispatcher = b.get("dispatcher", "")
            params = b.get("params", "").strip().rstrip(",").strip()
            btype = b.get("type", "bind")
            if params:
                bind_lines.append(f"{btype} = {mod}, {key}, {dispatcher}, {params}\n")
            else:
                bind_lines.append(f"{btype} = {mod}, {key}, {dispatcher}\n")

        self.lines = new_lines[:insert_idx] + bind_lines + new_lines[insert_idx:]

    def set_exec_once(self, commands: list[str]):
        """Replace all exec-once lines with new list."""
        self._exec_once = commands
        new_lines = []
        for line in self.lines:
            stripped = line.strip()
            if re.match(r'^exec-once\s*=', stripped) and not stripped.startswith("#"):
                continue
            new_lines.append(line)

        # Find insertion point
        insert_idx = len(new_lines)
        for i, line in enumerate(new_lines):
            if "AUTOSTART" in line:
                insert_idx = i + 1

        exec_lines = [f"exec-once = {cmd}\n" for cmd in commands]
        self.lines = new_lines[:insert_idx] + exec_lines + new_lines[insert_idx:]

    def set_input_kb_layout(self, layouts: list[str]):
        """Set kb_layout in the input section."""
        layout_str = ", ".join(layouts)
        self.set_value("input", "kb_layout", layout_str)

    def set_input_kb_options(self, options: str):
        """Set kb_options in the input section."""
        self.set_value("input", "kb_options", options)

    def set_monitors(self, monitors: list[str]):
        """Replace all monitor= lines."""
        self._monitors = monitors
        new_lines = []
        for line in self.lines:
            stripped = line.strip()
            if re.match(r'^monitor\s*=', stripped) and not stripped.startswith("#"):
                continue
            new_lines.append(line)
        insert_idx = 0
        for i, line in enumerate(new_lines):
            if "MONITOR" in line.upper():
                insert_idx = i + 1
                break
        mon_lines = [f"monitor={m}\n" for m in monitors]
        self.lines = new_lines[:insert_idx] + mon_lines + new_lines[insert_idx:]

    def set_variables(self, variables: dict[str, str]):
        """Replace all $VAR = value lines."""
        self._variables = variables
        new_lines = []
        for line in self.lines:
            stripped = line.strip()
            if re.match(r'^\$\w+\s*=', stripped) and not stripped.startswith("#"):
                continue
            new_lines.append(line)
        # Insert at top (after any initial comments)
        insert_idx = 0
        for i, line in enumerate(new_lines):
            s = line.strip()
            if s and not s.startswith("#") and not s.startswith("autogenerated"):
                insert_idx = i
                break
        var_lines = [f"${k} = {v}\n" for k, v in variables.items()]
        self.lines = new_lines[:insert_idx] + var_lines + new_lines[insert_idx:]

    def set_gestures(self, gestures: list[dict]):
        """Replace all gesture= lines."""
        self._gestures = gestures
        new_lines = []
        for line in self.lines:
            stripped = line.strip()
            if re.match(r'^gesture\s*=', stripped) and not stripped.startswith("#"):
                continue
            new_lines.append(line)
        insert_idx = len(new_lines)
        for i, line in enumerate(new_lines):
            if "gesture" in line.lower() or "GESTURE" in line:
                insert_idx = i + 1
        gest_lines = []
        for g in gestures:
            fingers = g.get("fingers", "3")
            direction = g.get("direction", "horizontal")
            action = g.get("action", "workspace")
            params = g.get("params", "")
            if params:
                gest_lines.append(f"gesture = {fingers}, {direction}, {action}, {params}\n")
            else:
                gest_lines.append(f"gesture = {fingers}, {direction}, {action}\n")
        self.lines = new_lines[:insert_idx] + gest_lines + new_lines[insert_idx:]

    def set_animations(self, animations: list[dict], beziers: list[dict]):
        """Replace animation= and bezier= lines inside animations { } block."""
        self._animations = animations
        self._beziers = beziers
        # Remove existing animation/bezier lines inside animations block
        new_lines = []
        in_animations = False
        section_depth = 0
        for line in self.lines:
            stripped = line.strip()
            if stripped == "animations {":
                in_animations = True
                section_depth = 1
                new_lines.append(line)
                # Insert bezier lines
                for b in beziers:
                    name = b.get("name", "")
                    x0 = b.get("x0", "0")
                    y0 = b.get("y0", "0")
                    x1 = b.get("x1", "1")
                    y1 = b.get("y1", "1")
                    new_lines.append(f"    bezier = {name}, {x0}, {y0}, {x1}, {y1}\n")
                # Insert animation lines
                for a in animations:
                    name = a.get("name", "")
                    onoff = a.get("onoff", "1")
                    speed = a.get("speed", "1")
                    curve = a.get("curve", "default")
                    style = a.get("style", "")
                    if style:
                        new_lines.append(f"    animation = {name}, {onoff}, {speed}, {curve}, {style}\n")
                    else:
                        new_lines.append(f"    animation = {name}, {onoff}, {speed}, {curve}\n")
                continue
            if in_animations:
                if stripped.endswith("{"):
                    section_depth += 1
                if stripped == "}":
                    section_depth -= 1
                    if section_depth == 0:
                        in_animations = False
                        new_lines.append(line)
                        continue
                # Skip old animation/bezier lines
                if re.match(r'^(animation|bezier)\s*=', stripped):
                    continue
            new_lines.append(line)
        self.lines = new_lines

    def save(self, backup: bool = True):
        """Write lines back to the config file, optionally creating a backup."""
        if backup and self.config_path.exists():
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.config_path.with_suffix(f".conf.bak.{ts}")
            shutil.copy2(self.config_path, backup_path)

        with open(self.config_path, "w", encoding="utf-8") as f:
            f.writelines(self.lines)

    def reload_hyprland(self) -> tuple[bool, str]:
        """Run hyprctl reload and return (success, message)."""
        import subprocess
        try:
            result = subprocess.run(
                ["hyprctl", "reload"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                return True, "Hyprland reloaded successfully"
            else:
                return False, result.stderr or "hyprctl reload failed"
        except FileNotFoundError:
            return False, "hyprctl not found"
        except subprocess.TimeoutExpired:
            return False, "hyprctl reload timed out"
        except Exception as e:
            return False, str(e)
