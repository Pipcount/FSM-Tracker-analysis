from utils import load_config, token_db
from accesslink import AccessLink
import json
import time

CONFIG_FILENAME = "config.yml"
TOKEN_FILENAME = "usertokens.yml"
DATA_FOLDER = "data"

config = load_config(CONFIG_FILENAME)
tokens = token_db(TOKEN_FILENAME)
accesslink = AccessLink(client_id=config['client_id'],
                        client_secret=config['client_secret'])

print(tokens)

def get_exercises(token):
    transaction = accesslink.training_data.create_transaction(user_id=token["user_id"],
                                                                    access_token=token["access_token"])
    if not transaction:
        print("No new exercises available.")
        return

    resource_urls = transaction.list_exercises()["exercises"]
    exercise_summary_list = []
    for url in resource_urls:
        exercise_summary = transaction.get_exercise_summary(url)
        exercise_summary_list.append(exercise_summary)

        print("Exercise summary:", exercise_summary)

    transaction.commit()
    return exercise_summary_list

def get_daily_activity(token):
    transaction = accesslink.daily_activity.create_transaction(user_id=token["user_id"],
                                                                    access_token=token["access_token"])
    if not transaction:
        print("No new daily activity available.")
        return

    resource_urls = transaction.list_activities()["activity-log"]

    activity_summary_list = []
    for url in resource_urls:
        activity_summary = transaction.get_activity_summary(url)
        activity_summary_list.append(activity_summary)

        print("Activity summary:", activity_summary)

    transaction.commit()
    return activity_summary_list

def get_physical_info(token):
    transaction = accesslink.physical_info.create_transaction(user_id=token["user_id"],
                                                                    access_token=token["access_token"])
    if not transaction:
        print("No new physical information available.")
        return

    resource_urls = transaction.list_physical_infos()["physical-informations"]

    physical_info_list = []
    for url in resource_urls:
        physical_info = transaction.get_physical_info(url)
        physical_info_list.append(physical_info)

        print("Physical info:", physical_info)

    transaction.commit()
    return physical_info_list

data = {}

for token in tokens["tokens"]:
    available_data = accesslink.pull_notifications.list()
    if not available_data:
        print("No data available")
        continue


    token_data = {}
    for item in available_data["available-user-data"]:
        if item["data-type"] == "EXERCISE":
            token_data["exercises"] = get_exercises(token)
        elif item["data-type"] == "ACTIVITY_SUMMARY":
            token_data["daily_activity"] = get_daily_activity(token)
        elif item["data-type"] == "PHYSICAL_INFORMATION":
            token_data["physical_info"] = get_physical_info(token)

    user_data = accesslink.get_userdata(token["user_id"], token["access_token"])
    token_data["user_data"] = user_data
    data[token["user_id"]] = token_data

filename = "{}.json".format(time.strftime("%Y%m%d-%H%M%S"))
with open(DATA_FOLDER + "/" + filename, "w") as f:
    json.dump(data, f, indent=4)

print("Data saved to", DATA_FOLDER + "/" + filename)