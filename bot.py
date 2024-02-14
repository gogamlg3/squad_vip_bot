import discord
import asyncio
import logging
import requests
import toml
import json
from discord import app_commands
from datetime import datetime, timezone
from dateutil.parser import isoparse as datetime_isoparse

handler = logging.FileHandler(filename='discord_bot.log', encoding='utf-8', mode='w')
logging.basicConfig(level=logging.INFO, filename="command.log", filemode="a",  format="[%(asctime)s]: %(message)s")

CONFIG = toml.load("config.toml")
WEBHOOK_URL = CONFIG["WEBHOOK_URL"]
ADMIN_ROLE = CONFIG["ROLE"]
TOKEN = CONFIG["BOT_TOKEN"]
REST_TOKEN = CONFIG["AUTH_TOKEN"]
REST_URL = CONFIG["REST_API_URL"]

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
        if ADMIN_ROLE in [role.id for role in interaction.user.roles]:
            data = {
                   "steam_id": steam_id,
                   "name": player_name,
                   "comment": f"{interaction.user.name} webhook",
                   "duration_until_end": date
                   }

            r = requests.post(WEBHOOK_URL, data=data)
            print(f"[{datetime.now()}]: {interaction.user.name} uses command /add")
            logging.info(f"[{datetime.now()}]: {interaction.user.name} uses command /add")

            if r.text != '{"detail":"Created"}':
                await interaction.response.send_message(f"Ты что-то неправильно ввел\n\n{r.text}", ephemeral=True)

            else:
                await interaction.response.send_message(f"{interaction.user.mention} дал вип игроку '{player_name}' на срок {date} дня(-ей)")
        else:
            print(f"[{datetime.now()}]: {interaction.user.name} uses command /add without admin role")
            logging.info(f"[{datetime.now()}]: {interaction.user.name} uses command /add")
            await interaction.response.send_message("У вас нет прав на использование этой команды", ephemeral=True)


    except Exception as e:
        print(e)


@tree.command(name="vip", description="Узнать время до истечения випки")
@app_commands.describe(steam_id = "SteamID")
async def vip_command(interaction: discord.Interaction, steam_id: str):
    try:
        print(f"[{datetime.now()}]: {interaction.user.name} uses command /vip")
        logging.info(f"[{datetime.now()}]: {interaction.user.name} uses command /vip")
        
        url_with_steam = f"{REST_URL}?steam_id={steam_id}"
        req = requests.get(url_with_steam, headers={"Authorization":f"Token {REST_TOKEN}"})

        if req.text in ["[]", '{"steam_id":["Введите число."]}']:
            await interaction.response.send_message(f"У вас нет випа или вы ввели неверный SteamID", ephemeral=True)

        else:
            jList = json.loads(req.text)
            date_of_end = jList[0]['date_of_end']
            is_active = jList[0]['is_active']
            
            if date_of_end == None:
                await interaction.response.send_message(f"У вас бессрочный вип", ephemeral=True)
           
            else:
                timestamp = datetime_isoparse(date_of_end).strftime('%d.%m.%Y %H:%M')
                
                if is_active == False:
                    await interaction.response.send_message(f"У вас закончился вип, дата: {timestamp} МСК", ephemeral=True)
                    
                times = datetime_isoparse(date_of_end) - datetime.now(timezone.utc)
                await interaction.response.send_message(f"Количество дней до конца вип: {times.days}.\n\nДата окончания вип: {timestamp} МСК", ephemeral=True)

    except Exception as e:
        print(e)


@client.event
async def on_ready():
    print(f"[{datetime.now()}]: {client.user} up!!")
    synced = await tree.sync()
    print(f'Synced {len(synced)} commands')

client.run(TOKEN, log_handler=handler)