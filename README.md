# neo & neon

> **A modern, unified package management suite for Gentoo Linux.**

`neo` seamlessly combines Gentoo Portage (`emerge`), Flatpak, and Linuxbrew / Homebrew under a single fast, beautiful CLI and a responsive Qt6 desktop GUI (`neon`).

---

## Architecture Overview

```
/home/ssd/neo/
├── neo-core/           # Rust acceleration core (PyO3)
│   ├── src/
│   │   ├── lib.rs      # PyO3 bindings & high-speed search
│   │   ├── resolver.rs # Atom parsing & version comparison
│   │   ├── downloader.rs # Tokio/reqwest parallel downloader
│   │   └── cache.rs    # Local cache at ~/.cache/neo/
│   ├── Cargo.toml
│   └── pyproject.toml
├── neo-cli/            # Python CLI (Click + Rich)
│   ├── neo/
│   │   ├── cli.py      # Main CLI commands
│   │   ├── config.py   # ~/.config/neo/config.toml manager
│   │   ├── sudo_helper.py # Non-blocking sudo via pexpect
│   │   ├── utils.py    # Formatting & subprocess helpers
│   │   └── backends/   # Backend implementations
│   │       ├── base.py
│   │       ├── ebuild.py
│   │       ├── flatpak.py
│   │       ├── brew.py
│   │       ├── cask.py
│   │       └── ebins.py
│   ├── pyproject.toml
│   └── README.md
├── neon/               # Modern Qt6 desktop GUI
│   ├── neon/
│   │   ├── app.py      # Application entry point
│   │   ├── main_window.py # QMainWindow with QThread workers
│   │   ├── theme.py    # Dark theme & backend palette
│   │   └── widgets/
│   │       ├── backend_selector.py # Left sidebar with counts
│   │       ├── package_list.py     # Package table
│   │       ├── search_bar.py       # Filterable search input
│   │       └── terminal_output.py  # ANSI color terminal view
│   └── pyproject.toml
├── install.sh          # One-step automated installer
└── README.md
```

---

## Backend Aliases Reference

You can specify a backend by appending `:alias` or passing `:alias` as an argument:

| Alias | Target Package Manager | Underlying Command | Description |
|---|---|---|---|
| `:ebuild` | Gentoo Portage (Source) | `emerge` | Compiles source ebuilds with Gentoo USE flags |
| `:flatp` | Flatpak | `flatpak` | Sandboxed desktop applications from Flathub |
| `:brew` | Linuxbrew / Homebrew | `brew` | Command-line developer tools and libraries |
| `:cask` | Homebrew Cask | `brew --cask` | Precompiled GUI applications and casks |
| `:ebins` | Portage Binary Packages | `emerge --getbinpkg` | Precompiled Gentoo binary packages (binhost) |

---

## Gentoo Overlay

`project-neo` is also a full Gentoo overlay providing live ebuilds (`9999`) for all components.

### Adding the Overlay

#### With `eselect-repository` (recommended)
```bash
sudo emerge -av app-eselect/eselect-repository
sudo eselect repository add project-neo git https://github.com/kool-os/project-neo.git
sudo emerge --sync project-neo
```

#### With `layman`
```bash
sudo layman -a project-neo
```

### Installing Packages from the Overlay

```bash
# Install neo CLI (with optional Rust acceleration core)
sudo emerge -av =app-portage/neo-9999

# Install neon Qt6 GUI
sudo emerge -av =app-portage/neon-9999

# Install neo-core Rust PyO3 engine directly
sudo emerge -av =dev-python/neo-core-9999
```

---

## Installation (Local Source)

### Prerequisites
- Gentoo Linux
- Python >= 3.11
- Rust / Cargo
- `maturin`, `pip`, and `PyQt6`

### One-Step Automated Installation
Run the included installation script:
```bash
cd /home/ssd/neo
./install.sh
```

### Manual Installation

1. **Build and install the Rust core (`neo-core`)**:
   ```bash
   cd /home/ssd/neo/neo-core
   maturin build --release
   pip install --break-system-packages target/wheels/neo_core-*.whl
   ```

2. **Install the CLI (`neo-cli`)**:
   ```bash
   cd /home/ssd/neo/neo-cli
   pip install --break-system-packages -e .
   ```

3. **Install the GUI (`neon`)**:
   ```bash
   cd /home/ssd/neo/neon
   pip install --break-system-packages -e .
   ```

---

## CLI Usage (`neo`)

### 1. Search Packages
Search across all backends or target a specific backend:
```bash
# Search across all enabled backends in parallel (accelerated by Rust core)
neo search firefox

# Search specific backends
neo search firefox :flatp
neo search vim :ebuild
neo search ripgrep :brew
```

### 2. Install Packages
Flexible syntax supports `pkg:backend` or `pkg :backend`:
```bash
# Explicit backend
neo install firefox :flatp
neo install vim:ebuild
neo install wget:brew
neo install htop:ebins

# Auto-detection: searches available backends if unspecified
neo install neovim
```

### 3. Remove Packages
```bash
neo remove firefox :flatp
neo remove vim:ebuild
neo remove wget:brew
```

### 4. Update Packages
```bash
# Update all backends
neo update

# Update specific backend
neo update :ebuild
neo update :flatp
neo update :brew
```

### 5. List Installed Packages
```bash
# List all packages installed across all backends
neo list

# List packages for a single backend
neo list :ebuild
neo list :flatp
neo list :brew
```

### 6. Package Information
```bash
neo info vim :ebuild
neo info org.mozilla.firefox :flatp
```

### 7. Sync Databases
```bash
# Sync repository databases
neo sync
neo sync :ebuild
neo sync :flatp
neo sync :brew
```

### 8. Clean Caches
```bash
# Cleans ~/.cache/neo and backend download caches
neo clean
neo clean :ebuild
```

---

## Desktop GUI Usage (`neon`)

Launch the graphical interface:
```bash
neon
```

### GUI Features
- **Sidebar**: Switch between backends (`:ebuild`, `:flatp`, `:brew`, `:cask`, `:ebins`) with real-time package counts.
- **Top Bar**: Search bar with real-time filtering, plus Quick Action buttons (`Install`, `Remove`, `Update`, `Sync`, `Clean`).
- **Main Table**: Browse packages with sortable columns: `Name`, `Version`, `Description`, `Status`, `Backend`.
- **Terminal Panel**: Live ANSI-colored command output powered by background `QThread` workers.

---

## Configuration

Configuration is stored in `~/.config/neo/config.toml`:

```toml
[sudo]
method = "store" # "store" (base64 encoded) or "prompt"
password = "..." # Base64 encoded password

[backends]
default = "ebuild"
enabled = ["ebuild", "flatp", "brew", "cask", "ebins"]

[paths]
brew_prefix = "/home/linuxbrew/.linuxbrew"
cache_dir = "~/.cache/neo"
```

To update your sudo preferences or switch the default backend, edit `~/.config/neo/config.toml` or set them via Python API `neo.config`.
