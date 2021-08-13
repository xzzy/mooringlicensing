#!/bin/bash
git log --pretty=oneline -30 > ./ml_git_history
docker image build --no-cache --tag $1 .
