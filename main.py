import os
import sys
import traceback
import aiohttp
import discord
from discord.ext import commands
from dotenv import load_dotenv
from typing import Optional
from chronically_online import keep_alive

dotenv_path = os.path.join(os.path.dirname(__file__), 'config.env')
load_dotenv(dotenv_path=dotenv_path)
TOKEN = os.getenv("TOKEN")
API_KEY = os.getenv("API_KEY")

bot = commands.Bot(command_prefix="/", intents=discord.Intents.all())

@bot.event
async def on_ready():
    print("Bot is connected.")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Invalid command. **/help** for more information.")
    else:
        print("Ignoring exception in command {}:".format(ctx.command), file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

@bot.command()
async def weather(ctx: commands.Context, *, city):
    url = "http://api.weatherapi.com/v1/current.json"
    params = {
        "key": API_KEY,
        "q": city,
        "aqi": "yes"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as responses:
            data = await responses.json()

            if "error" in data:
                error_code = data["error"]["code"]
                if error_code == 1006:
                    await ctx.send("Location not found. Please provide a valid city name.")
                else:
                    await ctx.send(f"`ERROR {error_code}`")
                return

            location = data["location"]["name"]

            temperature = round(data["current"]["temp_f"])
            condition_text = data["current"]["condition"]["text"].title()
            condition_icon = "http:" + data["current"]["condition"]["icon"]

            uv = int(data["current"]["uv"])
            precipitation = data["current"]["precip_in"]
            if precipitation == 0.0:
                precipitation = "0"

            wind = round(data["current"]["wind_mph"])
            humidity = data["current"]["humidity"]

            air_quality = data["current"]["air_quality"]["us-epa-index"]
            if air_quality == 1:
                air_quality = "Good"
            if air_quality == 2:
                air_quality = "Fair"
            if air_quality == 3 or air_quality == 4 or air_quality == 5:
                air_quality = "Bad"
            if air_quality == 6:
                air_quality = "Very Bad"

            embed = discord.Embed(title=f"**Current Weather in {location}**",
                                  description=f"**{temperature}\u00B0 | {condition_text}**")

            embed.set_thumbnail(url=condition_icon)
            embed.add_field(name="\n\n", value="", inline=False)

            embed.add_field(name="UV Index", value=f"{uv}")
            embed.add_field(name="Precipitation", value=f"{precipitation}\u201D")
            embed.add_field(name="\u200B", value="\u200B")

            embed.add_field(name="Wind", value=f"{wind} mph")
            embed.add_field(name="Humidity", value=f"{humidity}%")
            embed.add_field(name="\u200B", value="\u200B")
            embed.add_field(name="\n\n", value="", inline=False)

            embed.set_footer(text=f"Air Quality: {air_quality}")

            if data["current"]["is_day"] == 0:
                embed.color = discord.Color.from_rgb(25, 25, 75)

            if data["current"]["is_day"] == 1:
                if "sunny" in condition_text.lower():
                    embed.color = discord.Color.from_rgb(255, 185, 0)
                elif any(condition in condition_text.lower() for condition in ("mist", "fog", "cloudy", "overcast")):
                    embed.color = discord.Color.light_grey()
                elif any(condition in condition_text.lower() for condition in ("drizzle", "rain")):
                    embed.color = discord.Color.blurple()
                elif "ice" in condition_text.lower():
                    embed.color = discord.Color.from_rgb(185, 255, 255)
                elif "thunder" in condition_text.lower():
                    embed.color = discord.Color.from_rgb(255, 255, 0)
                else:
                    embed.color = discord.Color.from_rgb(255, 255, 255)

            await ctx.send(embed=embed)

@bot.command()
async def forecast(ctx: commands.Context, *, city):
    await forecast_callee(ctx, 1, city=city)

@bot.command()
async def forecast2(ctx: commands.Context, *, city):
    await forecast_callee(ctx, 2, city=city)

@bot.command()
async def forecast3(ctx: commands.Context, *, city):
    await forecast_callee(ctx, 3, city=city)

@weather.error
@forecast.error
@forecast2.error
@forecast3.error
async def MissingRequiredArgument(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Please provide a city name.")

@bot.command()
async def forecast_callee(ctx: commands.Context, days: Optional[int]=None, *, city):
    url = "http://api.weatherapi.com/v1/forecast.json"
    params = {
        "key": API_KEY,
        "days": 3,
        "q": city,
        "aqi": "yes"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as responses:
            data = await responses.json()

            if "error" in data:
                error_code = data["error"]["code"]
                if error_code == 1006:
                    await ctx.send("Location not found. Please provide a valid city name.")
                else:
                    await ctx.send(f"`ERROR {error_code}`")
                return

            location = data["location"]["name"]

            min1 = round(data["forecast"]["forecastday"][0]["day"]["mintemp_f"])
            max1 = round(data["forecast"]["forecastday"][0]["day"]["maxtemp_f"])
            condition_text1 = data["forecast"]["forecastday"][0]["day"]["condition"]["text"].title()
            condition_icon1 = "http:" + data["forecast"]["forecastday"][0]["day"]["condition"]["icon"]

            sunrise1 = data["forecast"]["forecastday"][0]["astro"]["sunrise"]
            if sunrise1.startswith("0"):
                sunrise1 = sunrise1[1:]
            sunset1 = data["forecast"]["forecastday"][0]["astro"]["sunset"]
            if sunset1.startswith("0"):
                sunset1 = sunset1[1:]

            embed1 = discord.Embed(title=f"**Forecast for {location} - Today**",
                                   description=f"**{min1}\u00B0 to {max1}\u00B0 | {condition_text1}**")

            embed1.set_thumbnail(url=condition_icon1)
            embed1.add_field(name="\n\n", value="", inline=False)

            embed1.add_field(name="Sunrise", value=f"{sunrise1}")
            embed1.add_field(name="Sunset", value=f"{sunset1}")

            if any(condition in condition_text1.lower() for condition in ("clear", "sunny")):
                embed1.color = discord.Color.from_rgb(255, 185, 0)
            elif any(condition in condition_text1.lower() for condition in ("mist", "fog", "cloudy", "overcast")):
                embed1.color = discord.Color.light_grey()
            elif any(condition in condition_text1.lower() for condition in ("drizzle", "rain")):
                embed1.color = discord.Color.blurple()
            elif "ice" in condition_text1.lower():
                embed1.color = discord.Color.from_rgb(185, 255, 255)
            elif "thunder" in condition_text1.lower():
                embed1.color = discord.Color.from_rgb(255, 255, 0)
            else:
                embed1.color = discord.Color.from_rgb(255, 255, 255)

            await ctx.send(embed=embed1)
            if days == 1:
                return

            date2 = data["forecast"]["forecastday"][1]["date"][-5:].replace("-", "/")
            if date2.startswith("0"):
                date2 = date2[1:]
            min2 = round(data["forecast"]["forecastday"][1]["day"]["mintemp_f"])
            max2 = round(data["forecast"]["forecastday"][1]["day"]["maxtemp_f"])
            condition_text2 = data["forecast"]["forecastday"][1]["day"]["condition"]["text"].title()
            condition_icon2 = "http:" + data["forecast"]["forecastday"][1]["day"]["condition"]["icon"]

            sunrise2 = data["forecast"]["forecastday"][1]["astro"]["sunrise"]
            if sunrise2.startswith("0"):
                sunrise2 = sunrise2[1:]
            sunset2 = data["forecast"]["forecastday"][1]["astro"]["sunset"]
            if sunset2.startswith("0"):
                sunset2 = sunset2[1:]

            embed2 = discord.Embed(title=f"**Forecast for {location} - {date2}**",
                                   description=f"**{min2}\u00B0 to {max2}\u00B0 | {condition_text2}**")

            embed2.set_thumbnail(url=condition_icon2)
            embed2.add_field(name="\n\n", value="", inline=False)

            embed2.add_field(name="Sunrise", value=f"{sunrise2}")
            embed2.add_field(name="Sunset", value=f"{sunset2}")

            if any(condition in condition_text2.lower() for condition in ("clear", "sunny")):
                embed2.color = discord.Color.from_rgb(255, 185, 0)
            elif any(condition in condition_text2.lower() for condition in ("mist", "fog", "cloudy", "overcast")):
                embed2.color = discord.Color.light_grey()
            elif any(condition in condition_text2.lower() for condition in ("drizzle", "rain")):
                embed2.color = discord.Color.blurple()
            elif "ice" in condition_text2.lower():
                embed2.color = discord.Color.from_rgb(185, 255, 255)
            elif "thunder" in condition_text2.lower():
                embed2.color = discord.Color.from_rgb(255, 255, 0)
            else:
                embed2.color = discord.Color.from_rgb(255, 255, 255)

            await ctx.send(embed=embed2)
            if days == 2:
                return

            date3 = data["forecast"]["forecastday"][2]["date"][-5:].replace("-", "/")
            if date3.startswith("0"):
                date3 = date3[1:]
            min3 = round(data["forecast"]["forecastday"][2]["day"]["mintemp_f"])
            max3 = round(data["forecast"]["forecastday"][2]["day"]["maxtemp_f"])
            condition_text3 = data["forecast"]["forecastday"][2]["day"]["condition"]["text"].title()
            condition_icon3 = "http:" + data["forecast"]["forecastday"][2]["day"]["condition"]["icon"]

            sunrise3 = data["forecast"]["forecastday"][2]["astro"]["sunrise"]
            if sunrise3.startswith("0"):
                sunrise3 = sunrise3[1:]
            sunset3 = data["forecast"]["forecastday"][2]["astro"]["sunset"]
            if sunset3.startswith("0"):
                sunset3 = sunset3[1:]

            embed3 = discord.Embed(title=f"**Forecast for {location} - {date3}**",
                                   description=f"**{min3}\u00B0 to {max3}\u00B0 | {condition_text3}**")

            embed3.set_thumbnail(url=condition_icon3)
            embed3.add_field(name="\n\n", value="", inline=False)

            embed3.add_field(name="Sunrise", value=f"{sunrise3}")
            embed3.add_field(name="Sunset", value=f"{sunset3}")

            if any(condition in condition_text3.lower() for condition in ("clear", "sunny")):
                embed3.color = discord.Color.from_rgb(255, 185, 0)
            elif any(condition in condition_text3.lower() for condition in ("mist", "fog", "cloudy", "overcast")):
                embed3.color = discord.Color.light_grey()
            elif any(condition in condition_text3.lower() for condition in ("drizzle", "rain")):
                embed3.color = discord.Color.blurple()
            elif "ice" in condition_text3.lower():
                embed3.color = discord.Color.from_rgb(185, 255, 255)
            elif "thunder" in condition_text3.lower():
                embed3.color = discord.Color.from_rgb(255, 255, 0)
            else:
                embed3.color = discord.Color.from_rgb(255, 255, 255)

            await ctx.send(embed=embed3)

bot.remove_command("help")
@bot.command()
async def help(ctx):
    embed = discord.Embed(title="**Available Commands**")
    embed.add_field(name="\n\n", value="", inline=False)

    embed.add_field(name="**/weather [city]**", value="fetches current weather conditions in [city]", inline=False)
    embed.add_field(name="**/forecast [city]**", value="fetches today's forecast for [city]", inline=False)
    embed.add_field(name="**/forecast2 [city]**", value="fetches 2-day forecast for [city]", inline=False)
    embed.add_field(name="**/forecast3 [city]**", value="fetches 3-day forecast for [city]", inline=False)
    embed.color = discord.Color.purple()

    await ctx.send(embed=embed)

keep_alive()

bot.run(TOKEN)