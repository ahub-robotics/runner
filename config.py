import json
import os
import shutil
import sys
from pathlib import Path

user_dir = Path.home() / 'Robot'
user_dir.mkdir(exist_ok=True)
config_file = user_dir / 'config.json'


def get_resource_path(relative_path):
    """Obtén la ruta absoluta del archivo, ajustada para PyInstaller."""
    # Verifica si estamos en un paquete PyInstaller
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def write_to_config(config_data):
     # Crea el directorio si no existe
    try:
        #file = get_resource_path("config.json")
        with open(config_file, "w") as file:
            json.dump(config_data, file, indent=4)
    except Exception as e:
        print("Error al escribir en Config.json:", e)


def get_config_data():
    kwargs = {}
    if not os.path.isfile(config_file):
        shutil.copyfile(get_resource_path('config.json'), config_file)

    file = open(config_file, 'r')
    data = file.read()
    if data:
        json_data = json.loads(data)
        kwargs['url'] = json_data.get('url', "https://robot-console-a73e07ff7a0d.herokuapp.com/")
        kwargs['token'] = json_data.get('token', None)
        kwargs['machine_id'] = json_data.get('machine_id', None)
        kwargs['license_key'] = json_data.get('license_key', None)
        kwargs['folder'] = json_data.get('folder', f"{user_dir}/Robots")
        kwargs['ip'] = json_data.get('ip', os.popen('curl -s ifconfig.me').readline())
        kwargs['port'] = json_data.get('port', "8088")

    return kwargs


def get_args(parser, config):
    args = parser.parse_args()
    if args.url:
        config['url'] = args.url
    if args.token:
        config['token'] = args.token
    if args.machine_id:
        config['machine_id'] = args.machine_id
    if args.license_key:
        config['license_key'] = args.license_key
    if args.folder:
        config['folder'] = args.folder
    if args.ip:
        config['ip'] = args.ip
    if args.port:
        config['port'] = args.port
    for k in config:
        if config[k] is None:
            config[k] = input(f"Introduce {k}")

    return config