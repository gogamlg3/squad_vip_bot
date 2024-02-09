import discord
import asyncio
import logging
import requests
import toml
import json
from discord import app_commands
from datetime import datetime
from dateutil.parser import isoparse as datetime_isoparse

handler = logging.FileHandler(filename='discord_bot.log', encoding='utf-8', mode='w')

CONFIG = toml.load("config.toml")
webhook_url = CONFIG["WEBHOOK_URL"]
admin_role = CONFIG["ROLE"]
token = CONFIG["BOT_TOKEN"]
rest_token = CONFIG["AUTH_TOKEN"]
rest_url = CONFIG["REST_API_URL"]

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@tree.command(name="add", description="Добавить нового випа")
@app_commands.describe(
                       player_name = "Player name",
                       steam_id = "SteamID",
                       date = "На сколько дней выдать вип?")
async def add_command(interaction: discord.Interaction, player_name: str, steam_id: str, date: str):
    try:
        if admin_role in [role.id for role in interaction.user.roles]:
            data = {
                   "steam_id": steam_id,
                   "name": player_name,
                   "comment": f"{interaction.user.name} webhook",
                   "duration_until_end": date
                   }

            r = requests.post(webhook_url, data=data)
            print(f"[{datetime.now()}]: {interaction.user.name} uses command /add")

            if r.text != '{"detail":"Created"}':
                await interaction.response.send_message(f"Ты что-то неправильно ввел\n\n{r.text}", ephemeral=True)

            else:
                await interaction.response.send_message(f"{interaction.user.mention} дал вип игроку '{player_name}' на срок {date} дня(-ей)")
        else:
            print(f"[{datetime.now()}]: {interaction.user.name} uses command /add without admin role")
            await interaction.response.send_message("У вас нет прав на использование этой команды", ephemeral=True)


    except Exception as e:
        print(e)


@tree.command(name="vip", description="Узнать время до истечения випки")
@app_commands.describe(steam_id = "SteamID")
async def vip_command(interaction: discord.Interaction, steam_id: str):
    print(f"[{datetime.now()}]: {interaction.user.name} uses command /vip")
    url_with_steam = f"{rest_url}?fields=date_of_end&steam_id={steam_id}"
    req = requests.get(url_with_steam, headers={"Authorization":f"Token {rest_token}"})

    if req.text in ["[]", '{"steam_id":["Введите число."]}']:
        await interaction.response.send_message(f"У вас нет випа или вы ввели неверный SteamID", ephemeral=True)

    else:
        jlist = json.loads(req.text)[0]['date_of_end']

        if jlist == None:
            await interaction.response.send_message(f"Дата окончания вип: Бессрочно", ephemeral=True)

        else:
            timestamp = datetime_isoparse(jlist).strftime('%d.%m.%Y %H:%M')
            
            await interaction.response.send_message(f"Дата окончания вип: {timestamp} МСК", ephemeral=True)


@client.event
async def on_ready():
    print(f"[{datetime.now()}]: {client.user} up!!")
    synced = await tree.sync()
    print(f'Synced {len(synced)} commands')

client.run(token, log_handler=handler)