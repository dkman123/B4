#!/bin/bash

# Big Brother Bot (B4) Management - http://www.bigbrotherbot.net
# Maintainer: Daniele Pantaleone <fenix@bigbrotherbot.net>
# App Version: 0.14
# Last Edit: 26/07/2015

### BEGIN INIT INFO
# Provides:          b4
# Required-Start:    $remote_fs
# Required-Stop:     $remote_fs
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Manage Big Brother Bot (B4) - http://www.bigbrotherbot.net
# Description:       Manage Big Brother Bot (B4) - http://www.bigbrotherbot.net
### END INIT INFO

########################################################################################################################
#
#  CHANGELOG
#
# ----------------------------------------------------------------------------------------------------------------------
#
#  2014-11-09 - 0.1  - Fenix         - initial version
#  2015-07-26 - 0.14 - Fenix         - do not allow to use root at all when using this very script
#                                    - create b4 home directory if it has not been created already
#  2024-02-12 - 0.15 - isopropanol   - updated to b4 using python 3.12.2


### SETUP
AUTO_RESTART="${B4_AUTORESTART:-1}" # will run b4 in auto-restart mode if set to 1
DATE_FORMAT="%a, %b %d %Y - %r"     # data format to be used when logging console output
LOG_ENABLED="${B4_LOG:-0}"          # if set to 1, will log console output to file
DEVELOPER="${B4_DEV:-0}"            # if set to 1, will activate developer mode
USE_COLORS="1"                      # if set to 1, will make use of bash color codes in the console output

### DO NOT MODIFY!!!
B4_DIR=""                   # will be set to the directory containing b4 source code (where we can find b4_run.py)
B4_RUN="b4_run.py"          # python executable which starts b4
B4_HOME=".b4"               # the name of the B4 home directory (located inside $HOME)
COMMON_PREFIX="b4_"         # a common prefix b4 configuration files must have to be parsed by this script
CONFIG_DIR="b4/conf"        # directory containing b4 configuration files (will be appended to ${B4_DIR}
CONFIG_EXT=(".ini" ".xml")  # list of b4 configuration file extensions
LOG_DIR="log"               # the name of the directory containing the log file (will be appended to ${SCRIPT_DIR})
PID_DIR="pid"               # the name of the directory containing the b4 pid file (will be appended to ${SCRIPT_DIR})
SCRIPT_DIR=""               # will be set to the directory containing this very script

########################################################################################################################
# OUTPUT FUNCTIONS

# @name p_out
# @description Parse Q3 alike color codes and translates them into BASH output colors.
#              All given strings are being hand over to p_log after stripping them from color codes.
function p_out() { 
    if [ "${USE_COLORS}" == "0" ]; then
        echo -e "${@//^[0-9]}"
    else
        echo -e $(echo "$@" | sed "s/\^\([0-9]\)/\\\\033[3\1m/g; s/\\\\033\[30m/\\\\033[0m/g") "\033[0m"
    fi
    # write console output to main log
    p_log "${@//^[0-9]}"
    return 0
}

# @name p_log
# @description Log messages in the log file.
function p_log()  {
    if [ ! "${LOG_ENABLED}" -eq 0 ]; then
        # make sure to have a valid directory for the logfile
        if [ ! -d "${SCRIPT_DIR}/${LOG_DIR}" ]; then
            mkdir "${SCRIPT_DIR}/${LOG_DIR}"
        fi
        LOG_FILE="${SCRIPT_DIR}/${LOG_DIR}/app.log"
        if [ ! -f "${LOG_FILE}" ]; then
            if ! STDERR=$(touch "${LOG_FILE}" 2>&1 > /dev/null); then
                LOG_ENABLED=0  # prevent infinite loop between p_out and p_log
                p_out "^1ERROR^0: could not create log file: no log will be written! ^3($STDERR)^0"
                return 1
            fi
        fi
        DATE=$(date +"${DATE_FORMAT}")
        echo "[${DATE}]  >  ${@}" 1>> "${LOG_FILE}" 2> /dev/null
    fi
    return 0
}

########################################################################################################################
# UTILITIES

# @name join
# @description Join array elements into a string using the given separator.
# @example      join , a "b c" d        # a,b c,d
#               join / var local tmp    # var/local/tmp
#               join , "${FOO[@]}"      # a,b,c
function join() { 
    local IFS="${1}";
    shift; 
    echo "${*}";
}

# @name b4_conf_path
# @description Will output the absolute path of the B4 instance configuration file: stdout 
#              redirection needs to be handled properly when using this function.
#              If no configuration file is found it outputs nothing (check using if [ -z $VAR ]).
function b4_conf_path() {
    local B4="${1}"
    for i in ${CONFIG_EXT[@]}; do
        local HOME_CONFIG="${HOME}/${B4_HOME}/${COMMON_PREFIX}${B4}${i}"
        local B4_CONFIG="${B4_DIR}/${CONFIG_DIR}/${COMMON_PREFIX}${B4}${i}"
        if [ -f "${HOME_CONFIG}" ]; then
            echo "${HOME_CONFIG}"
            break
        elif [ -f "${B4_CONFIG}" ]; then
            echo "${B4_CONFIG}"
            break
        fi
    done
}

# @name b4_pid_path
# @description Will output the absolute path of the B4 instance PID file: stdout redirection 
#              needs to be handled properly when using this function.
#              If no configuration file is found it outputs nothing check using if [ -z $VAR ]).
function b4_pid_path() {
    local B4="${1}"
    local PID_FILE="${SCRIPT_DIR}/${PID_DIR}/${COMMON_PREFIX}${B4}.pid"
    if [ -f "${PID_FILE}" ]; then
        echo "${PID_FILE}"
    fi
}

# @name b4_is_running
# @description Retrieve the status of a B4 instance given its name and configuration file path.
# @return 0 if the B4 daemon is running
#         1 if the B4 daemon is not running
#         2 if the B4 daemon was running but recently crashed
function b4_is_running() {
    local B4="${1}"
    local CONFIG="${2}"
    local SCREEN="${COMMON_PREFIX}${B4}"
    local PROCESS="${B4_DIR}/${B4_RUN}"
    local NUMPROC=$(ps ax | grep ${SCREEN} | grep ${PROCESS} | grep ${CONFIG} | grep -v grep | wc -l)

    if ([ ${AUTO_RESTART} -eq 1 ] && [ ${NUMPROC} -eq 4 ]); then
        # screen is running with B4 process inside and auto-restart mode (using subprocess)
        return 0
    elif ([ ! ${AUTO_RESTART} -eq 1 ] && [ ${NUMPROC} -eq 2 ]); then
        # both screen and process running => B4 running
        return 0
    else
        if [ -z "$(b4_pid_path ${B4})" ]; then
            # no PID file found => not running
            return 1
        else
            # PID file found but process not running => CRASH
            return 2
        fi
    fi
}

# @name b4_uptime
# @description Will output the uptime of a B4 instance given its PID file path: stdout
#              redirection needs to be handled properly when using this function.
function b4_uptime() {
    local PID_FILE="${1}"
    local NOW="$(date +"%s")"
    local MOD="$(stat --printf="%Y" "${PID_FILE}")"
    local SECDIFF=$(( ${NOW} - ${MOD} ))
    if [ ${SECDIFF} -lt 60 ]; then
        echo "${SECDIFF}s"
    elif ([ ${SECDIFF} -ge 60 ] && [ ${SECDIFF} -lt 3600 ]); then
        echo "$(echo "$(( ${SECDIFF} /  60 ))" | bc -l)m"
    else
        echo "$(echo "$(( ${SECDIFF} /  3600 ))" | bc -l)h"
    fi
}

# @name b4_list
# @description Will output a list of available B4 instances by checking available configuration 
#              files: stdout redirection needs to be handled properly when using this function.
#              The function is "duplicate-safe", so if a B4 instance has multiple configuration 
#              files specified (one for each supported configuration file extension), only the one 
#              with highest importance will be considered (according to the order extensions are 
#              specified in the configuration value ${CONFIG_EXT[@]})
function b4_list() {
    local B4_LIST=()
    local B4_CONF_PATH="${B4_DIR}/${CONFIG_DIR}"
    local B4_HOME_PATH="${HOME}/${B4_HOME}"
    local B4_CONFIG_LIST=$(find "${B4_HOME_PATH}" "${B4_CONF_PATH}" -maxdepth 1 -type f  \( -name "b4_*.ini" -o -name "b4_*.xml" \) -print | sort)
    for i in ${B4_CONFIG_LIST}; do
        local B4_NAME="$(basename ${i})"
        local B4_NAME="${B4_NAME:${#COMMON_PREFIX}}"
        for i in ${CONFIG_EXT[@]}; do
            local B4_NAME="${B4_NAME%${i}}"
        done
        IN=0
        for i in ${B4_LIST[@]}; do
            if [ "${i}" == "${B4_NAME}" ]; then
                IN=1
                break
            fi
        done
        if [ ${IN} -eq 0 ]; then
            B4_LIST+=("${B4_NAME}")
        fi
    done
    echo $(join ' ' "${B4_LIST[@]}")
}

########################################################################################################################
# MAIN FUNCTIONS

# @name b4_start
# @description Main B4 instance startup function.
function b4_start() {

    local B4="${1}"
    local CONFIG_FILE="$(b4_conf_path ${B4})"

    # check if already running
    b4_is_running "${B4}" "${CONFIG_FILE}"

    local RTN="${?}"
    local PID_FILE="$(b4_pid_path ${B4})"
    if [ ${RTN} -eq 0 ]; then
        local PID="$(cat ${PID_FILE})"
        local UPTIME="$(b4_uptime ${PID_FILE})"
        p_out "B4[${B4}] is already running [PID : ^2${PID}^0 - UPTIME : ^2${UPTIME}^0]"
        return 1
    elif [ ${RTN} -eq 2 ]; then
        p_out "^3WARNING^0: B4[${B4}] recently crashed..."
        rm "${PID_FILE}"
        sleep 1
    fi

    # start the B4 instance and sleep a bit: give it time to crash (if that's the case).
    # recompute also the PID file path because $(b4_pid_path) may output an empty string 
    # if the B4 was not running (and thus no PID file could be found in previous call)
    local SCREEN="${COMMON_PREFIX}${B4}"
    local PROCESS="${B4_DIR}/${B4_RUN}"
    local PID_FILE="${SCRIPT_DIR}/${PID_DIR}/${COMMON_PREFIX}${B4}.pid"

    if [ ${AUTO_RESTART} -eq 1 ]; then
        screen -DmS "${SCREEN}" python "${PROCESS}" --restart --console --config "${CONFIG_FILE}" &
    else
        screen -DmS "${SCREEN}" python "${PROCESS}" --console --config "${CONFIG_FILE}" &
    fi

    echo "${!}" > "${PID_FILE}"

    if [ ${AUTO_RESTART} -eq 1 ]; then
        sleep 6
    else
        sleep 1
    fi

    # check for proper B4 startup
    b4_is_running "${B4}" "${CONFIG_FILE}"

    local RTN="${?}"
    if [ ${RTN} -eq 0 ]; then
        local PID=$(cat ${PID_FILE})
        p_out "B4[${B4}] started [PID : ^2${PID}^0]"
        return 0
    else
        if [ ${RTN} -eq 2 ]; then
            rm "${PID_FILE}"
        fi
        p_out "^1ERROR^0: could not start B4[${B4}]"
        return 1
    fi
}

# @name process_start
# @description Main B4 instance shutdown function.
function b4_stop() {

    local B4="${1}"
    local CONFIG_FILE="$(b4_conf_path ${B4})"

    # check if already running
    b4_is_running "${B4}" "${CONFIG_FILE}"

    local RTN="${?}"
    local PID_FILE="$(b4_pid_path ${B4})"

    if [ ${RTN} -eq 1 ]; then
        p_out "B4[${B4}] is already stopped"
        return 1
    elif [ ${RTN} -eq 2 ]; then
        p_out "^3WARNING^0: B4[${B4}] recently crashed..."
        rm "${PID_FILE}"
        return 1
    fi

    # close the screen (and thus the process running inside)
    local PID="$(cat ${PID_FILE})"
    local UPTIME="$(b4_uptime ${PID_FILE})"
    local SCREEN="${COMMON_PREFIX}${B4}"
    screen -S "${PID}.${SCREEN}" -X quit &

    sleep 1

    # check for proper B4 shutdown
    b4_is_running "${B4}" "${CONFIG_FILE}"

    local RTN="${?}"
    if [ ${RTN} -eq 0 ]; then
        p_out "^1ERROR^0: could not stop B4[${B4}]"
        return 1
    else
        rm "${PID_FILE}"
        p_out "B4[${B4}] stopped [UPTIME : ^1${UPTIME}^0]"
        return 0
    fi
}

# @name b4_status
# @description Main B4 instance status check function. 
function b4_status() {

    local B4="${1}"
    local CONFIG_FILE="$(b4_conf_path ${B4})"

    # check if already running
    b4_is_running "${B4}" "${CONFIG_FILE}"

    local RTN="${?}"
    local PID_FILE="$(b4_pid_path ${B4})"

    case ${RTN} in
        0)
            local PID="$(cat ${PID_FILE})"
            local UPTIME="$(b4_uptime ${PID_FILE})"
            p_out "B4[${B4}] ^2ALIVE ^0[PID : ^2${PID}^0 - UPTIME : ^2${UPTIME}^0]"
            ;;
        1)
            p_out "B4[${B4}] ^3OFFLINE^0"
            ;;
        2)
            p_out "B4[${B4}] ^1CRASHED^0"
            ;;
        *)
            p_out "^1ERROR^0: invalid code returned: ^3${RTN}^0"
            p_out "Please report this to B4 developers: http://forum.bigbrotherbot.net"
            return 1
            ;;
    esac

    return 0
}

# @name b4_clean
# @description Clean B4 directories by removing all python compiled files. It will stop all 
#              the running B4 instances and restart them after the cleaning has been performed.
function b4_clean() {
    local B4_RUNNING=()
    local B4_LIST=$(b4_list)
    for i in ${B4_LIST}; do
        # check if B4 is running and if so stop it
        b4_is_running "${i}" "$(b4_conf_path ${i})"
        local RTN="${?}"
        if [ ${RTN} -eq 0 ]; then
            b4_stop "${i}"
            B4_RUNNING+=("${i}")
        fi
    done

    local B4_RUNNING_LIST=$(join ' ' "${B4_RUNNING[@]}")
    find "${B4_DIR}" -type f \( -name "*.pyc" -o -name "*.pid" \) \
                                -exec rm {} \; \
                                -exec printf "." \; \

    echo " DONE!"

    # restart all the B4 which were running 
    for i in ${B4_RUNNING_LIST}; do
        b4_start "${i}"
    done

    return 0
}

# @name do_usage
# @description Print the main help text
function b4_usage() {
    # do not  use p_out here otherwise it gets logged
    echo "
    -usage: b4.sh  start   [<name>] - start B4
                                stop    [<name>] - stop B4
                                restart [<name>] - restart B4
                                status  [<name>] - display current B4 status
                                clean            - clean B4 directory

    Copyright (C) 2014 Daniele Pantaleone <fenix@bigbrotherbot.net>
    Support: http://forum.bigbrotherbot.net
    "
    return 0
}

########################################################################################################################
# MAIN EXECUTION

# set some global variables needed in main execution and functions
SCRIPT_DIR="$(cd -P -- "$(dirname -- "${0}")" && pwd -P)"
B4_DIR="$(dirname ${SCRIPT_DIR})"

# check that the script is not executed by super user to avoid permission problems
# we will allow the B4 status check tho since the operation is totally harmless
if [ ! "${DEVELOPER}" -eq 0 ]; then # allow developers to use root to start b4
    if [ ${UID} -eq 0 ]; then
      p_out "^1ERROR^0: do not execute B4 as super user [root]"
      exit 1
    fi
fi

# check for python to be installed in the system
if [ -z $(which python) ]; then
    p_out "^1ERROR^0: The Python interpreter seems to be missing on your system"
    p_out "You need to install Python ^22.7 ^0to run B4"
    exit 1
fi

# check for correct python version to be installed on the system
VERSION=($(python -c 'import sys; print("%s %s" % (sys.version_info.major, sys.version_info.minor));'))
if [ ${VERSION[0]} -eq 3 ]; then
    p_out "^1ERROR^0: B4 is not yet compatible with Python ^33^0"
    p_out "You need to install Python ^22.7 ^0to run B4"
    exit 1
fi

if [ ${VERSION[1]} -lt 7 ]; then
    p_out "^1ERROR^0: B4 can't run under Python ^3${VERSION[0]}.${VERSION[1]}^0"
    p_out "You need to install Python ^22.7 ^0to run B4"
    exit 1
fi

# check for the PID directory to exists (user may have removed it)
if [ ! -d "${SCRIPT_DIR}/${PID_DIR}" ]; then
    mkdir "${SCRIPT_DIR}/${PID_DIR}"
fi

# check for b4 home directory (maybe b4 didn't started yet so it didn't create it)
if [ ! -d "${HOME}/${B4_HOME}" ]; then
    mkdir "${HOME}/${B4_HOME}"
fi

case "${1}" in

    "start")
        B4_LIST=$(b4_list)
        for i in ${B4_LIST}; do
            if ([ -z "${2}" ] || [ "${2}" == "${i}" ]); then
                b4_start "${i}"
                RUN=1
            fi
        done
        if [ -z ${RUN+xxx} ]; then
            if [ -z "${2}" ]; then
                p_out "^3WARNING^0: no B4 instance available"
            else
                p_out "^1ERROR^0: could not find configuration file for B4[${2}]"
            fi
            exit 1
        fi
        ;;
    "stop")
        B4_LIST=$(b4_list)
        for i in ${B4_LIST}; do
            if ([ -z "${2}" ] || [ "${2}" == "${i}" ]); then
                b4_stop "${i}"
                RUN=1
            fi
        done
        if [ -z ${RUN+xxx} ]; then
            if [ -z "${2}" ]; then
                p_out "^3WARNING^0: no B4 instance available"
            else
                p_out "^1ERROR^0: could not find configuration file for B4[${2}]"
            fi
            exit 1
        fi
        ;;
    "restart")
        B4_LIST=$(b4_list)
        for i in ${B4_LIST}; do
            if ([ -z "${2}" ] || [ "${2}" == "${i}" ]); then
                b4_stop "${i}"
                RUN=1
            fi
        done
        if [ -z ${RUN+xxx} ]; then
            if [ -z "${2}" ]; then
                p_out "^3WARNING^0: no B4 instance available"
            else
                p_out "^1ERROR^0: could not find configuration file for B4[${2}]"
            fi
            exit 1
        fi
        for i in ${B4_LIST}; do
            if ([ -z "${2}" ] || [ "${2}" == "${i}" ]); then
                b4_start "${i}"
            fi
        done
        ;;

    "status")
        B4_LIST=$(b4_list)
        for i in ${B4_LIST}; do
            if ([ -z "${2}" ] || [ "${2}" == "${i}" ]); then
                b4_status "${i}"
                RUN=1
            fi
        done
        if [ -z ${RUN+xxx} ]; then
            if [ -z "${2}" ]; then
                p_out "^3WARNING^0: no B4 instance available"
            else
                p_out "^1ERROR^0: could not find configuration file for B4[${2}]"
            fi
            exit 1
        fi
        ;;

    "clean")
        p_out "^3WARNING^0: all running B4 will be restarted"
        echo -n "Do you want to continue [y/N]? "
        read ANSWER
        if ([ "${ANSWER:0:1}" == "y" ] || [ "${ANSWER:0:1}" == "Y" ]); then
            b4_clean
        else
            p_out "... Aborted!"
            exit 1
        fi
        ;;
    *)
        b4_usage
        ;;
esac
exit "${?}"
