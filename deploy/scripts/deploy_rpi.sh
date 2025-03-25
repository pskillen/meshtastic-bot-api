#!/usr/bin/env bash

script_dir="$(dirname "$0")"
project_dir="$(realpath "${script_dir}/../..")"

remote_dir="~/MeshtasticAPI"

# Copy requirements.armv7.txt first
scp "${project_dir}/requirements.armv7.txt" paddy@meshcontrol.local:$remote_dir

# Run the pip install command on the remote server
ssh paddy@meshcontrol.local << EOF
    cd $remote_dir
    source venv/bin/activate
    pip install -r requirements.armv7.txt
EOF

# Rsync the rest of the project
rsync -av --exclude-from="${project_dir}/.rsyncignore" "${project_dir}/" paddy@meshcontrol.local:$remote_dir

# Run the migration script on the remote server
ssh paddy@meshcontrol.local << EOF
    cd $remote_dir
    source venv/bin/activate
    cd MeshtasticBotManager
    python manage.py migrate
EOF
