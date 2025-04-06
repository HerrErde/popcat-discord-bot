# How to use

[![Try in PWD](https://github.com/play-with-docker/stacks/raw/cff22438cb4195ace27f9b15784bbb497047afa7/assets/images/button.png)](http://play-with-docker.com?stack=https://raw.githubusercontent.com/HerrErde/popcat-discord-bot/master/docker/docker-compose.yml)

## Using an external database

By default, Mystatus uses SQLite for data storage but it is possible toconnect to an existing MySQL/MariaDB, MongoDB or PostgreSQL database.
You can also link a database container, e. g. `--link my-mysql:db`, and then use `db` as the database host on setup.
More info is in the docker-compose section.

## Configuration via environment variables

- `TOKEN` will set the Discord Bot TOKEN
- `DEBUG` will enable debug mode like bot reload
- `SHARDING` will enable sharding of the bot (recommended to enable at 1000 guilds)
- `AUTO_SHARD` will enable sharding if the bot is in 1000 or more guilds by the next restart
- `OWNER_USER_IDS` set the owner ids that should have a access to the owner commands
- `OWNER_GUILD_IDS` set the owner guild ids that have the owner commands registered
- `API_URL` is the popcat api url
- `TIMEZONE` will set your Timezone
- `REDDIT_ID` the reddit application id is for the Reddit module
- `REDDIT_SECRET` the reddit application secret
- `CHATBOT_ENABLE` if you want to enable the chatbot
- `BRAINSHOP_APIKEY`
- `BRAINSHOP_ID`
- `REDIS_HOST` the redis host
- `REDIS_PORT` the redis port
- `REDIS_DB` 
- `REDIS_USER` the redis user
- `REDIS_PASS` the redis password
- `MONGODB_HOST` the mongodb host
- `MONGODB_USER` the mongodb user
- `MONGODB_PASS` the mongodb password
- `MONGODB_CLUSTER` use when using the mongodb database of cloud.mongodb.com
- `VOTING_ENABLE` if you want to enable the Voting Modules
- `VOTING_DELAY` set the delay of each request (recommended to change when small amount of guilds, or higher votes are expected)
- `VOTING_HOOK` if true it will initailize the webhook method for the rewards, if not (recommended when many votes are expected)
- `VOTING_KEY` is for the auth of top.gg
- `VOTING_PORT` is the port of the websocket for the rewards (has to be a public facing ip or domain)
- `TODO_WEB` is if you want to enable the Todo website
- `TODO_WEB_PORT` the port of the web todo list
- `OAUTH2_CLIENT_ID` the id of the web todo list auth client
- `OAUTH2_CLIENT_SECRET` the secret of the web todo list auth client
- `FLASK_SECRET_KEY` a flask secret [https://jwtsecret.com](https://jwtsecret.com/generate)
- `OAUTH2_REDIRECT_URI` the callback url for the web todo list (has to be the same in the discord application)


### Voting

If you choose `VOTING_HOOK` you need to expose tbr bot to the internet with the port
In Docker you can do this with couldflare tunnels (this requires a domain)
If run local you can use [ngrok.com](https://ngrok.com) or [localhosr.run](https://localhost.run)

Set the you will need yor top.gg auth token
the endpoint will be `localhost:80/websocket`

If you did not choose the websocket way




# Todo Web

if you want to be able to view and edit your Todo list from a website
enable `TODO_WEB` choose a port with `TODO_WEB_PORT` and expose it to the internet
rest is self explained




### Redis

- `REDIS_HOST` (not set by default) Name of Redis container or domain
- `REDIS_PORT` (default: `6379`) Optional port for Redis, only use for external Redis servers that run on non-standard ports.
- `REDIS_USER` (no default)
- `REDIS_PASS` (no default)







## Running with docker-compose

The easiest way to get a fully functional setup is using a `docker-compose` file. There are too many different possibilities to setup your system.
When you want to have your server reachable from the internet, adding HTTPS-encryption is mandatory!

Make sure to pass in values for `MYSQL_ROOT_PASSWORD` and `MYSQL_PASS` variables before you run this setup.

```yaml
version: '3.9'

volumes:
  redis-data:
  mongo-data:


```

Then run `docker-compose up -d`, now you can access MyStatus at <http://localhost:6090/> from your host system.