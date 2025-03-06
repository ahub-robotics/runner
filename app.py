import argparse
import json
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import shared_memory

import flask
from flask import jsonify, request, render_template, redirect, url_for
from config import get_config_data, write_to_config, get_args
from server import Server
from waitress import serve
import webview
app = flask.Flask(__name__, static_folder='static')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

executor = ThreadPoolExecutor(max_workers=4)


@app.route('/status', methods=['GET'])
def get_robot_status():
    machine_id = request.args.get('machine_id')
    license_key = request.args.get('license_key')
    if machine_id != server.machine_id or license_key != server.license_key:
        return jsonify("closed")

    if server.run_robot_process:
        if server.run_robot_process.poll() != None:
            if server.status != "closed":
                server.status = "free"
        else:
            server.status = "running"
    else:
        if server.status != "closed":
            server.status = "free"
    return jsonify(server.status)


@app.route('/execution', methods=['GET'])
def get_execution_status():
    execution_id = request.args.get('id')
    if not server.run_robot_process:
        return jsonify({"status": "fail"})
    try:
        if server.run_robot_process.poll() == None:
            if execution_id == server.execution_id:
                return jsonify({"status": "working"})
            else:
                return jsonify({"status": "fail"})
    except:
        return jsonify({"status": "pending"})
    else:
        return jsonify({"status":"fail"})



@app.route('/block', methods=['GET'])
def set_robot_status():
    server.status = "blocked"
    response = app.response_class(
        response=json.dumps({'message': "blocked"}),
        status=300,
        mimetype='application/json')
    return response


@app.route('/run', methods=['POST'])
def run_robot():
    data = request.json
    try:

        executor.submit(server.run, data)
        server.status = "running"
        message = json.dumps({'message': "running"})
        status = 200
        response = app.response_class(
            response=message,
            status=status,
            mimetype='application/json')
    except Exception as e:
        server.send_log(str(e))
        server.status = "free"
        response = app.response_class(
            response=json.dumps({'message': e.__str__()}),
            status=400,
            mimetype='application/json')
    return response


@app.route('/stop', methods=['GET'])
def stop_robot():
    try:
        server.stop()
        response = app.response_class(
            response=json.dumps({'message': "OK"}),
            status=200,
            mimetype='application/json'
        )
    except Exception as e:
        server.set_status("fail")
        response = app.response_class(
            response=json.dumps({'message': e.__str__()}),
            status=200,
            mimetype='application/json'
        )
    return response


@app.route('/pause', methods=['GET'])
def pause_robot():
    try:
        server.pause()
        response = app.response_class(
            response=json.dumps({'message': "OK"}),
            status=200,
            mimetype='application/json')
    except Exception as e:
        server.set_status("fail")
        response = app.response_class(
            response=json.dumps({'message': e.__str__()}),
            status=200,
            mimetype='application/json')
    return response


@app.route('/resume', methods=['GET'])
def resume_robot():
    try:
        server.resume()
        response = app.response_class(
            response=json.dumps({'message': "OK"}),
            status=200,
            mimetype='application/json')
    except Exception as e:
        response = app.response_class(
            response=json.dumps({'message': e.__str__()}),
            status=200,
            mimetype='application/json')
    return response

def get_resource_path(relative_path):
    """Obtén la ruta absoluta del archivo, ajustada para PyInstaller."""
    # Verifica si estamos en un paquete PyInstaller
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


@app.route('/connected',  methods=['GET','POST'])
def connected():
    if request.method == 'GET':
        return render_template('connected.html')
    elif request.method == "POST":
        server.stop_execution()
        server.status = "closed"
        return redirect(url_for("connect"))



@app.route('/connect', methods=['GET', 'POST'])
def connect():
     if request.method == "GET":
        config_data = get_config_data()
        message = "Set machine credentials from the Robot Console."
        return render_template('form.html',
                                                ip=config_data.get("ip",os.popen('curl -s ifconfig.me').readline()),
                                                port=config_data["port"],
                                                token=config_data["token"],
                                                machine_id=config_data["machine_id"],
                                                license_key=config_data["license_key"],
                                                url=config_data["url"],
                                                message=message,
                                                color="white")

     elif request.method == "POST":

         data = request.form
         server.url = server.clean_url(data['url'])
         server.token = data['token']
         server.machine_id = data['machine_id']
         server.license_key = data['license_key']

         config_data = {}
         try:
             #server.set_machine_ip()
             server.status = 'free'

             for field, entry in data.items():
                 config_data[field] = entry

             write_to_config(data)
             return redirect(url_for("home"))

         except Exception:
             config_data = get_config_data()
             message = "Invalid credentials, ckeck them in the console and try again."
             return render_template('form.html',
                                    ip=config_data["ip"],
                                    port=config_data["port"],
                                    token=config_data["token"],
                                    machine_id=config_data["machine_id"],
                                    license_key=config_data["license_key"],
                                    url=config_data["url"],
                                    message=message,
                                    color="red")

@app.route('/',  methods=['GET'])
def home():
    try:
        #server.set_machine_ip()
        server.status = 'free'
        return redirect(url_for('connected'))
    except:
        return redirect(url_for('connect'))



socket_file = "/tmp/myapp_socket"

def check_already_running():
    try:
        shm = shared_memory.SharedMemory(name='my_app_lock', create=True, size=1)
    except FileExistsError:
        print("La aplicación ya está en ejecución.")
        sys.exit(0)
    return shm




def start_server():
    # Inicia el servidor en un hilo separado
    serve(app, host="0.0.0.0", port=server.port)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Introduce las variables de conexión')
    parser.add_argument('--url', type=str, help='Console url')
    parser.add_argument('--token', type=str, help='Folder Token')
    parser.add_argument('--machine_id', type=str, help='Machine ID')
    parser.add_argument('--license_key', type=str, help='Machine KEY')
    parser.add_argument('--folder', type=str, help='Robot`s folder')
    parser.add_argument('--ip', type=str, help='Public IP')
    parser.add_argument('--port', type=int, help='Port')

    s = check_already_running()
    config = get_config_data()

    config = get_args(parser, config)

    write_to_config(config)

    server = Server(config)

    server_thread = threading.Thread(target=start_server)
    server_thread.daemon = True
    server_thread.start()
    window = webview.create_window('Robot Runner', f'http://127.0.0.1:{server.port}/')
    webview.start()
