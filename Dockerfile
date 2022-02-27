# Instructions for getting rednotebook working on macos with x:
# https://gist.github.com/paul-krohn/e45f96181b1cf5e536325d1bdee6c949

# For windows, you have something like cygwin that you can use

# 1) install xwindows on your machine, and run it with a script like startx
# % docker build . --tag rednotebook:LATEST
# % export REDNOTEBOOK_HOME=<select a directory for your journal> && mkdir $REDNOTEBOOK_HOME

# 2) startup rednotebnook:
# % docker run --rm -e DISPLAY=host.docker.internal:0 -it --volume ${REDNOTEBOOK_HOME}:/root/.rednotebook rednotebook:LATEST

# You can update to the latest release of rednotebook by running "docker build" again.

FROM ubuntu:latest
RUN apt-get update
RUN apt install -y software-properties-common
RUN add-apt-repository ppa:rednotebook/stable
RUN apt-get update
RUN apt-get install -y rednotebook adwaita-icon-theme-full

# Hides GTK accessibility warnings
ENV NO_AT_BRIDGE=1

CMD ["/usr/bin/rednotebook"]
