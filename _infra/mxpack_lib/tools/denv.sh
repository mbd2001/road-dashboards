#!/bin/bash --login

set -e  # enable usage of shell built-in command [ e.g. test -f ] and have script not exit when $? is 1
# set -x  # keep-comment for debug control

# ---- setup consts ----
SCRIPT_DIR=$(readlink -f $(dirname "$0"))
# ---- setup docker image ---
DIMAGE_DEFAULT=artifactory.sddc.mobileye.com/me-conda-docker-local/mx-conda:latest
DIMAGE=${DIMAGE:-$DIMAGE_DEFAULT}


if [[ "$1" == "--help" ]]; then
    __help_str="
      Usage: denv.sh [bash] [command]
    \n\n\n  Examples:
    \n\t    # Enter in docker in interactive mode
    \n\t    _infra/mxpack_lib/tools/denv.sh bash
    \n\n
    \t    # Run custom command inside container
    \n\t    _infra/mxpack_lib/tools/denv.sh bash --version
    \n\n
    \t    # Add custom docker params (command is pwd)
    \n\t    DOCKER_ARGS='-v /tmp:/kk' _infra/mxpack_lib/tools/denv.sh ls /kk
    \n\n
    \t    # Use cusom image instead of
    \n\t    DIMAGE=my-image _infra/mxpack_lib/tools/denv.sh ls
     "
    echo -e ${__help_str}
    exit 1
fi


if [[ "$1" == "bash" && "$2" == "" ]]; then
    IT=-it
    DCMD=bash
else
    IT=
    DCMD=$@
fi

# ---- check that denv is needed ----
if [[ "${DENV_OFF}" != "" ]]; then
    echo "[mx-tools:denv] @@[.level=info \
        .vars=@[.action=skip.enter .target=tunnel.denv .reason='already in denv']@ \
        .msg='@{.action} to @{.venv} since @{.reason}' \
        ]@@"
    $DCMD
else
    echo "[mx-tools:denv] @@[.level=info \
        .vars=@[.action=start.enter .target=tunnel.denv .dimage='${DIMAGE}']@ \
        .msg='@{.action} to @{.target} with docker image @{.dimage}' \
        ]@@"

    # those seems like constans in version dir
    branch_name_orig="$(git symbolic-ref --short HEAD)"
    branch_name_safe="$(echo ${branch_name_orig} | tr -cd '[:alnum:]._')"
    JOB_NAME_safe="$(echo ${JOB_NAME} | tr -cd '[:alnum:]._')"

    abs_path_to_repo_root=$(realpath $(git rev-parse --show-toplevel))
    abs_path_to_subpath_dir=$(realpath .)
    rel_path_to_subpath_dir=$(realpath --relative-to="${abs_path_to_repo_root}" "${abs_path_to_subpath_dir}")
    rel_path_to_repo_root=$(realpath --relative-to="${abs_path_to_subpath_dir}" "${abs_path_to_repo_root}")

    REPO_DIR_HOST=${abs_path_to_repo_root}
    WORKDIR_REL_PATH=${rel_path_to_subpath_dir}
    WORKDIR_HOST=$(realpath ${REPO_DIR_HOST}/${WORKDIR_REL_PATH})
    echo -e "[mx-tools:denv] @@SCRIPT_DIR=${SCRIPT_DIR} REPO_DIR_HOST=${REPO_DIR_HOST}"
    echo -e "[mx-tools:denv] @@WORKDIR_REL_PATH=${WORKDIR_REL_PATH} WORKDIR_HOST=${WORKDIR_HOST}"

    REPO_NAME=$(basename $(readlink -f $REPO_DIR_HOST))
    REPO_DIR_GUEST=/repos/$(basename ${REPO_DIR_HOST})
    WORKDIR_GUEST=${REPO_DIR_GUEST}/${WORKDIR_REL_PATH}
    echo -e "[mx-tools:denv] REPO_NAME=${REPO_NAME} REPO_DIR_GUEST=${REPO_DIR_GUEST} WORKDIR_GUEST=${WORKDIR_GUEST}"

    DCONDA_ENVS_PATH=/home/me.docker/.conda/envs
    echo -e "[mx-tools:denv] DCONDA_ENVS_PATH=${DCONDA_ENVS_PATH}"

    DEF_LOCAL_CONDA_ENVS_DIR=/tmp/__docker_data__/denv/__conda_envs__
    LOCAL_CONDA_ENVS_DIR_P=${LOCAL_CONDA_ENVS_DIR:-${DEF_LOCAL_CONDA_ENVS_DIR}}/$(whoami)


    JOB_NAME_safe="${JOB_NAME_safe/*2F//}"
    # branch_name_safe
    LOCAL_CONDA_ENVS_DIR_BRANCH="$(dirname ${LOCAL_CONDA_ENVS_DIR_P})/${branch_name_safe}/${JOB_NAME_safe}/$(basename ${LOCAL_CONDA_ENVS_DIR_P})"
    # on jenkins use /data/docker_conda_envs_cache as root for such caches
    if [[ "${JENKINS_URL}" != "" ]]; then
        LOCAL_CONDA_ENVS_DIR_BRANCH=/data/denv_c/${LOCAL_CONDA_ENVS_DIR_BRANCH}
    fi
    mkdir -p ${LOCAL_CONDA_ENVS_DIR_BRANCH}

    LOCAL_CONDA_ENVS_DIR=$(realpath ${LOCAL_CONDA_ENVS_DIR_BRANCH})
    mkdir -p ${LOCAL_CONDA_ENVS_DIR}
    echo -e "[mx-tools:denv] LOCAL_CONDA_ENVS_DIR=${LOCAL_CONDA_ENVS_DIR}"

    # --- Transform Params to docker run ---
    DOCKER_ARGS=${DOCKER_ARGS:-}

    # Set a specific GID aligned with the default docker above that was built as me.docker user [ GID 1000 ]

    # If ROOTLESS_DOCKER_MODE, set default USER_STR_DEFAULT to root ?

    ROOTLESS_DOCKER_MODE=NO
    for i in `pidof dockerd`; do
        [ `cat /proc/${i}/status | grep -i ^uid | awk '{print $2}'` != "0" ] \
            && ROOTLESS_DOCKER_MODE=YES;
    done

    echo "[mx-tools:denv] ROOTLESS_DOCKER_MODE=${ROOTLESS_DOCKER_MODE}"

    # force unset of DOCKER_HOST ?
    if [[ ${ROOTLESS_DOCKER_MODE} == "NO" ]] && [[ -v DOCKER_HOST ]]; then
        echo "[mx-tools:denv] unset DOCKER_HOST"
        unset DOCKER_HOST
    fi

    if [[ "${ROOTLESS_DOCKER_MODE}" == "NO" ]]; then
        # root docker - as is, with gid 1000
        USER_STR_DEFAULT="--user $(id -u):1000"
    else
        # rootless docker - set as "root" ( will map to user )
        USER_STR_DEFAULT="--user 0:0"
    fi

    USER_STR=${USER_STR:-$USER_STR_DEFAULT}

    echo "[mx-tools:denv] DOCKER_ARGS=${DOCKER_ARGS}"
    echo "[mx-tools:denv] USER_STR=${USER_STR}"

    if [[ "${DENV_CONDA_ENV_MOUNT_OFF}" != "" ]]; then
        echo "[mx-tools:denv] @@[.level=info \
            .vars=@[.action=skip.conda-envs-mount .target=tunnel.denv .reason='in jenkins']@ \
            .msg='@{.action} to @{.venv} since @{.reason}' \
            ]@@"
        MOUNT_LOCAL_CONDA_ENVS_DIR=
    else
        MOUNT_LOCAL_CONDA_ENVS_DIR="-v ${LOCAL_CONDA_ENVS_DIR}:${DCONDA_ENVS_PATH}"
    fi

    echo "[mx-tools:denv] MOUNT_LOCAL_CONDA_ENVS_DIR=${MOUNT_LOCAL_CONDA_ENVS_DIR}"
    host_git_config_user_name=$(git config user.name || echo '')
    # --- require explicit git user config (local or global)
    if [[ "${host_git_config_user_name}" == "" ]]; then
        echo "You should configure git user and email global or in repo before"
        exit 1
    fi

    host_git_config_user_name=$(git config user.name)
    host_git_config_user_email=$(git config user.email)

    if [[ ! -v "${GIT_AUTHOR_NAME}" ]]; then
        GIT_AUTHOR_NAME=$(git config user.name)
        GIT_COMMITTER_NAME=$(git config user.email)
        GIT_COMMITTER_EMAIL=$(git config user.email)
        echo "[mx-tools:denv] GIT_AUTHOR_NAME=${GIT_AUTHOR_NAME}"
        echo "[mx-tools:denv] GIT_COMMITTER_NAME=${GIT_COMMITTER_NAME}"
        echo "[mx-tools:denv] GIT_COMMITTER_EMAIL=${GIT_COMMITTER_EMAIL}"
    fi

    echo "[mx-tools:denv] host_git_config_user_name=${host_git_config_user_name}"
    echo "[mx-tools:denv] host_git_config_user_email=${host_git_config_user_email}"

    # -e VENV_OFF=${VENV_OFF}  # not in use
    # --- run full docker command --- --init

    docker run --rm  ${IT} ${USER_STR} \
        --workdir ${WORKDIR_GUEST} \
        ${DMAP_PORTS} \
        ${DOCKER_ARGS} \
        -e DENV_OFF=1 \
        -e BUILD_NUMBER=${BUILD_NUMBER} \
        -e BUILD_ID=${BUILD_ID} \
        -e BUILD_URL="${BUILD_URL}" \
        -e GIT_BRANCH="${GIT_BRANCH}" \
        -e GIT_COMMIT="${GIT_COMMIT}" \
        -e NODE_NAME="${NODE_NAME}" \
        -e host_git_config_user_email="${host_git_config_user_email}" \
        -e host_git_config_user_name="${host_git_config_user_name}" \
        -e GIT_AUTHOR_NAME="${GIT_AUTHOR_NAME}" \
        -e GIT_COMMITTER_NAME="${GIT_COMMITTER_NAME}" \
        -e GIT_COMMITTER_EMAIL="${GIT_COMMITTER_EMAIL}" \
        -e JOB_NAME="${JOB_NAME}" \
        -e BUILD_TAG="${BUILD_TAG}" \
        -e JENKINS_URL=${JENKINS_URL} \
        -e creds__art_user=${creds__art_user} \
        -v $(realpath ~/.aws):/home/me.docker/.aws \
        -v $(realpath ~/.gitconfig):/home/me.docker/.gitconfig:ro \
        -v $(realpath ~/.ssh):/home/me.docker/.ssh:ro \
        ${MOUNT_LOCAL_CONDA_ENVS_DIR} \
        -v ${REPO_DIR_HOST}:${REPO_DIR_GUEST} \
        -v $(realpath ~)/.config/rclone/rclone.conf:/home/me.docker/.config/rclone/rclone.conf:ro \
        ${DIMAGE} \
        ${DCMD}

    echo "[denv] @@[.level=info \
        .vars=@[.action=start.enter .target=tunnel.denv .dimage='${DIMAGE}']@ \
        .msg='@{.action} to @{.target} with docker image @{.dimage}' \
        ]@@"
fi
