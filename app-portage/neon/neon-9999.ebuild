# Copyright 2024 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

EAPI=8

PYTHON_COMPAT=( python3_{11,12,13} )
DISTUTILS_USE_PEP517=setuptools

inherit distutils-r1 xdg

DESCRIPTION="neon - Qt6 GUI frontend for the neo unified package manager"
HOMEPAGE="https://github.com/kool-os/project-neo"

if [[ ${PV} == 9999 ]]; then
    inherit git-r3
    EGIT_REPO_URI="https://github.com/kool-os/project-neo.git"
    EGIT_CHECKOUT_DIR="${WORKDIR}/project-neo"
    S="${WORKDIR}/project-neo/neon"
else
    SRC_URI="https://github.com/kool-os/project-neo/archive/v${PV}.tar.gz -> ${P}.tar.gz"
    S="${WORKDIR}/project-neo-${PV}/neon"
fi

LICENSE="MIT"
SLOT="0"
KEYWORDS=""
IUSE=""

RDEPEND="
    dev-python/pyqt6[${PYTHON_USEDEP}]
    app-portage/neo[${PYTHON_USEDEP}]
"
BDEPEND="
    dev-python/setuptools[${PYTHON_USEDEP}]
"

src_install() {
    distutils-r1_src_install
    # Install .desktop file
    domenu neon.desktop 2>/dev/null || domenu neon/neon.desktop 2>/dev/null || true
    # Install icon if present
    if [[ -f neon/icons/neon.png ]]; then
        doicon neon/icons/neon.png
    elif [[ -f icons/neon.png ]]; then
        doicon icons/neon.png
    fi
}

pkg_postinst() {
    xdg_pkg_postinst
    elog "neon GUI has been installed. Launch with:"
    elog "  neon"
    elog "  or via your application launcher"
}
