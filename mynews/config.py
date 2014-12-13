class Config(object):
    DEBUG = False
    TESTING = False
    CONSUMER_KEY = 'BJIpFUnXoRMk4Q=='
    CONSUMER_SECRET = '+2vCyqFiehc6MeBBzct4H1/CIss='
    APPID = 'dj0zaiZpPU04TDh6WHptblN1QiZzPWNvbnN1bWVyc2VjcmV0Jng9MDQ-'
    FROM_MAIL_ADDRESS = 'junpei.k.29@gmail.com'
    FROM_MAIL_PASSWORD = '2108058m'

class ProductConfig(Config):
    pass

class DevelopConfig(Config):
    DEBUG = True
