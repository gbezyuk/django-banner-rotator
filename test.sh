virtualenv env
. env/bin/activate
pip install -r requirements.txt
cd testproject
mkdir media
mkdir media/uploads
./manage.py test banner_rotator
