#!/bin/bash --login

set -e

# !!! DON'T call Tasks from this file !!!

CONDABIN_PATH='/usr/local/conda/condabin'

if [[ "${PATH}" == *"${CONDABIN_PATH}"* ]]; then
    echo "[crun]  -- $CONDABIN_PATH in PATH; Skip Adding"
else
    echo "[crun]  -- $CONDABIN_PATH NOT in PATH; Adding !"
    export PATH=${CONDABIN_PATH}:${PATH}
fi

# set -x  # keep-comment for debug control

# ---- check that venv is present ----
# it fails if no env present (for any command include 'pwd')
if mamba run -n  "${VENV_NAME}" pwd ; then
    IS_VENV_PRESENT=1
else
    echo "[crun] Requested venv ${VENV_NAME} is not present. abort"
    exit 1
fi

# ---- dont activate venv if already activated ----
if [[  "${VENV_NAME}_" == "_" ]]; then
    echo "[crun]  -- no environment selected, use existing"
elif [[ "${VENV_NAME}_" == "${CONDA_DEFAULT_ENV}" ]]; then
    echo "[crun]  -- environment already selected, ${VENV_NAME}"
else
    echo "[crun]  -- activating ${VENV_NAME}"
    conda activate ${VENV_NAME}
fi

# ---- process environment variables in the beggining of command ----
# HACK: mostly for mxpack module, accept PYTHONPATH=. envvar setting
if [[ "$1" == "PYTHONPATH=." ]]; then
    export PYTHONPATH=.
    shift
fi

export MXCTL_HOME="${HOME}/.mxctl"
export PATH="${MXCTL_HOME}/bin:${PATH}"

$@
