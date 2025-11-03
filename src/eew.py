from datetime import datetime
import discord
import logging
# other module
import map

def scaleToString(scaleCode):
    scale_map = {
        10: '1', 20: '2', 30: '3', 40: '4',
        45: '5弱', 50: '5強', 55: '6弱', 60: '6強', 70: '7'
    }
    return scale_map.get(scaleCode, '不明')

def formatData(logger: logging.Logger, data):
    code = data.get('code')
    logger.debug("format data started.")

    if (code == 551 or code == 556) and data.get('earthquake'):
        eq = data['earthquake']
        hypo = eq.get('hypocenter', {})

        hypo_name = hypo.get('name', '不明')
        magnitude = hypo.get('magnitude', -1)
        max_scale_code = eq.get('maxScale', -1)
        max_scale_str = scaleToString(max_scale_code)

        time_str = eq.get('time', '不明')

        latitude = hypo.get('latitude', -1)
        longitude = hypo.get('longitude', -1)

        logger.debug("get properties done.")

        mapFile = map.createMap(logger, latitude, longitude)

        logger.debug("create embed start.")

        # create embed
        mention = "<@everyone> "
        color = discord.Color.blue()
        if max_scale_code >= 50: # upper 5 or higher
            color = discord.Color.red()
        elif max_scale_code >= 40: # lower 4 or below
            color = discord.Color.orange()

        title = mention if max_scale_code >= 50 or code == 556 else ""
        title = title + "地震情報" if code == 551 else "緊急地震速報（警報）"

        date_format = "%Y/%m/%d %H:%M:%S"
        embed = discord.Embed(
            title=title,
            description=f"**最大震度: {max_scale_str}**",
            color=color,
            timestamp=datetime.strptime(time_str, date_format) if time_str != '不明' else discord.utils.utcnow()
        )

        logger.debug("embed obj created.")

        embed.add_field(name="震源地", value=hypo_name, inline=True)
        embed.add_field(name="緯度", value=latitude, inline=True)
        embed.add_field(name="経度", value=longitude, inline=True)
        embed.add_field(name="マグニチュード", value=f"M{magnitude:.1f}" if magnitude != -1 else "不明", inline=True)
        embed.set_footer(text="Created by nekoeewbot based on data from JMA and GSI Map Tiles.")
        
        logger.debug("add field done.")

        embed.set_image(url=f"attachment://{mapFile.filename}")

        logger.debug("set image done.")

        return ( embed, mapFile )
    if code == 554 and data.get('issue', {}).get('type') == 'Warning':
        logger.info(f"received Warning data. code:554 detail:{data}")
        return ( None, None )

