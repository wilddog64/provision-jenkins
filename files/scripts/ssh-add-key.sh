#!/usr/bin/env bash

# if ssh-agent is not running then run it
ssh_passphrase=$1
ssh_agents=$(pgrep -u jenkins ssh-agent)
if [[ -z $ssh_agents ]]; then
	eval "$(ssh-agent -s)"
fi
ssh-add
