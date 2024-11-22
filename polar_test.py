from utils import load_config, token_db
from accesslink import AccessLink
import json, time
from datetime import datetime, timedelta
from isodate import parse_duration
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

CONFIG_FILENAME = "config.yml"
TOKEN_FILENAME = "usertokens.yml"
DATA_FOLDER = "data"

config = load_config(CONFIG_FILENAME)
tokens = token_db(TOKEN_FILENAME)
accesslink = AccessLink(client_id=config['client_id'],
                        client_secret=config['client_secret'])
influx_client = InfluxDBClient(url=config['influxdb']['url'], token=config['influxdb']['token'], org=config['influxdb']['org'])
write_api = influx_client.write_api(write_options=SYNCHRONOUS)

def get_exercises(token):
    transaction = accesslink.training_data.create_transaction(user_id=token["user_id"],
                                                                    access_token=token["access_token"])
    if not transaction:
        print("No new exercises available.")
        return

    resource_urls = transaction.list_exercises()["exercises"]
    print("Exercise urls: ", resource_urls)
    exercise_list = []
    for url in resource_urls:
        exercise_summary = transaction.get_exercise_summary(url)
        heart_rate_zones = transaction.get_heart_rate_zones(url)
        available_samples = transaction.get_available_samples(url)
        samples = []
        if available_samples:
            samples = [transaction.get_samples(sample) for sample in available_samples["samples"]]
        exercise = {"exercise_summary": exercise_summary, "heart_rate_zones": heart_rate_zones, "samples": samples}
        exercise_list.append(exercise)


    transaction.commit()
    return exercise_list

def get_daily_activity(token):
    transaction = accesslink.daily_activity.create_transaction(user_id=token["user_id"],
                                                                    access_token=token["access_token"])
    if not transaction:
        print("No new daily activity available.")
        return

    resource_urls = transaction.list_activities()["activity-log"]
    print("daily activity urls: ", resource_urls)

    activity_list = []
    for url in resource_urls:
        activity_summary = transaction.get_activity_summary(url)
        date = activity_summary["date"]
        step_samples = transaction.get_step_samples(url)
        for sample in step_samples["samples"]:
            if sample.get("steps") is None: # Samples without steps are in the future
                continue
            timestamp = "{}T{}Z".format(date, sample["time"])
            point = Point("Steps") \
                .tag("user_id", token["user_id"]) \
                .field("steps", sample["steps"]) \
                .time(timestamp, WritePrecision.NS)
            write_api.write(bucket=config['influxdb']['bucket'], record=point)
        zone_samples = transaction.get_zone_samples(url)
        activity = {"activity_summary": activity_summary, "step_samples": step_samples, "zone_sample": zone_samples}
        activity_list.append(activity)

    transaction.commit()
    return activity_list

def get_physical_info(token):
    transaction = accesslink.physical_info.create_transaction(user_id=token["user_id"],
                                                                    access_token=token["access_token"])
    if not transaction:
        print("No new physical information available.")
        return

    resource_urls = transaction.list_physical_infos()["physical-informations"]
    print("physical info urls: ", resource_urls)
    
    physical_info_list = []
    for url in resource_urls:
        physical_info = transaction.get_physical_info(url)
        physical_info_list.append(physical_info)

    transaction.commit()
    return physical_info_list

def insert_calories(activity, user_id):
    calories = activity["activity_summary"]["calories"]
    timestamp = "{}T00:00:00Z".format(activity["activity_summary"]["date"])
    point = Point("Calories") \
        .tag("user_id", user_id) \
        .field("calories", calories) \
        .time(timestamp, WritePrecision.NS)
    write_api.write(bucket=config['influxdb']['bucket'], record=point)

def insert_active_calories(activity, user_id):
    active_calories = activity["activity_summary"]["active-calories"]
    timestamp = "{}T00:00:00Z".format(activity["activity_summary"]["date"])
    point = Point("Active_Calories") \
        .tag("user_id", user_id) \
        .field("active_calories", active_calories) \
        .time(timestamp, WritePrecision.NS)
    write_api.write(bucket=config['influxdb']['bucket'], record=point)

def insert_active_steps(activity, user_id):
    acive_steps  = activity["activity_summary"]["active-steps"]
    timestamp = "{}T00:00:00Z".format(activity["activity_summary"]["date"])
    point = Point("Active_Steps") \
        .tag("user_id", user_id) \
        .field("active_steps", acive_steps) \
        .time(timestamp, WritePrecision.NS)
    write_api.write(bucket=config['influxdb']['bucket'], record=point)

def insert_steps(activity, user_id):
    for step_sample in activity["step_samples"]["samples"]:
        if step_sample.get("steps") is None:
            continue
        timestamp = "{}T{}Z".format(activity["activity_summary"]["date"], step_sample["time"])
        point = Point("Steps") \
            .tag("user_id", user_id) \
            .field("steps", step_sample["steps"]) \
            .time(timestamp, WritePrecision.NS)
        write_api.write(bucket=config['influxdb']['bucket'], record=point)

def insert_hr_zones(activity, user_id):
    for zone_sample in activity["zone_sample"]["samples"]:
        timestamp = "{}T{}Z".format(activity["activity_summary"]["date"], zone_sample["time"])
        for zone in zone_sample["activity-zones"]:
            time_in_zone = parse_duration(zone["inzone"]).total_seconds()
            point = Point("HR_Zones") \
                .tag("user_id", user_id) \
                .tag("zone-idx", zone["index"]) \
                .field("in_zone_seconds", time_in_zone) \
                .time(timestamp, WritePrecision.NS)
            write_api.write(bucket=config['influxdb']['bucket'], record=point)

def insert_continuous_hr(hr_data, user_id):
    date = hr_data["date"]
    for hr_sample in hr_data["heart_rate_samples"]:
        timestamp = "{}T{}Z".format(date, hr_sample["sample_time"])
        point = Point("Continuous_HR") \
            .tag("user_id", user_id) \
            .field("heart_rate", hr_sample["heart_rate"]) \
            .time(timestamp, WritePrecision.NS)
        write_api.write(bucket=config['influxdb']['bucket'], record=point)



def insert_influx(data, user_id):
    for data_type in data:
        if data[data_type] is None:
                continue
        if data_type == "daily_activity":
            for activity in data[data_type]:
                insert_steps(activity, user_id)
                insert_hr_zones(activity, user_id)
                insert_calories(activity, user_id)
                insert_active_calories(activity, user_id)
                insert_active_steps(activity, user_id)
        elif data_type == "continuous_hr":
            if data[data_type]["heart_rates"]:
                insert_continuous_hr(data[data_type]["heart_rates"][0], user_id)

def main():
    data = {}

    for token in tokens["tokens"]:
        available_data = accesslink.pull_notifications.list()
        if not available_data:
            print("No data available")
            continue

        yesterday = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')
        data[token["user_id"]] = {
            "exercises": get_exercises(token),
            "daily_activity": get_daily_activity(token),
            "physical_info": get_physical_info(token),
            "sleep": accesslink.get_sleep(token["access_token"]),
            "recharge": accesslink.get_recharge(token["access_token"]),
            "continuous_hr": accesslink.get_continuous_hr(from_time=yesterday, to_time=yesterday, access_token=token["access_token"]),
            "user_data": accesslink.get_userdata(token["user_id"], token["access_token"])
        }
        print("Data for user", token["user_id"], "collected")
        if data[token["user_id"]] is not None:
            insert_influx(data[token["user_id"]], token["user_id"])

    filename = "{}.json".format(time.strftime("%Y%m%d-%H%M%S"))
    with open(DATA_FOLDER + "/" + filename, "w") as f:
        json.dump(data, f, indent=4)

    print("Data saved to", DATA_FOLDER + "/" + filename)

if __name__ == "__main__":
    main()