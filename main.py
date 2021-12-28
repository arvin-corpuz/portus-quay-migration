import requests
import subprocess
import configparser
from subprocess import check_output

config = configparser.ConfigParser()
config.read('config.ini')

PORTUS_URL = config['default']['portus_url']
PORTUS_AUTH_USER = config['default']['portus_api_auth_user']
PORTUS_AUTH_TOKEN = config['default']['portus_api_auth_token']
PORTUS_DOCKER_USER = config['default']['portus_docker_user']
PORTUS_DOCKER_PASSWD = config['default']['portus_docker_user_password']

QUAY_URL = config['default']['quay_url']
QUAY_OAUTH2_TOKEN = config['default']['quay_api_oauth2_token']
QUAY_DOCKER_USER = config['default']['quay_docker_user']
QUAY_DOCKER_PASSWD = config['default']['quay_docker_user_password']

if __name__ == '__main__':

    # Get all namespaces from portus
    url = f'https://{PORTUS_URL}/api/v1/repositories'
    headers = {
        'Accept': 'application/json',
        'Portus-Auth': f'{PORTUS_AUTH_USER}:{PORTUS_AUTH_TOKEN}'
    }

    output = requests.get(url, headers=headers)
    
    namespaces = []
    image_with_errors = []
    for repository in output.json():
        namespace = repository.get('namespace').get('name')
        full_name = repository.get('full_name')
        
        # Create organization
        url = f'https://{QUAY_URL}/api/v1/organization/'

        headers = {
            'Authorization': f'Bearer {QUAY_OAUTH2_TOKEN}'
        }

        obj = {
            'name': namespace
        }

        # migrate everything with no namespace to global namespace
        if 'portus' in namespace:
            namespace = 'global'
            obj['name'] = 'global'

        if namespace not in namespaces:
            namespaces.append(namespace)
            output = requests.post(url, headers=headers, json=obj, verify=False)

        skopeo_sync = f'skopeo sync --src-creds={PORTUS_DOCKER_USER}:{PORTUS_DOCKER_PASSWD} --dest-creds={QUAY_DOCKER_USER}:{QUAY_DOCKER_PASSWD} --dest-tls-verify=false --src=docker --dest=docker {PORTUS_URL}/{full_name} {QUAY_URL}/{namespace}'

        print(f'Syncing {full_name}')
        try:
            output = check_output(skopeo_sync.split(' '))
        except:
            print(f'Error {full_name}')
            image_with_errors.append(full_name)

    print(f'Image with errors \n {image_with_errors}')
    
        