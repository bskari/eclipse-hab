set -u
set -e
export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3
pip3 install virtualenvwrapper
pushd ~pi/eclipse-2017-hab/pi/setup
sudo -u pi bash setup-virtualenv-2.sh
popd
