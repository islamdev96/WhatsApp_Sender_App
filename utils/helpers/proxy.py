"""Proxy configuration, extension generation, and cleanup."""
import os
from utils.logger import logger, log_exception


def check_proxy(proxy_type, host, port, username=None, password=None, timeout=10):
    """Tests a proxy connection using urllib.
    
    Returns (success, info_dict).
    """
    import urllib.request
    import json

    proxy_type = proxy_type.lower()
    proxy_url = f"{proxy_type}://"
    if username and password:
        proxy_url += f"{username}:{password}@"
    proxy_url += f"{host}:{port}"
    
    proxy_handler = urllib.request.ProxyHandler({
        'http': proxy_url,
        'https': proxy_url
    })
    
    opener = urllib.request.build_opener(proxy_handler)
    try:
        # Use http://ip-api.com/json (clean HTTP) to verify public IP and location details
        response = opener.open("http://ip-api.com/json", timeout=timeout)
        data = json.loads(response.read().decode('utf-8'))
        if data.get('status') == 'success':
            return True, {
                'ip': data.get('query'),
                'country': data.get('country'),
                'city': data.get('city'),
                'isp': data.get('isp')
            }
        else:
            return True, {
                'ip': data.get('query') or 'Unknown',
                'country': 'Unknown',
                'city': 'Unknown',
                'isp': 'Unknown'
            }
    except Exception as e:
        return False, {'error': str(e)}



def create_proxy_extension(profile_dir, proxy_type, host, port, username, password):
    """Generates a custom Chrome extension dynamically to handle proxy credentials authentication."""
    import json
    ext_dir = os.path.join(profile_dir, "proxy_extension")
    os.makedirs(ext_dir, exist_ok=True)
    
    manifest_path = os.path.join(ext_dir, "manifest.json")
    background_path = os.path.join(ext_dir, "background.js")
    
    manifest_json = {
        "version": "1.0.0",
        "manifest_version": 2,
        "name": "Chrome Proxy Helper Extension",
        "permissions": [
            "proxy",
            "tabs",
            "unlimitedStorage",
            "storage",
            "<all_urls>",
            "webRequest",
            "webRequestBlocking"
        ],
        "background": {
            "scripts": ["background.js"]
        },
        "minimum_chrome_version": "22.0.0"
    }
    
    background_js = f"""
    var config = {{
        mode: "fixed_servers",
        rules: {{
            singleProxy: {{
                scheme: "{proxy_type.lower()}",
                host: "{host}",
                port: parseInt({port})
            }},
            bypassList: []
        }}
    }};

    chrome.proxy.settings.set({{value: config, scope: "regular"}}, function() {{}});

    chrome.webRequest.onAuthRequired.addListener(
        function(details) {{
            return {{
                authCredentials: {{
                    username: "{username}",
                    password: "{password}"
                }}
            }};
        }},
        {{urls: ["<all_urls>"]}},
        ["blocking"]
    );
    """
    
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_json, f, indent=4)
        
    with open(background_path, "w", encoding="utf-8") as f:
        f.write(background_js)
        
    return ext_dir



def cleanup_proxy_extension(profile_dir):
    """Remove the dynamically generated proxy extension from a Chrome profile.

    Should be called after the browser session ends to avoid leaving
    stale credential files on disk.
    """
    import shutil
    ext_dir = os.path.join(profile_dir, "proxy_extension")
    if os.path.isdir(ext_dir):
        try:
            shutil.rmtree(ext_dir, ignore_errors=True)
            logger.info("Cleaned up proxy extension in %s", profile_dir)
        except Exception as exc:
            log_exception(f"Could not remove proxy extension dir {ext_dir}", exc)



