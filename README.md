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

1. Create a `.env` file in the project root. See **Environment variables** below for all options.
    ```
    TOKEN="<your Discord bot token>"
    CHANNEL_ID="1234567890"
    WS_URI="wss://api-realtime-sandbox.p2pquake.net/v2/ws"
    LOGGING_LEVEL="INFO"
    MIN_NORTIFY_SCALE=30
    MIN_MENTION_SCALE=50
    USERQUAKE_COOLDOWN_SEC=300
    ```
1. Run `build.sh` in the root directory to build the Dockerfile.
1. Running `up.sh` in the root directory starts Docker.
1. It automatically connects to the server and verifies that the bot is participating.
1. To stop, run `down.sh` in the root directory.

### Environment variables

| Variable | Required | Description |
|---|---|---|
| `TOKEN` | Yes | Discord bot token. |
| `CHANNEL_ID` | Yes | Discord channel ID used for alerts. |
| `WS_URI` | Yes | P2Pquake WebSocket endpoint. Use `wss://api-realtime-sandbox.p2pquake.net/v2/ws` for sandbox testing, or `wss://api.p2pquake.net/v2/ws` for production. |
| `LOGGING_LEVEL` | No | Log level: `DEBUG`, `INFO`, `WARNING`, or `ERROR`. Defaults to `WARNING` if unset or unrecognized. |
| `MIN_NORTIFY_SCALE` | Yes (for 551/556) | Minimum max-intensity code required to post an earthquake / EEW alert. Events below this value are ignored. Note the spelling `NORTIFY`. |
| `MIN_MENTION_SCALE` | Yes (for 551/556) | Minimum max-intensity code required to mention `@everyone`. EEW alerts (`code` 556) always mention. |
| `USERQUAKE_COOLDOWN_SEC` | No | Cooldown in seconds before another userquake (`code` 561) alert is posted for the **same area**. Default: `300`. |

Intensity codes used by `MIN_NORTIFY_SCALE` / `MIN_MENTION_SCALE`:

| Code | Intensity |
|---|---|
| `10` | 1 |
| `20` | 2 |
| `30` | 3 |
| `40` | 4 |
| `45` | 5- |
| `50` | 5+ |
| `55` | 6- |
| `60` | 6+ |
| `70` | 7 |