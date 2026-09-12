from datetime import datetime, timezone, timedelta
from collections import OrderedDict
import discord
import logging
# other module
import areas
import eq_map
import os
from time import monotonic

# P2Pquake timestamps are Japan Standard Time (no DST).
JST = timezone(timedelta(hours=9))

# import .env
from dotenv import load_dotenv
load_dotenv()

def envInt(name, default):
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default

MIN_MENTION_SCALE = envInt("MIN_MENTION_SCALE", 50)
# Prefer MIN_NOTIFY_SCALE; keep MIN_NORTIFY_SCALE as a compatibility alias.
MIN_NOTIFY_SCALE = envInt("MIN_NOTIFY_SCALE", envInt("MIN_NORTIFY_SCALE", 30))
USERQUAKE_COOLDOWN_SEC = envInt("USERQUAKE_COOLDOWN_SEC", 300)
SEEN_EVENT_LIMIT = envInt("SEEN_EVENT_LIMIT", 1000)

# area_code -> last notified monotonic time
_last_userquake_by_area = {}
# event id -> None (insertion-ordered for eviction)
_seen_event_ids = OrderedDict()

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
    # P2Pquake timestamps are Japan local time without an offset.
    if not time_str or time_str == '不明':
        return discord.utils.utcnow()
    for fmt in ("%Y/%m/%d %H:%M:%S.%f", "%Y/%m/%d %H:%M:%S"):
        try:
            return datetime.strptime(time_str, fmt).replace(tzinfo=JST)
        except ValueError:
            continue
    return discord.utils.utcnow()

def isDuplicateEvent(event_id):
    if not event_id:
        return False
    if event_id in _seen_event_ids:
        return True
    _seen_event_ids[event_id] = None
    while len(_seen_event_ids) > SEEN_EVENT_LIMIT:
        _seen_event_ids.popitem(last=False)
    return False

def isUserquakeInCooldown(area_code):
    last = _last_userquake_by_area.get(area_code)
    return last is not None and (monotonic() - last) < USERQUAKE_COOLDOWN_SEC

def markUserquakeNotified(area_code):
    if area_code is None:
        return
    _last_userquake_by_area[area_code] = monotonic()

def formatUserquake(logger: logging.Logger, data):
    area_code = data.get('area')
    if area_code is None:
        logger.warning(f"561 missing area. detail:{data}")
        return ( None, None, False )

    if isUserquakeInCooldown(area_code):
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
        mapFile = eq_map.createMap(logger, area['lat'], area['lon'])

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
        
        # check need to notification
        if max_scale_code < MIN_NOTIFY_SCALE:
            return ( None, None, False )

        max_scale_str = scaleToString(max_scale_code)

        time_str = eq.get('time', '不明')

        latitude = hypo.get('latitude', -1)
        longitude = hypo.get('longitude', -1)

        if latitude < 0 or longitude < 0:
            return ( None, None, False )

        logger.debug("get properties done.")

        mapFile = eq_map.createMap(logger, latitude, longitude)

        # create embed
        color = discord.Color.blue()
        if max_scale_code >= 50: # upper 5 or higher
            color = discord.Color.red()
        elif max_scale_code >= 40: # lower 4 or below
            color = discord.Color.orange()

        mention = True if max_scale_code >= MIN_MENTION_SCALE or code == 556 else False
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
    if code == 554:
        # EEWDetection: top-level type like "Full" / "Chime ..."
        logger.info(
            f"received EEW detection. code:554 type:{data.get('type')} detail:{data}"
        )
        return ( None, None, False )
    else:
        return ( None, None, False )
