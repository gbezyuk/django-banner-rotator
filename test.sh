virtualenv env
. env/bin/activate
pip install -r requirements.txt
cd testproject
./manage.py test banner_rotator
