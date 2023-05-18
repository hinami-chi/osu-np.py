import configparser
import json
import os
import re
import socket
import threading
import websocket

config = configparser.ConfigParser()

# Si el archivo config.ini existe, lo leemos
if os.path.exists('config.ini'):
    config.read('config.ini')
else:
    # Si el archivo no existe, lo creamos con los valores por defecto
    config['Twitch'] = {'HOST': 'irc.chat.twitch.tv', 'PORT': '6667', 'NICK': '', 'PASS': '', 'CHANNEL': '#nick', 'NP_COMMAND': '!np'}
    with open('config.ini', 'w') as configfile:
        config.write(configfile)

# Obtenemos los valores de configuración
HOST = config['Twitch']['HOST']
PORT = int(config['Twitch']['PORT'])
NICK = config['Twitch']['NICK']
PASS = config['Twitch']['PASS']
CHANNEL = config['Twitch']['CHANNEL']
NP_COMMAND = config['Twitch']['NP_COMMAND']
has_printed_running = False
# Expresión regular para buscar el comando !np en los mensajes del chat
NP_REGEX = re.compile(NP_COMMAND)

def send_message(message):
    # Función para enviar mensajes al chat de Twitch
    s.send(f"PRIVMSG {CHANNEL} :{message}\r\n".encode())

def handle_messages():
    # Función para recibir y procesar mensajes del servidor de IRC
    while True:
        resp = s.recv(2048).decode()
        if resp.startswith("PING"):
            s.send("PONG\n".encode())
        else:
            # Buscamos si el mensaje contiene el comando !np y, si es así, enviamos el mensaje correspondiente al chat
            match = re.search(NP_REGEX, resp)
            if match:
                send_np_message()

def send_np_message():
    # Función para enviar el mensaje correspondiente al comando !np al chat de Twitch
    if state == 1:
        state_str = "editing"
        message = f'/me is {state_str} {artist} - {title} [{version}] mapped by {mapper} | https://osu.ppy.sh/s/{id_beatmap_set} | MIRRORS: https://beatconnect.io/b/{id_beatmap_set} | https://chimu.moe/d/{id_beatmap_set}'
    elif state == 2:
        state_str = "playing"
        if bpmmin == bpmmax:
            message = f'/me is {state_str} {artist} - {title} [{version}] +{mods} {bpmmax}BPM ★{sr} mapped by {mapper} | https://osu.ppy.sh/s/{id_beatmap_set} | MIRRORS: https://beatconnect.io/b/{id_beatmap_set} | https://chimu.moe/d/{id_beatmap_set}'
        else:
            message = f'/me is {state_str} {artist} - {title} [{version}] +{mods} BPM: {bpmmin}-{bpmmax} ★{sr} mapped by {mapper} | https://osu.ppy.sh/s/{id_beatmap_set} | MIRRORS: https://beatconnect.io/b/{id_beatmap_set} | https://chimu.moe/d/{id_beatmap_set}'
    else:
        state_str = "listening"
        message = f'/me is {state_str} {artist} - {title} | https://osu.ppy.sh/s/{id_beatmap_set} | MIRRORS: https://beatconnect.io/b/{id_beatmap_set} | https://chimu.moe/d/{id_beatmap_set}'

    # For others states, here -> https://github.com/Piotrekol/ProcessMemoryDataFinder/blob/99e2014447f6d5e5ba3943076bc8210b6498db5c/OsuMemoryDataProvider/OsuMemoryStatus.cs#L3
    send_message(message)

def on_message(ws, message):
    # La respuesta es un string JSON, así que necesitamos analizarlo
    global artist, title, version, mapper, id_beatmap_set, state, mods, sr, bpmmin, bpmmax, has_printed_running
    data = json.loads(message)

    # Accedemos al título de la canción utilizando la estructura especificada
    artist = data['menu']['bm']['metadata']['artist']
    title = data['menu']['bm']['metadata']['title']
    version = data['menu']['bm']['metadata']['difficulty']
    mapper = data['menu']['bm']['metadata']['mapper']
    id_beatmap_set = data['menu']['bm']['set']
    state = data['menu']['state']
    mods = data['menu']['mods']['str']
    sr = round(data['menu']['bm']['stats']['fullSR'], 2)
    bpmmin = int(data['menu']['bm']['stats']['BPM']['max'])
    bpmmax = int(data['menu']['bm']['stats']['BPM']['max'])

    if not has_printed_running:
        print(f"Running: Test typing '{NP_COMMAND}' in your channel: https://www.twitch.tv/{NICK}")
        has_printed_running = True

def on_error(ws, error):
    print(error)

def on_close(ws):
    print("Conexión cerrada")

def on_open(ws):
    # Enviamos un mensaje de suscripción para obtener información sobre la canción actual
    ws.send(json.dumps({'m': 'livesim/subscribe', 'p': {'all': True}}))

    # Creamos un hilo para procesar los mensajes del servidor de IRC
    t = threading.Thread(target=handle_messages)
    t.daemon = True
    t.start()

if __name__ == "__main__":
    
    # Creamos el socket de conexión al servidor de IRC de Twitch
    s = socket.socket()
    s.connect((HOST, PORT))

    # Enviamos los datos de login al servidor de IRC
    s.send(f"PASS {PASS}\n".encode())
    s.send(f"NICK {NICK}\n".encode())
    s.send(f"JOIN {CHANNEL}\n".encode())

    # Conectamos con el endpoint de ws de gosumemory
    ws = websocket.WebSocketApp("ws://localhost:24050/ws",
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)

    ws.on_open = on_open

    # Iniciamos el bucle de eventos de websocket
    ws.run_forever()
    
    ws.on_open = on_open

    # Iniciamos el bucle de eventos de websocket
    ws.run_forever()
