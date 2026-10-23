# Copyright 2024 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

# @ECLASS: neo-maturin.eclass
# @MAINTAINER:
# kool-os <kool-os@users.noreply.github.com>
# @AUTHOR:
# ssd <kool-os@users.noreply.github.com>
# @BLURB: Helper eclass for building PyO3 / maturin packages in project-neo
# @DESCRIPTION:
# Provides helper functions to build and install Python extensions built with Maturin.

case ${EAPI} in
	8) ;;
	*) die "${ECLASS}: EAPI ${EAPI} unsupported." ;;
esac

if [[ -z ${_NEO_MATURIN_ECLASS} ]]; then
_NEO_MATURIN_ECLASS=1

inherit distutils-r1

BDEPEND="
	dev-lang/rust:=
	dev-python/maturin[${PYTHON_USEDEP}]
"

# @FUNCTION: neo-maturin_src_compile
# @DESCRIPTION:
# Compile maturin-based PyO3 package into a wheel.
neo-maturin_src_compile() {
	debug-print-function ${FUNCNAME} "$@"

	cd "${S}" || die
	maturin build --release --skip-auditwheel --out "${BUILD_DIR}/wheels/" || die "maturin build failed"
}

# @FUNCTION: neo-maturin_src_install
# @DESCRIPTION:
# Install the wheel built by maturin.
neo-maturin_src_install() {
	debug-print-function ${FUNCNAME} "$@"

	cd "${S}" || die
	local wheel
	wheel=$(ls "${BUILD_DIR}"/wheels/*.whl 2>/dev/null | head -1)
	if [[ -n "${wheel}" ]]; then
		distutils-r1_python_install_wheel "${wheel}"
	else
		die "No wheel found after maturin build"
	fi
}

fi
