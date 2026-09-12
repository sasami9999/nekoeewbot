from datetime import datetime
import discord
import logging
# other module
import areas
import map
import os
from time import monotonic

# import .env
from dotenv import load_dotenv
load_dotenv()

MIN_MENTION_SCALE=os.getenv("MIN_MENTION_SCALE")
MIN_NORTIFY_SCALE=os.getenv("MIN_NORTIFY_SCALE")
USERQUAKE_COOLDOWN_SEC=int(os.getenv("USERQUAKE_COOLDOWN_SEC", "300"))

# area_code -> last notified monotonic time
_last_userquake_by_area = {}

def scaleToString(scaleCode):
    scale_map = {
        10: '1', 20: '2', 30: '3', 40: '4',
        45: '5弱', 50: '5強', 55: '6弱', 60: '6強', 70: '7'
    }
    return scale_map.get(scaleCode, '不明')

def effectiveToString(effective):
    effect_map = {
        'None': 'なし', 'Unknown': '不明', 'Checking': '調査中', 'NonEffective': '若干の海面変動が予想されるが、被害の心配なし',
        'Watch': '津波注意報', 'Warning': '津波予報(種類不明)'
    }
    return effect_map.get(effective, '不明')

def parseTime(time_str):
    if not time_str or time_str == '不明':
        return discord.utils.utcnow()
    for fmt in ("%Y/%m/%d %H:%M:%S.%f", "%Y/%m/%d %H:%M:%S"):
        try:
            return datetime.strptime(time_str, fmt)
        except ValueError:
            continue
    return discord.utils.utcnow()

def canNotifyUserquake(area_code):
    now = monotonic()
    last = _last_userquake_by_area.get(area_code)
    if last is not None and (now - last) < USERQUAKE_COOLDOWN_SEC:
        return False
    _last_userquake_by_area[area_code] = now
    return True

def formatUserquake(logger: logging.Logger, data):
    area_code = data.get('area')
    if area_code is None:
        logger.warning(f"561 missing area. detail:{data}")
        return ( None, None, False )

    if not canNotifyUserquake(area_code):
        logger.info(
            f"skip 561 for area {area_code}: "
            f"within cooldown {USERQUAKE_COOLDOWN_SEC}s"
        )
        return ( None, None, False )

    area = areas.get_area(area_code)
    area_name = area['name'] if area else f"地域コード {area_code}"
    time_str = data.get('time', '不明')

    logger.info(f"userquake area: {area_code} ({area_name})")

    mapFile = None
    if area:
        mapFile = map.createMap(logger, area['lat'], area['lon'])

    embed = discord.Embed(
        title="地震感知情報",
        description=f"**{area_name}で揺れを感知**",
        color=discord.Color.dark_teal(),
        timestamp=parseTime(time_str)
    )
    embed.add_field(name="感知地域", value=area_name, inline=True)
    if area and area.get('pref'):
        embed.add_field(name="都道府県", value=area['pref'], inline=True)
    embed.add_field(name="地域コード", value=str(area_code), inline=True)
    embed.set_footer(text="Created by nekoeewbot based on data from P2Pquake and GSI Map Tiles.")

    if mapFile:
        embed.set_image(url=f"attachment://{mapFile.filename}")

    return ( embed, mapFile, False )

def formatData(logger: logging.Logger, data):
    code = data.get('code')
    logger.debug("---------- format data started. ----------")
    logger.info(f"code: {code}")

    if code == 561:
        return formatUserquake(logger, data)

    if (code == 551 or code == 556) and data.get('earthquake'):
        eq = data['earthquake']
        hypo = eq.get('hypocenter', {})

        hypo_name = hypo.get('name', '不明')
        magnitude = hypo.get('magnitude', -1)
        max_scale_code = eq.get('maxScale', -1)
        tsunami = effectiveToString(eq.get('domesticTsunami', 'UnKnown'))

        logger.info(f"hypo_name: {hypo_name}, magnitude: {magnitude}, max_scale_code: {max_scale_code}, tsunami: {tsunami}")
        
        # check need to notificatopn
        if max_scale_code < int(MIN_NORTIFY_SCALE):
            return ( None, None, False )

        max_scale_str = scaleToString(max_scale_code)

        time_str = eq.get('time', '不明')

        latitude = hypo.get('latitude', -1)
        longitude = hypo.get('longitude', -1)

        if latitude < 0 or longitude < 0:
            return ( None, None, False )

        logger.debug("get properties done.")

        mapFile = map.createMap(logger, latitude, longitude)

        # create embed
        color = discord.Color.blue()
        if max_scale_code >= 50: # upper 5 or higher
            color = discord.Color.red()
        elif max_scale_code >= 40: # lower 4 or below
            color = discord.Color.orange()

        mention = True if max_scale_code >= int(MIN_MENTION_SCALE) or code == 556 else False
        title = "地震情報" if code == 551 else "緊急地震速報（警報）"

        embed = discord.Embed(
            title=title,
            description=f"**最大震度: {max_scale_str}**",
            color=color,
            timestamp=parseTime(time_str)
        )

        logger.debug("embed obj created.")

        embed.add_field(name="震源地(緯度 / 経度)", value=f"{hypo_name}({latitude} / {longitude})", inline=True)
        embed.add_field(name="津波の影響", value=tsunami, inline=True)
        embed.add_field(name="マグニチュード", value=f"M{magnitude:.1f}" if magnitude != -1 else "不明", inline=True)
        embed.set_footer(text="Created by nekoeewbot based on data from JMA and GSI Map Tiles.")
        
        logger.debug("add field done.")

        if mapFile:
            embed.set_image(url=f"attachment://{mapFile.filename}")
            logger.debug("set image done.")
        else:
            logger.warning("map creation failed; sending embed without map image.")

        return ( embed, mapFile, mention )
    if code == 554 and data.get('issue', {}).get('type') == 'Warning':
        logger.info(f"received Warning data. code:554 detail:{data}")
        return ( None, None, False )
    else:
        return ( None, None, False )
