# Hyprland Config Manager

> A native GTK4 + Libadwaita GUI for editing your Hyprland compositor configuration — no text editing required.

![screenshot](https://raw.githubusercontent.com/your-repo/hyprconfigmanager/main/screenshot.png)

---

## ✨ Features

| Section | What you can do |
|---|---|
| 🖥️ **Monitors** | Add/edit/remove monitor configs (resolution, refresh rate, position, scale) |
| 🚀 **Autostart** | Manage `exec-once` programs that launch at login |
| 📦 **Variables** | Define `$variables` (e.g. `$terminal = kitty`) — used everywhere else |
| 🎨 **Layout & Gaps** | Window gaps, border size, tiling layout (dwindle/master) |
| 💎 **Decoration** | Corner rounding, opacity, drop shadows, blur/glass effects |
| 🎬 **Animations** | Enable/disable animations, bezier curves, animation speeds |
| ⌨️ **Keyboard & Mouse** | Layouts, language switching, mouse sensitivity, natural scroll |
| 👆 **Gestures** | Touchpad workspace swipe gestures |
| 🎮 **Keybindings** | Full keybind editor with 70+ dispatchers and live descriptions |

### Extra goodies
- **Variable resolution** — `$terminal` shows as `kitty` in all lists
- **Undo / Redo** — Ctrl+Z / Ctrl+Y, with buttons in the toolbar
- **Auto-backup** — timestamped `.bak` file before every save
- **Apply & Reload** — writes config and runs `hyprctl reload` instantly
- **Create default config** — if no config exists, generate a sensible starter

---

## 📦 Requirements

- Python 3.10+
- GTK4 + Libadwaita

**Arch Linux:**
```bash
sudo pacman -S python-gobject gtk4 libadwaita
```

**Ubuntu / Debian:**
```bash
sudo apt install python3-gi gir1.2-gtk-4.0 gir1.2-adw-1
```

**Fedora:**
```bash
sudo dnf install python3-gobject gtk4 libadwaita
```

---

## 🚀 Running

```bash
cd ~/hyprconfigmanager
python3 main.py
```

> **First time?** If you don't have a `~/.config/hypr/hyprland.conf` yet, the app will offer to create a default one for you.

---

## 🖥️ Install as Desktop App

```bash
cp hyprland-config-manager.desktop ~/.local/share/applications/
```

Then search for "Hyprland Config Manager" in your app launcher.

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl+Z` | Undo last change |
| `Ctrl+Y` | Redo |

---

## 🗂️ File Structure

```
hyprconfigmanager/
├── main.py              # Entry point
├── hypr_parser.py       # Config file reader/writer
└── ui/
    ├── window.py        # Main window & navigation
    ├── undo_manager.py  # Undo/redo stack
    ├── general_page.py  # Layout & gaps
    ├── decoration_page.py
    ├── input_page.py
    ├── keybinds_page.py
    ├── autostart_page.py
    ├── monitor_page.py
    ├── variables_page.py
    ├── animations_page.py
    └── gestures_page.py
```

---

## 🔧 Troubleshooting

**"Config file not found"**
The app will offer to create a default config. Click **"Create Default Config"**.

**"Permission denied"**
```bash
chmod 644 ~/.config/hypr/hyprland.conf
```

**Hyprland doesn't reload after Apply**
Make sure `hyprctl` is in your PATH:
```bash
which hyprctl
```

**App crashes on launch**
Check you have all dependencies installed (see Requirements above).
