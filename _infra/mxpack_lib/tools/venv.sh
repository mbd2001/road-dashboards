#!/bin/bash

set -e
# set -x

SCRIPT_DIR=$(readlink -f $(dirname "$0"))
CRUN_SH=${SCRIPT_DIR}/crun.sh

# # echo
REQUESTED_ENV_ARG=$1
REQUESTED_ENV_VAL=${REQUESTED_ENV_ARG:-dev}
# use same script for run
RUN_PARAM=$2

CTV_SELECTED_VENV=$(task conda:venv:get:fullname REQUESTED_ENV_VAL=$REQUESTED_ENV_VAL -o interleaved)

[[ "$CTV_SELECTED_VENV" == "base" ]] && \
    # first, handle the special case of base mamba env; do not include minimamba install prefix
    IS_INSIDE=$(which python | grep "conda/bin/python" 2>&1 > /dev/null && echo 1 || echo 0 ) || \
    IS_INSIDE=$(which python | grep ${CTV_SELECTED_VENV} 2>&1 > /dev/null && echo 1 || echo 0 )

echo "CTV_SELECTED_VENV=$CTV_SELECTED_VENV, IS_INSIDE=$IS_INSIDE"
echo "---"

if [[ "${IS_INSIDE}" == "1" || "${VENV_OFF}" == "1" ]]; then
    echo "already activated ${CTV_SELECTED_VENV}"
    if [[ "${RUN_PARAM}" == "run" ]]; then
        shift
        shift
        $@
    fi
else
    # prevent double activation
    conda deactivate 2> /dev/null || true
    conda deactivate 2> /dev/null || true
    # task conda:venv:update:$REQUESTED_ENV_VAL-env
    if [[ "${RUN_PARAM}" == "" ]]; then
        # assume source. TODO: check more strictly
        conda activate $CTV_SELECTED_VENV
    elif [[ "${RUN_PARAM}" == "run" ]]; then
        shift
        shift
        VENV_NAME=${CTV_SELECTED_VENV} ${CRUN_SH} $@
    fi
fi
