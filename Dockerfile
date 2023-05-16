# Prepare the base environment.
FROM ubuntu:20.04 as builder_base_mooringlicensing
MAINTAINER asi@dbca.wa.gov.au

ENV DEBIAN_FRONTEND=noninteractive
#ENV DEBUG=True
ENV TZ=Australia/Perth
ENV EMAIL_HOST="smtp.corporateict.domain"
ENV DEFAULT_FROM_EMAIL='no-reply@dbca.wa.gov.au'
ENV NOTIFICATION_EMAIL='no-reply@dbca.wa.gov.au'
ENV NON_PROD_EMAIL='none@none.com'
ENV PRODUCTION_EMAIL=False
ENV EMAIL_INSTANCE='DEV'
ENV SECRET_KEY="ThisisNotRealKey"
ENV SITE_PREFIX='mls-dev'
ENV SITE_DOMAIN='dbca.wa.gov.au'
ENV OSCAR_SHOP_NAME='Parks & Wildlife'
ENV BPAY_ALLOWED=False
#ARG BRANCH_ARG
#ARG REPO_ARG
#ARG REPO_NO_DASH_ARG
#ENV BRANCH=$BRANCH_ARG
#ENV REPO=$REPO_ARG
#ENV REPO_NO_DASH=$REPO_NO_DASH_ARG

RUN apt-get clean
RUN apt-get update
RUN apt-get upgrade -y
RUN apt-get install --no-install-recommends -y wget git libmagic-dev gcc binutils libproj-dev gdal-bin python3 python3-setuptools python3-dev python3-pip tzdata cron rsyslog gunicorn
RUN apt-get install --no-install-recommends -y libpq-dev patch libreoffice
RUN apt-get install --no-install-recommends -y postgresql-client mtr htop vim nodejs npm
RUN ln -s /usr/bin/python3 /usr/bin/python 

# Install Python libs from requirements.txt.
FROM builder_base_mooringlicensing as python_libs_ml
WORKDIR /app
COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt \
  && rm -rf /var/lib/{apt,dpkg,cache,log}/ /tmp/* /var/tmp/*

#COPY libgeos.py.patch /app/
#RUN patch /usr/local/lib/python3.8/dist-packages/django/contrib/gis/geos/libgeos.py /app/libgeos.py.patch
#RUN rm /app/libgeos.py.patch

# Install the project (ensure that frontend projects have been built prior to this step).
FROM python_libs_ml
COPY gunicorn.ini manage_ml.py ./
#COPY timezone /etc/timezone
RUN echo "Australia/Perth" > /etc/timezone
ENV TZ=Australia/Perth
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN touch /app/.env
COPY .git ./.git
COPY mooringlicensing ./mooringlicensing
COPY patch_for_admin_0001_initial.patch ./patch_for_admin_0001_initial.patch
COPY patch_for_admin_0001_initial.patch_revert ./patch_for_admin_0001_initial.patch_revert
COPY patch_for_reversion_0001.patch ./patch_for_reversion_0001.patch
COPY patch_for_reversion_0001.patch_revert ./patch_for_reversion_0001.patch_revert
RUN python manage_ml.py collectstatic --noinput

RUN mkdir /app/tmp/
RUN chmod 777 /app/tmp/

COPY cron /etc/cron.d/dockercron
COPY startup.sh /
# Cron start
RUN service rsyslog start
RUN chmod 0644 /etc/cron.d/dockercron
RUN crontab /etc/cron.d/dockercron
RUN touch /var/log/cron.log
RUN service cron start
RUN chmod 755 /startup.sh
# cron end

# IPYTHONDIR - Will allow shell_plus (in Docker) to remember history between sessions
# 1. will create dir, if it does not already exist
# 2. will create profile, if it does not already exist
RUN mkdir /app/logs/.ipython
RUN export IPYTHONDIR=/app/logs/.ipython/
#RUN python profile create 

EXPOSE 8080
HEALTHCHECK --interval=1m --timeout=5s --start-period=10s --retries=3 CMD ["wget", "-q", "-O", "-", "http://localhost:8080/"]
CMD ["/startup.sh"]

