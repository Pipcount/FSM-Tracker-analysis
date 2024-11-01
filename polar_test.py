from utils import load_config, save_config, remove_oldtokens, token_db
from accesslink import AccessLink

CONFIG_FILENAME = "config.yml"
TOKEN_FILENAME = "usertokens.yml"

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

    for url in resource_urls:
        exercise_summary = transaction.get_exercise_summary(url)

        print("Exercise summary:", exercise_summary)

    transaction.commit()

def get_daily_activity(token):
    transaction = accesslink.daily_activity.create_transaction(user_id=token["user_id"],
                                                                    access_token=token["access_token"])
    if not transaction:
        print("No new daily activity available.")
        return

    resource_urls = transaction.list_activities()["activity-log"]

    for url in resource_urls:
        activity_summary = transaction.get_activity_summary(url)

        print("Activity summary:", activity_summary)

    transaction.commit()

def get_physical_info(token):
    transaction = accesslink.physical_info.create_transaction(user_id=token["user_id"],
                                                                    access_token=token["access_token"])
    if not transaction:
        print("No new physical information available.")
        return

    resource_urls = transaction.list_physical_infos()["physical-informations"]

    for url in resource_urls:
        physical_info = transaction.get_physical_info(url)

        print("Physical info:", physical_info)

    transaction.commit()


for token in tokens["tokens"]:
    available_data = accesslink.pull_notifications.list()
    print(available_data)
    if not available_data:
        print("No data available")
        continue

    for item in available_data["available-user-data"]:
        if item["data-type"] == "EXERCISE":
            get_exercises(token)
        elif item["data-type"] == "ACTIVITY_SUMMARY":
            get_daily_activity(token)
        elif item["data-type"] == "PHYSICAL_INFORMATION":
            get_physical_info(token)
