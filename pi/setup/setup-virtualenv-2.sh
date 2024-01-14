pushd ~pi/eclipse-hab/pi
export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3
source /usr/local/bin/virtualenvwrapper.sh
mkvirtualenv eclipse-hab -p /usr/bin/python3
workon eclipse-hab
pip install -r requirements.txt
deactivate
popd
