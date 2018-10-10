import sys
import yaml
import json
import getpass
import argparse
from ansible.parsing.vault import VaultEditor, VaultSecret, is_encrypted


class VaultYaml(unicode):
    pass


def vault_constructor(loader, node):
    return node.value


def literal_unicode_representer(dumper, data):
    return dumper.represent_scalar("!vault", data, style='|')


def encrypt_credentials_file(passcode, deployment_name):
    yaml.add_representer(VaultYaml, literal_unicode_representer)
    yaml.add_constructor(u'!vault', vault_constructor)
    credentials_file = 'deployments/' + deployment_name + '/credentials.yml'
    with open(credentials_file, 'r') as file:
        credentials = yaml.load(file.read())

    with open('schemas/credentials.json') as credentials_schema:
        data = yaml.load(credentials_schema)
    props = data['properties']
    encryt_credentials_list = []
    for k, v in props.items():
        if ('encrypt' not in v) or v['encrypt']:
            encryt_credentials_list.append(k)

    if credentials is not None:
        for cred in encryt_credentials_list:
            if cred in credentials:
                secret = VaultSecret(passcode)
                editor = VaultEditor()
                if not is_encrypted(credentials[cred]):
                    vaultCode = editor.encrypt_bytes(credentials[cred], secret)
                else:
                    vaultCode = credentials[cred]
                credentials[cred] = VaultYaml(vaultCode)
        with open(credentials_file, 'w') as file:
            yaml.dump(credentials, file, default_flow_style=False)


def main():
    parser = argparse.ArgumentParser(
        description='Encrypt user credentials file')
    parser.add_argument(
        "--deployment",
        help="Optional deployment name - will default to 'default' deployment",
        default="default")
    args = parser.parse_args()

    try:
        print "This file will ecrypt user credentials for MetroAE"
        print "All user comments in the user credentials file might be lost"
        passcode = getpass.getpass()
    except:
        print "Error in getting passcode from command line"
        sys.exit()
    encrypt_credentials_file(passcode, args.deployment)


if __name__ == '__main__':
    main()
