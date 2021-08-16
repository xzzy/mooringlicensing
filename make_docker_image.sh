#!/bin/bash
cd mooringlicensing/frontend/mooringlicensing/ &&
npm run build &&
cd ../../../ &&
source venv3.8/bin/activate &&
./manage_ml.py collectstatic --no-input &&
git log --pretty=oneline -30 > ./ml_git_history &&
docker image build --no-cache --tag $1 .
