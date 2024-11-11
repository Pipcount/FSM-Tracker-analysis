# FSM-Tracker-analysis
Recover data from users via Garmin and Polar API's and add them to a database with visualization to help researchers

### Sources :
[accesslink](accesslink) is from https://github.com/polarofficial/accesslink-example-python


### Setup:
Make a config.yml file in the root directory with the following content:
```yaml
client_id: "your_client_id"
client_secret: "your_client_secret"
influxdb:
    url: "http://influxdb:8086"
    token: "your_influxdb_token"
    org: "your_influxdb_org"
    bucket: "your_influxdb_bucket"
``` 
Authenticate the users using the following command:
```bash
python3 polar_user_auth.py
```
Then follow the link presented in the terminal end connect to the wanted Polar account.

You need to do this for each user you want to track.

This will create a file named `usertokens.yml` in the root directory.

Once you have authenticated all the users you want to track, you can run the docker container.
### How to run:

```bash
docker build -t fsm-tracker-analysis .
docker run --rm -it -v $(pwd)/docker_data:/app/data fsm-tracker-analysis
```