import logging
import discord
import time
import io
import math
import requests
from PIL import Image
from cairosvg import svg2png

def latLonToPixelXY(lat, lon, zoom):
    tileSize = 256
    scale = pow(2, zoom) * tileSize

    x = ((lon + 180) / 360) * scale
    latRad = lat * math.pi / 180
    y = (1 - math.log(math.tan(latRad) + 1 / math.cos(latRad)) / math.pi) / 2 * scale

    return ( x, y )


def createRedCrossSVG(logger: logging.Logger, imageSize, x_center, y_center, globalPixel):
    logger.debug("create svg start.")

    topLeftTileX = x_center - 1
    topLeftTileY = y_center - 1
    
    topLeftGlobalPixelX = topLeftTileX * 256
    topLeftGlobalPixelY = topLeftTileY * 256

    markerX = globalPixel[0] - topLeftGlobalPixelX
    markerY = globalPixel[1] - topLeftGlobalPixelY
    
    crossSVG =f'<svg width="{imageSize}" height="{imageSize}"> \
        <line x1="{markerX - 10}" y1="{markerY}" x2="{markerX + 10}" y2="{markerY}" stroke="red" stroke-width="4"/> \
        <line x1="{markerX}" y1="{markerY - 10}" x2="{markerX}" y2="{markerY + 10}" stroke="red" stroke-width="4"/> \
        </svg>'
    
    logger.debug(f"create svg end. content={crossSVG}")
    return crossSVG


def createMap(logger: logging.Logger, latitude, longitude):
    logger.debug("create map start.")

    zoom = 9
    size = 256
    tileSet = 'pale'
    tileCount = 3
    imageSize = size * tileCount

    # calculation center of map
    n = pow(2, zoom)
    x_center = math.floor((longitude + 180) / 360 * n)
    
    MAX_LAT = 85.05112878
    if latitude > MAX_LAT:
        latitude = MAX_LAT
    elif latitude < -MAX_LAT:
        latitude = -MAX_LAT
        
    latRad = latitude * math.pi / 180
    
    log_arg = math.tan(latRad) + 1 / math.cos(latRad)
    
    if log_arg <= 0:
        log_arg = 1e-10 
        
    y_center = math.floor(
        (1 - math.log(log_arg) / math.pi) / 2 * n
    )

    logger.debug("calculation done.")

    if math.nan != x_center and math.nan != y_center:
        # create cross red svg
        svg = createRedCrossSVG(logger, imageSize, x_center, y_center, latLonToPixelXY(latitude, longitude, zoom))
        
        logger.debug("get PNG and combine start.")
        combinedPng = Image.new('RGB', (imageSize, imageSize), color="white")
        # get png map
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                x = x_center + dx
                y = y_center + dy
                j = dx + 1
                i = dy + 1
                
                logger.debug(f"x_center:{x_center}, y_center:{y_center}, x:{x}, y:{y}")
                reqUrl = f'https://cyberjapandata.gsi.go.jp/xyz/{tileSet}/{zoom}/{x}/{y}.png'

                try:                    
                    response = requests.get(reqUrl, timeout=10)
                    response.raise_for_status()
                except Exception as e:
                    logger.error(f"failed get png: {e}")
                    break

                combinedPng.paste(Image.open(io.BytesIO(response.content)), (j * size, i * size))

        logger.debug("get PNG and combine end.")

        try:
            logger.debug("PNG and SVG combine start.")
            # svg to png
            svgToPng = svg2png(
                bytestring=svg.encode('utf-8'),
                output_width=imageSize,
                output_height=imageSize
            )
            pilObjSVG = Image.open(io.BytesIO(svgToPng))
            pilObjSVG = pilObjSVG.convert('RGBA')
            # combine svg to png
            combinedPng.paste(pilObjSVG, (0, 0), pilObjSVG)

            logger.debug("PNG and SVG combine end.")
        except Exception as e:
            logger.error(f"failed rendered svg: {e}")

        buffered = io.BytesIO()
        combinedPng.save(buffered, format="PNG")
        epocTime = time.time()
        buffered.seek(0)
        logger.debug("create map end.")
        return discord.File(buffered, filename=f'map_{epocTime:.0f}.png')
