# neo-cli

Unified package manager CLI for Gentoo Linux.

## Overview
`neo` bridges Portage, Flatpak, and Homebrew under a single modern command-line interface.

## Backends Supported
- `:ebuild` - Portage source packages (`emerge`)
- `:flatp` - Flatpak packages (`flatpak`)
- `:brew` - Homebrew formulae (`brew`)
- `:cask` - Homebrew GUI casks (`brew --cask`)
- `:ebins` - Portage binary packages (`emerge --getbinpkg`)

## Commands
```bash
neo install <pkg> [:<backend>]
neo remove <pkg> [:<backend>]
neo search <pkg> [:<backend>]
neo update [:<backend>]
neo list [:<backend>]
neo info <pkg> [:<backend>]
neo sync [:<backend>]
neo clean [:<backend>]
```
