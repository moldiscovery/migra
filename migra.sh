#!/bin/bash

REGEX_GIT_URL="((git|ssh|http(s)?)|(git@[\w\.]+))(:(//)?)([\w\.@\:/\-~]+)(\.git)(/)?"
FILE=""
OWNER=""
URLS=()

print_help() {
    echo "Usage: migra -o [OWNER] [GIT_URLS]..."
    echo "  or:  migra -o [OWNER] -f [FILE]"
    echo "The used file must have one URL per line for the script to correctly work"
    echo
    echo "Options:"
    echo "    --help,   -h:  Prints this text"
    echo "    --owner,  -o:  User or organization that will be used to create the new repo"
    echo "    --file,   -f:  Path to file to parse for URLs"
    exit 0
}

validate_git_url() {
    echo "$1" | grep -P -q $REGEX_GIT_URL
    return $?
}

# Get opts
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -o|--owner)
            OWNER="$2"
            shift # past argument
            shift # past value
        ;;
        -f|--file)
            FILE="$2"
            shift # past argument
            shift # past value
        ;;
        -h|--help)
            print_help
        ;;
        *)
            # Saves valid URLs
            validate_git_url $1
            if [ $? -eq 0 ]; then
                URLS+=("$1")
            else
                echo "Ignoring invalid git URL $1"
            fi
            shift # past argument
        ;;
    esac
done

if [ -z "$OWNER" ]; then
    echo "Owner is not optional"
    exit 1
fi

# Check if executable is installed
check_is_installed() {
    eval "which $1 >/dev/null"
    if [ $? -ne 0 ]; then
        echo
        echo "$1 not found, please install or add it to PATH"
        exit 1
    fi
}

check_is_installed git
check_is_installed hub

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

if [ -n "$FILE" ]; then
    if [ ! -f "$FILE" ]; then
        echo "File not found $FILE"
        exit 1
    fi
    read_file "$FILE"
fi
