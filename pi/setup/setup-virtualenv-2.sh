pushd ~pi/eclipse-2017-hab/pi
export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3
source /usr/local/bin/virtualenvwrapper.sh
mkvirtualenv eclipse-2017-hab -p /usr/bin/python3
workon eclipse-2017-hab
pip install -r requirements.txt
deactivate
popd
