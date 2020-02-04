#!/bin/bash

REGEX_GIT_URL="((git|ssh|http(s)?)|(git@[\w\.]+))(:(//)?)([\w\.@\:/\-~]+)(\.git)(/)?"
URLS=()

print_help() {
    echo "Usage:"
    echo "    migra git@bitbucket.org:<your_org>/<your_repo>.git"
    echo "    migra https://<your_username>@bitbucket.org/<your_org>/<your_repo>.git"
    echo "    migra -f <path_to_file>"
    echo "    The used file must have one URL per line for the script to correctly work"
    echo

    echo "Options:"
    echo "    --help, -h: Prints this text"
    echo "    --file, -f: Path to file to parse for URLs"
}

# Check if executable is installed
check_is_installed() {
    eval "which $1 >/dev/null"
    if [ $? -ne 0 ]; then
        echo
        echo "Please install git"
        exit 1
    fi
}

validate_git_url() {
    echo "$1" | grep -P -q $REGEX_GIT_URL
    return $?
}

read_file() {
    i=1
    while read line; do
        validate_git_url $line
        if [ $? -eq 0 ]; then
            URLS+=("$line")
        else
            echo "Line $i of $1 is not a valid git URL"
        fi
        i=`expr $i + 1`
    done < "$1"
}

check_is_installed git
check_is_installed hub

if [ $# -eq 0 ] \
|| [ "$1" == "--help" ] \
|| [ "$1" == "-h" ]
then
    print_help
    exit 0
fi

if [ "$1" == "--file" ] || [ "$1" == "-f" ]; then
    if [ -z "$2" ]; then
        echo "Option $1 requires an argument"
        exit 1
    fi
    read_file "$2"
fi

for url in "$@"; do
    validate_git_url $url
    if [ $? -eq 0 ]; then
        URLS+=("$url")
    else
        echo "Ignoring invalid git URL $url"
    fi
done
