from discord_webhook import DiscordWebhook, DiscordEmbed
import json
import datetime as dt
import requests
import time
import webbrowser
import discord
import asyncio
import pandas as pd
from geopy.geocoders import Nominatim
from discord.ext import commands

# Constants that need to be changed
DISCORD_WEBHOOK_URL = {DISCORD_WEBHOOK_URL}
TOKEN = {DISCORD_TOKEN_HERE}
CHANNEL = {CHANNEL_ID}
# 'ResyAPI api_key=xxx
RESY_API = {RESY_AUTHORIZATION_KEY}
GOOGLE_MAPS_API = {GOOGLE_MAPS_API_KEY}
# Constant - optional to change
DELAY = 10

# Global variables
venue, place, urlSlug, cityCode = None, None, None, None
lat, lng = None, None
confirmedPlace = False


async def getCoords(location):
    # geocode used to find longitude and latitude
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={location}&key={GOOGLE_MAPS_API}"
    request = requests.get(url, headers={})
    data = json.loads(request.text)
    if data['status'] == "ZERO_RESULTS":
        return False, "", ""
    lat = str(data["results"][0]["geometry"]["location"]["lat"])
    lng = str(data["results"][0]["geometry"]["location"]["lng"])
    return True, lat, lng


async def findCity(city):
    global lat, lng
    geolocator = Nominatim(user_agent="MyApp")
    url = f"https://maps.googleapis.com/maps/api/place/autocomplete/json?input={city}&key={GOOGLE_MAPS_API}&types=(cities)"
    response = requests.request("GET", url, headers={}, data={})
    status = json.loads(response.text)["status"]
    if status == "ZERO_RESULTS":
        print(f"{city} CANNOT BE FOUND VIA GOOGLE MAPS!")
        return False, ""
    else:
        prediction = json.loads(response.text)[
            'predictions'][0]
        city = prediction["description"]
        print(city)
        location = geolocator.geocode(city)
        lat = location.latitude
        lng = location.longitude
        print("The latitude of the location is: ", location.latitude)
        print("The longitude of the location is: ", location.longitude)
        return True, city


async def findPlace(restaurant):
    global lat, lng
    restaurant = '-'.join(restaurant.split())
    # autocomplete using google maps geocode api
    # strictly 25 mile radius of city --> circle:radius@lat, lng
    print(lat)
    print(lng)
    url = f"https://maps.googleapis.com/maps/api/place/autocomplete/json?input={restaurant}&locationrestriction=circle:40233.6@{lat},{lng}&strictbounds=true&key={GOOGLE_MAPS_API}&types=restaurant|cafe|bakery|food"
    response = requests.request("GET", url, headers={}, data={})
    status = json.loads(response.text)["status"]

    # status will be whether or not the google maps autocompletion successfully found the restaurant
    if status == "ZERO_RESULTS":
        print(f"{restaurant} CANNOT BE FOUND VIA GOOGLE MAPS!")
        return False
    else:
        prediction = json.loads(response.text)['predictions'][0]
        # even if the prediction is made, need to ensure the place is actually on Resy
        global place
        place = prediction['structured_formatting']['main_text']
        found = await getVenueID(prediction)
        print("FOUND:---------------------------------------------  ", found)
        if not found:
            return False
        successPrediction(prediction)
        return True


def successPrediction(prediction):
    restaurant = prediction['structured_formatting']['main_text']
    description = prediction['description']
    title = f"{restaurant.upper()} FOUND!\n\nPlease confirm by messaging 'yes' or 'no'.\nYou may also react below!"
    sendWebhook(title, description, "Success", 0x2ecc71)


async def getVenueID(prediction):
    global venue, place
    # look for place on google maps api by location with description
    desc = prediction["description"]
    print(f"FINDING VENUE ID FOR {desc}.", dt.datetime.now())
    found, lat, lng = await getCoords(desc)
    if not found:
        return False
    headers = {
        "authorization": RESY_API,
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
    }
    params = {
        "lat": lat,
        "long": lng,
        "day": str(dt.datetime.now())[:10],
        "party_size": 2
    }
    request = requests.get("https://api.resy.com/4/find",
                           params=params, headers=headers)

    # multiple venue could be in the same location by coordinates (ie: food courts)
    data = json.loads(request.text)["results"]["venues"]
    name = ""
    for i in range(len(data)):
        name = data[i]["venue"]["name"]
        # need to match place name with venue name
        if name.lower() == prediction['structured_formatting']['main_text'].lower():
            venue = str(data[i]["venue"]["id"]["resy"])
            print("VENUE ID: ------------------------", venue, ' - ', name)
            print("FOUND VENUE ID", dt.datetime.now())
            print()
            break
    # if no names match, return False
    else:
        return False

    params["venue_id"] = venue
    getParams(params, headers)
    return True


def getParams(params, headers):
    print("FINDING SLUG AND CITY CODE", dt.datetime.now())
    global urlSlug, cityCode
    request = requests.get("https://api.resy.com/4/find",
                           params=params, headers=headers)
    data = json.loads(request.text)["results"]["venues"][0]["venue"]
    urlSlug = data["url_slug"]
    cityCode = data["location"]["code"]
    print("URL SLUG: --------------------------", urlSlug)
    print("CITY CODE: --------------------------", cityCode)
    print("FOUND SLUG", dt.datetime.now())


def sendWebhook(title, description, status, color):
    print("Sent webhook!")
    webhook = DiscordWebhook(url=DISCORD_WEBHOOK_URL)
    embed = DiscordEmbed(title=title, description=description, color=color)
    embed.set_author(
        name=f"Resy {status}!",
        icon_url="https://pbs.twimg.com/profile_images/1111645642881941504/qW8aVGFm_400x400.png"
    )
    webhook.add_embed(embed)
    webhook.execute()


async def reserve(seats, venue, dates):
    headers = {
        "authorization": RESY_API,
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
    }
    params = {
        "venue_id": venue,
        "num_seats": seats,
        "start_date": dates[0],
        "end_date": dates[-1]
    }
    while True:
        print("WAITING FOR RESERVATION!")
        request = requests.get(
            "https://api.resy.com/4/venue/calendar", params=params, headers=headers)
        print(f"{dt.datetime.now()} : Request Made.")
        data = json.loads(request.text)['scheduled']
        print(data)
        print("-------------------------------------")
        for day in data:
            correctDate = True if day['date'] in dates else False
            available = True if day['inventory']['reservation'] == "available" else False
            if (correctDate and available):
                print(day)
                return openResy(day['date'], seats)
        time.sleep(DELAY)


def openResy(date, seats):
    global urlSlug, cityCode, place
    webhook = DiscordWebhook(url=DISCORD_WEBHOOK_URL)
    link = f"https://resy.com/cities/{cityCode}/{urlSlug}?date={date}&seats={seats}"
    embed = DiscordEmbed(
        title=f"**{place} RESERVATION FOUND!\n**", description=link, color=0x2ecc71)
    embed.set_footer(text=str(dt.datetime.now()))
    webbrowser.open(link)
    webhook.add_embed(embed)
    webhook.execute()
    return


def runDiscordBot():
    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f"{client.user} is now running!")
        channel = client.get_channel(CHANNEL)
        await addLine(channel)
        await channel.send(">>>**__Hello, this is a bot to help you monitor available reservation for your desired restaurant!__**\nYou may type **!restart** or **!stop** at any time to restart or stop the bot.")
        await cityResponse(channel)

    @client.event
    async def on_message(message):
        global venue, confirmedPlace
        # to prevent loop messaging itself
        if message.author == client.user or str(message.author) == "Resy Webhook#0000":
            if str(message.author) == "Resy Webhook#0000":
                channel = message.channel
                global confirmedPlace
                if not confirmedPlace:
                    print("ADDING REACTIONS!")
                    flag = await confirmationMessage(message, channel)
                    if flag == 1:
                        confirmedPlace = True
                        await guestsResponse(channel)
                    elif flag == 2:
                        await channel.send(">>>Sorry, can you please specify the restaurant you are looking for?\n** **")
                        await restaurantResponse(channel)
            return
        username = str(message.author)
        userMessage = str(message.content).lower()
        channel = client.get_channel(CHANNEL)
        print(f"{username} said: {userMessage} in {channel}.")
        if userMessage == 'cool':
            await message.add_reaction('\U0001F60E')
        if userMessage == "!stop":
            await channel.send(">>>__**Stopping the bot.**__")
            exit()
        if userMessage == "!start":
            await channel.send(">>>__**Restarting bot to find a new restaurant!**__")
            confirmedPlace = False
            await cityResponse(channel)

    async def cityResponse(channel):
        await addLine(channel)
        await channel.send(f">>>**Please enter the city you would like to search in.**")
        try:
            message = await client.wait_for("message", timeout=60.0)
        except asyncio.TimeoutError:
            await timeError(channel)
        else:
            flag, city = await findCity(message.content)
            if flag:
                print("City has been found and coordinates have been set.")
                botMsg = await channel.send(f"Is the city you are looking for: **{city}**?\n**Please respond with a 'Yes' or 'No'.\nReactions also work!**")
                flag = await confirmationMessage(botMsg, channel)
                # 1 = yes, 2 = no
                if flag == 1:
                    await restaurantResponse(channel)
                elif flag == 2:
                    await channel.send(f"**Sorry, can you please specify the city you are looking for?**")
                    await cityResponse(channel)
            else:
                await channel.send(f"**{message.content}** is not a city that could be found according to Google Maps.")
                await cityResponse(channel)

    # get restaurant name and check if on resy
    async def restaurantResponse(channel):
        await addLine(channel)
        await channel.send(f">>>__Searching for restaurant.__\n**Please enter the restaurant name you would like to look up on Resy.**")
        try:
            message = await client.wait_for("message", timeout=60.0)
        except asyncio.TimeoutError:
            await timeError(channel)
        try:
            global place, venue
            place = str(message.content)
            print("TRYING TO FIND RESTAURANT")
            await channel.send(f">>>__Checking if **{place}** exists on Resy.__\nPlease wait a few seconds.")
            found = await findPlace(place)
            if not found:
                await channel.send(f"** **\n**{place}** could not be found on Resy.\n** **")
                await restaurantResponse(channel)
        except Exception as e:
            print("An error has occured:", e)

    # add reactions and wait for user confirmation through reaction or text response
    async def confirmationMessage(message, channel):
        await message.add_reaction('\U00002705')
        await message.add_reaction('\U0000274C')
        tasks = [
            asyncio.create_task(client.wait_for(
                "message", timeout=60.0
            ), name="msg"),
            asyncio.create_task(client.wait_for(
                "reaction_add", timeout=60.0
            ), name="react")
        ]
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED, timeout=60.0)

        # empty set if no reaction or message from user in 60 secs
        if not done:
            await timeError(channel)

        for task in pending:
            try:
                task.cancel()
            except asyncio.CancelledError:
                pass

        finished: asyncio.Task = list(done)[0]
        result = finished.result()
        action = finished.get_name()
        flag = 0
        if action == "react":
            # if reaction, a tuple is returned
            reaction, user = result
            if str(reaction) == "✅":
                print("CHECK")
                flag = 1
            elif str(reaction) == "❌":
                print("DENY")
                flag = 2
            print(f"{user} has sent {reaction} emoji.")
        elif action == "msg":
            # create message variable of type discord.Message
            msg: discord.Message = result
            if msg.content.lower() == "yes":
                flag = 1
            elif msg.content.lower() == "no":
                flag = 2
            print(f"{msg.author} has sent '{msg.content}' message.")

        if flag == 0:
            msg = await channel.send(message.content)
            return await confirmationMessage(msg, channel)
        else:
            return flag

    async def guestsResponse(channel):
        await addLine(channel)
        await channel.send(">>>__Confirmed restaurant!__\n\n**How many guest(s) would you like to reserve for? \nPlease enter using numbered digits, ie: 2**")
        try:
            message = await client.wait_for("message", timeout=60.0)
        except asyncio.TimeoutError:
            await timeError(channel)
        else:
            userMessage = message.content
            if userMessage.isdigit():
                await channel.send(
                    f">>>__Confirmed: **{userMessage}** guest(s).__"
                )
                await datesResponse(channel, userMessage)
            else:
                await channel.send("**Please enter a valid number.**\n** **")
                await guestsResponse(channel)

    async def datesResponse(channel, guests):
        await addLine(channel)
        await channel.send("**What date(s) would you like to reserve for?**\nIf multiple dates, please separate with **commas**\nIf entering a range, use a **hpyhen** '**-**' between the starting and ending date (inclusive) with the same date format like so, ie: 4/28/23 - 12/27/23\n\n**Enter using the format of MM/DD/YY, ie: 2/6/23, 4/28/23, 12/27/23**")
        try:
            message = await client.wait_for("message", timeout=180.0)
        except asyncio.TimeoutError:
            await timeError(channel)
        else:
            dates = []
            userMessage = message.content.replace(',', '').split()
            print(userMessage)
            increment = 1
            try:
                # hypen in message means it's a range
                if len(userMessage) == 3:
                    if userMessage[1] == '-':
                        increment = 2
                for i in range(0, len(userMessage), increment):
                    month, day, year = userMessage[i].split('/')
                    try:
                        date = dt.datetime(
                            2000 + int(year), int(month), int(day))
                        print(type(date))
                        dates.append(str(date)[:10])
                    except ValueError:
                        print("Error, date is not valid")
                        await channel.send(">>>**Please enter a valid date(s).**\n** **")
                        await datesResponse(channel, 2)
            except Exception as e:
                print(e)
                await channel.send(">>>**Please enter valid date(s).**")
                await datesResponse(channel, 2)

            # used pandas time series to convert range to dates
            if increment == 2:
                db = pd.date_range(start=dates[0], end=dates[-1])
                for i in range(1, len(db) - 1):
                    dates.append(str(db[i])[:10])
            await channel.send(f">>>__Searching for available reservation(s) for **{place}**.__")
            await reserve(guests, venue, dates)
            await addLine(channel)
            await channel.send("**Congratulations on finding your reservation!**\nHope you were able to reserve it. Autocompleting the reservation is currently in development.\n>>>**Please restart the bot by typing __!start__ to search for a new restaurant!\nYou may also stop the bot by typing __!stop__.**")
            await addLine(channel)
            # exit()

    async def timeError(channel):
        await addLine(channel)
        await channel.send("__**Restarting bot. User took too long to respond.**__")
        await cityResponse(channel)

    async def addLine(channel):
        await channel.send("---------- ---------- ---------- ---------- ---------- ---------- ")

    client.run(TOKEN)


def main():
    print(dt.datetime.now())
    runDiscordBot()
    print(dt.datetime.now())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(e)
        pass
