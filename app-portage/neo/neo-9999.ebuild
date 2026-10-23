# Copyright 2024 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

EAPI=8

PYTHON_COMPAT=( python3_{11,12,13} )
DISTUTILS_USE_PEP517=setuptools

inherit distutils-r1

DESCRIPTION="neo - Unified CLI package manager for Gentoo (ebuild/flatpak/brew/cask/ebins)"
HOMEPAGE="https://github.com/kool-os/project-neo"

if [[ ${PV} == 9999 ]]; then
    inherit git-r3
    EGIT_REPO_URI="https://github.com/kool-os/project-neo.git"
    EGIT_CHECKOUT_DIR="${WORKDIR}/project-neo"
    S="${WORKDIR}/project-neo/neo-cli"
else
    SRC_URI="https://github.com/kool-os/project-neo/archive/v${PV}.tar.gz -> ${P}.tar.gz"
    S="${WORKDIR}/project-neo-${PV}/neo-cli"
fi

LICENSE="MIT"
SLOT="0"
KEYWORDS=""
IUSE="rust-core"

RDEPEND="
    dev-python/click[${PYTHON_USEDEP}]
    dev-python/rich[${PYTHON_USEDEP}]
    dev-python/toml[${PYTHON_USEDEP}]
    dev-python/pexpect[${PYTHON_USEDEP}]
    rust-core? ( dev-python/neo-core[${PYTHON_USEDEP}] )
"
BDEPEND="
    dev-python/setuptools[${PYTHON_USEDEP}]
"

distutils_enable_tests pytest

pkg_postinst() {
    elog "neo has been installed. Usage:"
    elog "  neo install <pkg> :<backend>"
    elog "  neo search <pkg> :<backend>"
    elog "  Backends: :ebuild :flatp :brew :cask :ebins"
    elog ""
    elog "See 'neo --help' for full usage."
}
