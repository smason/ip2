# base everything on a recent Ubuntu
FROM ubuntu:14.04

# get system packages up to date
RUN apt-get update && apt-get -y upgrade

# install a basic scientific python
RUN apt-get -y install python3 python3-pip cython3 \
         python3-numpy python3-scipy python3-pandas python3-matplotlib && \
    pip3 install seaborn

# get h5py installed (HDF5 development libraries needed)
RUN apt-get -y install libhdf5-dev && \
    pip3 install h5py

# RUN apt-get -y install ttf-bitstream-vera && \
#     pip3 install GPy

# get our code (git needed first)
RUN apt-get -y install git-core && \
    git clone https://github.com/smason/ip2.git ip2

# configure CSI
WORKDIR /ip2
MAINTAINER Sam Mason <sam@samason.uk>
ENTRYPOINT ["python3", "-m", "csi"]
CMD ["--help"]
