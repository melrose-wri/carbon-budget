# Questions:
# Need to include git?
# Use the same release of ubuntu as the spot machine?
# Is postgres RUN formatted correctly? I think spot machine has Postgres 9.6.5 and postgis 2.3
# Which of the longer list of installations do I need?
# Some packages in requirements.txt I'm not sure about
# What does `RUN pip3 install -e .` do again?



FROM ubuntu:16.04   # The release on the AMI I've been using

ENV DIR=/usr/local/app

RUN apt-get install -y osgeo/gdal:ubuntu-small-3.0.4

# based on https://severalnines.com/database-blog/deploying-postgresql-docker-container
RUN apt-key adv --keyserver hkp://p80.pool.sks-keyservers.net:80 --recv-keys B97B0AFCAA1A47F044F244A07FCC7D46ACCC4CF8
RUN echo "deb http://apt.postgresql.org/pub/repos/apt/ precise-pgdg main" > /etc/apt/sources.list.d/pgdg.list


RUN sed -i '/^[fedora]/a\exclude=postgresql*' /etc/yum.repos.d/fedora.repo \
    && sed -i '/^[updates]/a\exclude=postgresql*' /etc/yum.repos.d/fedora-updates.repo

RUN apt-get install -y https://download.postgresql.org/pub/repos/yum/12/fedora/fedora-30-x86_64/pgdg-fedora-repo-latest.noarch.rpm

RUN apt-get install -y \
    make \
    automake \
    gcc \
    gcc-c++ \
    kernel-devel \
    libpq-devel \
    python3 \
    python3-devel \
    gdal \
    gdal-python-tools \
    && apt-get clean all


RUN mkdir -p ${DIR}
WORKDIR ${DIR}

COPY requirements.txt .
RUN pip3 install -r requirements.txt

RUN pip3 install -e .

# Set current work directory to /tmp. This is important when running as AWS Batch job
# When using the ephemeral-storage launch template /tmp will be the mounting point for the external storage
# In AWS batch we will then mount host's /tmp directory as docker volume /tmp
WORKDIR /tmp