from os import environ


class Config(object):
    SECRET_KEY = environ.get('SECRET_KEY') or 'rimma-ravilevna-favorite-star-of-the-10th-class'
    JSON_AS_ASCII = environ.get('JSON_AS_ASCII') or False
    UPLOAD_FOLDER = environ.get('UPLOAD_FOLDER') or "static/files"
