CSRF_TRUSTED_ORIGINS = [
    'http://localhost',
]

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME': 'testdb',
#         'USER': 'root',
#         'PASSWORD': 'testrootpwd',
#         'HOST': 'mysql',
#         'PORT': 3306,
#     }
# }
# 本地调试用
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3'
    }
}