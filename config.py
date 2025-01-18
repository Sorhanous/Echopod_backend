import boto3
import json

def get_secret():
    secret_name = "Bevi_Secrets"
    region_name = "us-west-2"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except Exception as e:
        raise e

    secret = get_secret_value_response['SecretString']
    return json.loads(secret)

secrets = get_secret()

class Config:
    DEBUG = False
    TESTING = False
    SECRET_KEY = secrets.get('SECRET_KEY', 'your-default-secret-key')
    DATABASE_URI = f"postgresql://{secrets['DB_USER']}:{secrets['DB_PASSWORD']}@{secrets['DB_HOST']}/{secrets['DB_NAME']}"
    OPENAI_API_KEY = secrets['OPENAI_API_KEY']
    OPENAI_API_SECRET_2 = secrets['OPENAI_API_SECRET_2']
    MODEL3 = secrets['Model3']
    MODEL4 = secrets['Model4']
    YOUTUBE_API_KEY = secrets['Youtube_API_KEY']
    YOUTUBE_API_KEY_2 = secrets['youtube_api_key_2']

class ProductionConfig(Config):
    DEBUG = False

class DevelopmentConfig(Config):
    DEBUG = True
    DEVELOPMENT = True

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
}
