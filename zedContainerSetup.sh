### This script will install the necessary dependencies, install the zed sdk and build and install opencv

apt-get update
apt-get -y --no-install-recommends install sudo wget ca-certificates qt5-default udev

# add zedUser
useradd -G sudo,video zedUser
sudo passwd -d zedUser \ # delete password for zedUser
# Do not require password when sudoing as zedUser
echo "zedUser ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers \

## Install the ZED sdk
wget https://download.stereolabs.com/zedsdk/2.3/ubuntu -O ZED_SDK_Linux_Ubuntu16_v2.3.1.run
chmod +x ZED_SDK_Linux_Ubuntu16_v2.3.1.run
sudo -u zedUser ./ZED_SDK_Linux_Ubuntu16_v2.3.1.run --quiet --nox11

## Build and install opencv
apt-get -y install build-essential cmake git libgtk2.0-dev pkg-config libavcodec-dev libavformat-dev libswscale-dev
cd /tmp
git clone https://github.com/Itseez/opencv.git
cd opencv
git checkout tags/3.1.0
mkdir build
cd build
cmake  -D WITH_CUDA=OFF -D BUILD_TESTS=OFF -D BUILD_PERF_TESTS=OFF -D BUILD_EXAMPLES=OFF -D CMAKE_BUILD_TYPE=RELEASE ..

make -j3
make install