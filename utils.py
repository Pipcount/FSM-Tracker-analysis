import yaml
from genericpath import exists


def load_config(filename):
    """Load configuration from a yaml file"""
    with open(filename) as f:
        return yaml.full_load(f)


def save_config(config, filename):
    """Save configuration to a yaml file"""
    with open(filename, "w+") as f:
        yaml.safe_dump(config, f, default_flow_style=False)

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

def token_db(token_filename):
    usertokens = None
    if exists(token_filename):
        usertokens = load_config(token_filename)
    if usertokens == None:
        usertokens = {"tokens" : []}
    return usertokens