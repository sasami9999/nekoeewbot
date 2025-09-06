## Neko EEW for Discord
Thanks for finding me! I'm [sasami](http://x.com/sasami989).

nekoeewbot is an emergency earthquake alert bot for Discord servers using [P2P earthquake information](https://www.p2pquake.net/).

The EEW feature is currently under development and not yet available. It will be released soon.

It also has a few cat-themed features, so feel free to explore them.

### how to setup
* [NOTICE] Please prepare your Discord server in advance and ensure it is ready for the bot to join as an application.

1. Prepare a .env file and enter the access token for the server you want the bot to join.
    ```
    TOKEN=(your server access token)
    ```
1. Run `build.sh` in the root directory to build the Dockerfile.
1. Running `up.sh` in the root directory starts Docker.
1. It automatically connects to the server and verifies that the bot is participating.
1. To stop, run `down.sh` in the root directory.