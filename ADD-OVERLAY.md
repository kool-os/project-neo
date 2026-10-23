# Adding the project-neo overlay

## Using eselect-repository (recommended)
```bash
emerge eselect-repository
eselect repository add project-neo git https://github.com/kool-os/project-neo.git
emerge --sync project-neo
```

## Using layman
```bash
layman -a project-neo
```

## Install neo
```bash
emerge =app-portage/neo-9999
```

## Install neon (GUI)
```bash
emerge =app-portage/neon-9999
```
