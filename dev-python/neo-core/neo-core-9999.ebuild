# Copyright 2024 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

EAPI=8

PYTHON_COMPAT=( python3_{11,12,13} )
DISTUTILS_USE_PEP517=maturin
CRATES="" # populated by cargo.eclass

inherit cargo distutils-r1 pypi

DESCRIPTION="Rust core engine for the neo unified package manager (PyO3 + Tokio)"
HOMEPAGE="https://github.com/kool-os/project-neo"

if [[ ${PV} == 9999 ]]; then
    inherit git-r3
    EGIT_REPO_URI="https://github.com/kool-os/project-neo.git"
    EGIT_CHECKOUT_DIR="${WORKDIR}/project-neo"
    EGIT_SUBDIR="neo-core"
    S="${WORKDIR}/project-neo/neo-core"
    SRC_URI=""
else
    SRC_URI=""
    S="${WORKDIR}/neo-core-${PV}"
fi

LICENSE="MIT"
SLOT="0"
KEYWORDS=""
IUSE=""

DEPEND="
    dev-lang/rust:=
    dev-python/maturin[${PYTHON_USEDEP}]
"
RDEPEND="${PYTHON_DEPS}"
BDEPEND="
    dev-lang/rust:=
    dev-python/maturin[${PYTHON_USEDEP}]
"

distutils_enable_tests pytest

python_compile() {
    cd "${S}" || die
    maturin build --release --skip-auditwheel --out "${BUILD_DIR}/wheels/" || die "maturin build failed"
}

distutils-r1_python_install_wheel() {
    distutils_wheel_install "${D}" "$@"
}

python_install() {
    cd "${S}" || die
    local wheel
    wheel=$(ls "${BUILD_DIR}"/wheels/*.whl 2>/dev/null | head -1)
    if [[ -n "${wheel}" ]]; then
        distutils-r1_python_install_wheel "${wheel}"
    else
        die "No wheel found after maturin build"
    fi
}
