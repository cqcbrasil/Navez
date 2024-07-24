import requests
import subprocess

# URL da lista IPTV
url_lista_iptv = "https://github.com/punkstarbr/STR-YT/raw/main/RUSSIA.M4U"

# Função para testar cada canal com FFmpeg
def testar_canal_ffmpeg(url):
    try:
        # Comando FFmpeg para verificar se o canal está ativo por 7 segundos
        comando = [
            "ffmpeg",
            "-loglevel", "quiet",
            "-i", url,
            "-t", "7",
            "-f", "null", "-"
        ]
        
        # Chama FFmpeg e verifica o retorno
        subprocess.run(comando, check=True)
        return True
    except subprocess.CalledProcessError:
        return False

# Função principal para processar a lista IPTV
def processar_lista_iptv(url_lista_iptv):
    try:
        # Baixa a lista IPTV
        response = requests.get(url_lista_iptv)
        response.raise_for_status()
        
        # Lista para armazenar os canais funcionando
        canais_funcionando = []
        
        # Abre o arquivo para escrita do novo arquivo M3U
        with open("espanol.m3u", "w", encoding="utf-8") as arquivo_saida:
            linhas = response.text.splitlines()
            
            for linha in linhas:
                if linha.startswith("#EXTINF"):
                    # Testa se o canal está funcionando usando FFmpeg
                    if testar_canal_ffmpeg(linhas[linhas.index(linha) + 1]):
                        canais_funcionando.append(linha)
                        arquivo_saida.write(linha + "\n")
                        arquivo_saida.write(linhas[linhas.index(linha) + 1] + "\n")
                elif linha.startswith("#EXTM3U") or linha.strip() == "":
                    arquivo_saida.write(linha + "\n")
                else:
                    arquivo_saida.write(linha + "\n")
        
        print(f"Processo concluído. {len(canais_funcionando)} canais funcionando foram escritos no arquivo OUTRA LISTA.m3u.")
    
    except requests.RequestException as e:
        print(f"Erro ao baixar a lista IPTV: {e}")

# Chamada da função principal para processar a lista IPTV
processar_lista_iptv(url_lista_iptv)

#!/usr/bin/python3

import requests
import os
import sys
import streamlink
import logging
from logging.handlers import RotatingFileHandler
import json

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  

log_file = "log.txt" 
file_handler = RotatingFileHandler(log_file)
file_handler.setLevel(logging.DEBUG) 

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)

banner = r'''
#EXTM3U
'''

def grab(url):
    try:
        if url.endswith('.m3u') or url.endswith('.m3u8') or ".ts" in url:
            return url

        session = streamlink.Streamlink()
        streams = session.streams(url)
        logger.debug("URL Streams %s: %s", url, streams)
        if "best" in streams:
            return streams["best"].url
        return None
    except streamlink.exceptions.NoPluginError as err:
        logger.error("URL Error No PluginError %s: %s", url, err)
        return url
    except streamlink.StreamlinkError as err:
        logger.error("URL Error %s: %s", url, err)
        return None


def check_url(url):
    try:
        response = requests.head(url, timeout=15)
        if response.status_code == 200:
            logger.debug("URL Streams %s: %s", url, response)
            return True
    except requests.exceptions.RequestException as err:
        pass
    
    try:
        response = requests.head(url, timeout=15, verify=False)
        if response.status_code == 200:
            logger.debug("URL Streams %s: %s", url, response)
            return True
    except requests.exceptions.RequestException as err:
        logger.error("URL Error %s: %s", url, err)
        return None
    
    return False

channel_data = []
channel_data_json = []

channel_info = os.path.abspath(os.path.join(os.path.dirname(__file__), '../channel_info.txt'))

with open(channel_info) as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith('~~'):
            continue
        if not line.startswith('http:') and len(line.split("|")) == 4:
            line = line.split('|')
            ch_name = line[0].strip()
            grp_title = line[1].strip().title()
            tvg_logo = line[2].strip()
            tvg_id = line[3].strip()
            channel_data.append({
                'type': 'info',
                'ch_name': ch_name,
                'grp_title': grp_title,
                'tvg_logo': tvg_logo,
                'tvg_id': tvg_id
            })
        else:
            link = grab(line)
            if link and check_url(link):
                channel_data.append({
                    'type': 'link',
                    'url': link
                })

with open("playlist.m3u", "w") as f:
    f.write(banner)
    f.write(f'\n#EXTM3U')


    prev_item = None

    for item in channel_data:
        if item['type'] == 'info':
            prev_item = item
        if item['type'] == 'link' and item['url']:
            f.write(f'\n#EXTINF:-1 group-title="{prev_item["grp_title"]}" tvg-logo="{prev_item["tvg_logo"]}" tvg-id="{prev_item["tvg_id"]}", {prev_item["ch_name"]}')
            f.write('\n')
            f.write(item['url'])
            f.write('\n')


prev_item = None

for item in channel_data:
    if item['type'] == 'info':
        prev_item = item
    if item['type'] == 'link' and item['url']:
        channel_data_json.append( {
            "id": prev_item["tvg_id"],
            "name": prev_item["ch_name"],
            "alt_names": [""],
            "network": "",
            "owners": [""],
            "country": "AR",
            "subdivision": "",
            "city": "Buenos Aires",
            "broadcast_area": [""],
            "languages": ["spa"],
            "categories": [prev_item["grp_title"]],
            "is_nsfw": False,
            "launched": "2016-07-28",
            "closed": "2020-05-31",
            "replaced_by": "",
            "website": item['url'],
            "logo": prev_item["tvg_logo"]
        })

with open("playlist.json", "w") as f:
    json_data = json.dumps(channel_data_json, indent=2)
    f.write(json_data)
