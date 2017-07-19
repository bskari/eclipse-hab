set -u
set -e
export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3
pip-3.2 install virtualenvwrapper
pushd ~pi/eclipse-2017-hab/setup
sudo -u pi bash setup-virtualenv-2.sh
popd
