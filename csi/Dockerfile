# run as:
#   docker build -f csi/Dockerfile  .

# base everything on a recent Ubuntu
FROM debian:latest

# get system packages up to date then install a basic scientific python
RUN apt-get update && apt-get -y upgrade && \
    apt-get -y install python3 \
         python3-numpy python3-scipy python3-pandas python3-matplotlib \
	 python3-seaborn python3-h5py

# add and configure our code
ADD . ip2
WORKDIR /ip2
MAINTAINER Sam Mason <sam@samason.uk>
ENTRYPOINT ["python3", "-m", "csi"]
VOLUME ["/agave"]
CMD ["--help"]
