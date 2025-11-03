## Neko EEW for Discord
Thanks for finding me! I'm [sasami](http://x.com/sasami989).

nekoeewbot is an emergency earthquake alert bot for Discord servers using [P2P earthquake information](https://www.p2pquake.net/) and [JMA](https://www.jma.go.jp/jma/index.html).

The map uses [GSI Map Tiles](https://maps.gsi.go.jp/development/ichiran.html)

This bot is for Japan only.

The EEW feature is currently in beta.

It also has a few cat-themed features, so feel free to explore them.

Let's prepare a cat image for the bot's icon!

### how to setup
* [NOTICE] Please prepare your Discord server in advance and ensure it is ready for the bot to join as an application.

1. Prepare a .env file and enter the access token for the server you want the bot to join.
    ```
    TOKEN="<your server access token>"
    ```
1. Additionally, prepare the notification channel ID, the P2P earthquake information URI, and the log level.
    ```
    CHANNEL_ID="1234567890"
    WS_URI="<P2Pquake API URI>"
    LOGGING_LEVEL="INFO"
    ```
1. Run `build.sh` in the root directory to build the Dockerfile.
1. Running `up.sh` in the root directory starts Docker.
1. It automatically connects to the server and verifies that the bot is participating.
1. To stop, run `down.sh` in the root directory.