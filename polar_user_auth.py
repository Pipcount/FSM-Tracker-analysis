#!/usr/bin/env python

from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import requests
import threading
from genericpath import exists


import yaml
from accesslink import AccessLink

CALLBACK_PORT = 5000
CALLBACK_ENDPOINT = "/oauth2_callback"

CONFIG_FILENAME = "config.yml"
TOKEN_FILENAME = "usertokens.yml"

REDIRECT_URL = "http://localhost:{}{}".format(CALLBACK_PORT, CALLBACK_ENDPOINT)

def load_config(filename):
    """Load configuration from a yaml file"""
    with open(filename) as f:
        return yaml.full_load(f)


def save_config(config, filename):
    """Save configuration to a yaml file"""
    with open(filename, "w+") as f:
        yaml.safe_dump(config, f, default_flow_style=False)
        
config = load_config(CONFIG_FILENAME)

accesslink = AccessLink(client_id=config['client_id'],
                        client_secret=config['client_secret'])


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith(CALLBACK_ENDPOINT):
            parsed_path = urllib.parse.urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed_path.query)
            authorization_code = query_params.get("code", [None])[0]
            
            if authorization_code:
                token_response = accesslink.get_access_token(authorization_code)
                
                user_id = token_response["x_user_id"]
                accesstoken = token_response["access_token"]

                usertokens = token_db()

                usertokens["tokens"] = remove_oldtokens(array = usertokens["tokens"], newuserid= user_id)
                newtoken = {"user_id": user_id, "access_token":accesstoken}
                usertokens["tokens"].append(newtoken)
                save_config(usertokens, TOKEN_FILENAME)
                
                try:
                    accesslink.users.register(access_token=accesstoken)
                except requests.exceptions.HTTPError as err:
                    if err.response.status_code != 409:
                        raise err
                
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"Client authorized! You can now close this page.")
                
                # Shutdown the server
                threading.Thread(target=self.server.shutdown).start()
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Missing authorization code.")
        else:
            self.send_response(404)
            self.end_headers()

def remove_oldtokens(array , newuserid):
    res = []
    for item in array:
        if item == None:
            del item
            continue
        useritem = item["user_id"]
        usertoken = item["access_token"]
        if useritem != newuserid:
            res.append({"user_id": useritem,
                    "access_token":usertoken})
    return res

def token_db():
    usertokens = None
    if exists(TOKEN_FILENAME):
        usertokens = load_config(TOKEN_FILENAME)
    if usertokens == None:
        usertokens = {"tokens" : []}
    return usertokens


def main():
    print("Navigate to https://flow.polar.com/oauth2/authorization?response_type=code&client_id={}".format(config['client_id']))
    server = HTTPServer(('localhost', CALLBACK_PORT), OAuthCallbackHandler)
    server.serve_forever()

if __name__ == "__main__":
    main()