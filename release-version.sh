#!/usr/bin/env bash

SHELL_FOLDER=$(cd "$(dirname "$0")";pwd)
cd $SHELL_FOLDER

##############################init###############################################
if [ ! -n "$1" ] ;then
    echo "error: please input a release version number!"
    echo "Usage $0 <version number>"
    exit 1
else
    if [[ "$1" =~ ^[A-Za-z0-9.]*$ ]] ;then
        echo -e "\033[3;30;47m*** Build a new release version: \033[5;36;47m($1)\033[0m)"
        echo -e "Institute of Software, Chinese Academy of Sciences"
        echo -e "        wuyuewen@otcaix.iscas.ac.cn"
        echo -e "              Copyright (2019)\n"
    else
        echo "error: wrong syntax in release version number, support chars=[A-Za-z0-9.]"
        exit 1
    fi
fi

VERSION=$1

echo -e "\033[3;30;47m*** Pull latest version from Github.\033[0m"
git pull
if [ $? -ne 0 ]; then
    echo "    Failed to pull latest version from Github!"
    exit 1
else
    echo "    Success pull latest version."
fi

##############################patch stuff#########################################
SHELL_FOLDER=$(dirname $(readlink -f "$0"))
cd ${SHELL_FOLDER}
if [ ! -d "./dist" ]; then
	mkdir ./dist
fi
cp -f config ./dist
chmod +x kubeovn-adm
gzexe ./kubeovn-adm
cp -f kubeovn-adm ./dist
gzexe -d ./kubeovn-adm
rm -f ./kubeovn-adm~
cp ovn-ovsdb.service ./dist
cp -rf ../yamls ./dist
echo ${VERSION} > ./VERSION
pyinstaller -F kubevmm_adm.py -n kubevmm-adm
if [ $? -ne 0 ]; then
    echo "    Failed to compile <kubevmm-adm>!"
    exit 1
else
    echo "    Success compile <kubevmm-adm>."
fi
pyinstaller -F vmm.py
if [ $? -ne 0 ]; then
    echo "    Failed to compile <vmm>!"
    exit 1
else
    echo "    Success compile <vmm>."
fi
git clone https://github.com/kubesys/kubeext-SDS.git
cd ./kubeext-SDS
pyinstaller -F kubesds-adm.py
if [ $? -ne 0 ]; then
    echo "    Failed to compile <kubesds-adm>!"
    exit 1
else
    echo "    Success compile <kubesds-adm>."
fi
pyinstaller -F kubesds-rpc.py
if [ $? -ne 0 ]; then
    echo "    Failed to compile <kubesds-rpc>!"
    exit 1
else
    echo "    Success compile <kubesds-rpc>."
fi
cp -f ./dist/kubesds-adm ../docker/virtctl
cp -f ./dist/kubesds-adm ../dist
cp -f ./dist/kubesds-rpc ../docker/virtctl
cp -f ./dist/kubesds-rpc ../dist
cd ..
rm -rf ./kubeext-SDS

find ${SHELL_FOLDER}/dist -maxdepth 1 -type f -exec ln -s {} $HOME/rpmbuild/SOURCES/ \;
find ${SHELL_FOLDER}/dist -type d -exec ln -s {} $HOME/rpmbuild/SOURCES/ \;

cp -rf ./dist/yamls/ ./VERSION ./dist/vmm ./dist/kubevmm-adm ./dist/config ./dist/kubeovn-adm docker/virtctl
if [ $? -ne 0 ]; then
    echo "    Failed to copy stuff to docker/virtctl!"
    exit 1
else
    echo "    Success copy stuff to docker/virtctl."
fi

python -m py_compile *.py
python -m py_compile utils/*.py

##############################patch image#########################################

# step 1 copy file
if [ ! -d "./docker/virtctl/utils" ]; then
	mkdir ./docker/virtctl/utils
fi
if [ ! -d "./docker/virtlet/utils" ]; then
	mkdir ./docker/virtlet/utils
fi
cp -rf utils/*.pyc docker/virtctl/utils/
cp -rf utils/*.pyc docker/virtlet/utils/
cp -rf config arraylist.cfg virtctl_in_docker.pyc invoker.pyc virtctl.pyc docker/virtctl
cp -rf config arraylist.cfg virtlet_in_docker.pyc host_cycler.pyc libvirt_event_handler.pyc os_event_handler.pyc virtlet.pyc docker/virtlet

rm -rf *.pyc
rm -rf utils/*.pyc

#step 2 docker build
cd docker
docker build base -t registry.cn-hangzhou.aliyuncs.com/cloudplus-lab/kubevirt-base:latest
docker build virtlet -t registry.cn-hangzhou.aliyuncs.com/cloudplus-lab/kubevirt-virtlet:${VERSION}
docker build virtctl -t registry.cn-hangzhou.aliyuncs.com/cloudplus-lab/kubevirt-virtctl:${VERSION}
docker build virtlet -t registry.cn-hangzhou.aliyuncs.com/cloudplus-lab/kubevirt-virtlet:latest
docker build virtctl -t registry.cn-hangzhou.aliyuncs.com/cloudplus-lab/kubevirt-virtctl:latest

#step 3 docker push
echo -e "\033[3;30;47m*** Login docker image repository in aliyun.\033[0m"
echo "Username: bigtree0613@126.com"
docker login --username=bigtree0613@126.com registry.cn-hangzhou.aliyuncs.com
if [ $? -ne 0 ]; then
    echo "    Failed to login aliyun repository!"
    exit 1
else
    echo "    Success login...Pushing images!"
fi
docker push registry.cn-hangzhou.aliyuncs.com/cloudplus-lab/kubevirt-base:latest
docker push registry.cn-hangzhou.aliyuncs.com/cloudplus-lab/kubevirt-virtctl:${VERSION}
docker push registry.cn-hangzhou.aliyuncs.com/cloudplus-lab/kubevirt-virtlet:${VERSION}
docker push registry.cn-hangzhou.aliyuncs.com/cloudplus-lab/kubevirt-virtctl:latest
docker push registry.cn-hangzhou.aliyuncs.com/cloudplus-lab/kubevirt-virtlet:latest

###############################patch version to SPECS/kubevmm.spec######################################################
echo -e "\033[3;30;47m*** Patch release version number to SPECS/kubevmm.spec\033[0m"
cd ..
sed "4s/.*/%define         _verstr      ${VERSION}/" SPECS/kubevmm.spec > SPECS/kubevmm.spec.new
mv SPECS/kubevmm.spec.new SPECS/kubevmm.spec
if [ $? -ne 0 ]; then
    echo "    Failed to patch version number to SPECS/kubevmm.spec!"
    exit 1
else
    echo "    Success patch version number to SPECS/kubevmm.spec."
fi

echo -e "\033[3;30;47m*** Push new SPECS/kubevmm.spec to Github.\033[0m"
git add ./SPECS/kubevmm.spec
git commit -m "new release version ${VERSION}"
git push
if [ $? -ne 0 ]; then
    echo "    Failed to push SPECS/kubevmm.spec to Github!"
    exit 1
else
    echo "    Success push SPECS/kubevmm.spec to Github."
fi

