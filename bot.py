import discord
from discord import app_commands
from discord.ui import Button, View
import os
from flask import Flask
from threading import Thread
import json

# Flask web server to keep bot alive
app = Flask('')

@app.route('/')
def home():
    return "Gamepass Calculator Bot is running!"

def run():
    app.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = Thread(target=run)
    t.start()

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.guild_messages = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# Configuration
RATE = 7  # $7 per 1000 Robux
SHOP_CHANNEL_ID = None  # Will be set with /setup command
TICKET_CHANNEL_ID = None  # Will be set with /setup command

# Storage for shop channel (persistent)
def load_config():
    global SHOP_CHANNEL_ID, TICKET_CHANNEL_ID
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            SHOP_CHANNEL_ID = config.get('shop_channel_id')
            TICKET_CHANNEL_ID = config.get('ticket_channel_id')
    except FileNotFoundError:
        pass

def save_config():
    with open('config.json', 'w') as f:
        json.dump({
            'shop_channel_id': SHOP_CHANNEL_ID,
            'ticket_channel_id': TICKET_CHANNEL_ID
        }, f)

class ShopView(View):
    def __init__(self, ticket_channel_id):
        super().__init__(timeout=None)  # Never timeout
        self.ticket_channel_id = ticket_channel_id
    
    @discord.ui.button(label="🎮 Buy Giftable Gamepass", style=discord.ButtonStyle.green, custom_id="giftable_gamepass")
    async def giftable_gamepass(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(
            title="🎮 Giftable Gamepass Purchase",
            description=f"To purchase a **giftable gamepass**, please create a ticket in <#{self.ticket_channel_id}>",
            color=discord.Color.green()
        )
        embed.add_field(
            name="📊 Current Rate",
            value=f"**${RATE} per 1,000 Robux**",
            inline=False
        )
        embed.add_field(
            name="📝 What to Include",
            value="• Gamepass link\n• Robux amount\n• Your username",
            inline=False
        )
        embed.set_footer(text=f"Click the channel mention to go to tickets")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="💎 Buy Robux", style=discord.ButtonStyle.blurple, custom_id="buy_robux")
    async def buy_robux(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(
            title="💎 Robux Purchase",
            description=f"To purchase **Robux**, please create a ticket in <#{self.ticket_channel_id}>",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="📊 Current Rate",
            value=f"**${RATE} per 1,000 Robux**",
            inline=False
        )
        embed.add_field(
            name="📝 What to Include",
            value="• Amount of Robux needed\n• Your Roblox username\n• Payment method",
            inline=False
        )
        embed.set_footer(text=f"Click the channel mention to go to tickets")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="shop", description="Display the shop menu")
@app_commands.checks.has_permissions(administrator=True)
async def shop(interaction: discord.Interaction):
    """Display the shop menu with purchase options"""
    
    if SHOP_CHANNEL_ID is None:
        await interaction.response.send_message(
            "❌ Shop channel not set! Use `/setup shop_channel:#channel` first.",
            ephemeral=True
        )
        return
    
    if TICKET_CHANNEL_ID is None:
        await interaction.response.send_message(
            "❌ Ticket channel not set! Use `/setup ticket_channel:#channel` first.",
            ephemeral=True
        )
        return
    
    # Check if command is used in the shop channel
    if interaction.channel_id != SHOP_CHANNEL_ID:
        await interaction.response.send_message(
            f"❌ This command can only be used in <#{SHOP_CHANNEL_ID}>",
            ephemeral=True
        )
        return
    
    embed = discord.Embed(
        title="🛒 Welcome to Our Shop!",
        description="Choose what you'd like to purchase:",
        color=discord.Color.gold()
    )
    embed.add_field(
        name="💰 Current Rate",
        value=f"**${RATE} per 1,000 Robux**",
        inline=False
    )
    embed.add_field(
        name="🎫 How to Purchase",
        value=f"Click a button below, then create a ticket in <#{TICKET_CHANNEL_ID}>",
        inline=False
    )
    embed.set_footer(text="Select an option below to get started")
    
    view = ShopView(TICKET_CHANNEL_ID)
    await interaction.response.send_message(embed=embed, view=view)

@tree.command(name="setup", description="Set the shop and ticket channels")
@app_commands.describe(
    shop_channel="The channel where /shop command will work",
    ticket_channel="The channel where users create tickets"
)
@app_commands.checks.has_permissions(administrator=True)
async def setup(interaction: discord.Interaction, shop_channel: discord.TextChannel, ticket_channel: discord.TextChannel):
    """Set the shop and ticket channels"""
    global SHOP_CHANNEL_ID, TICKET_CHANNEL_ID
    
    SHOP_CHANNEL_ID = shop_channel.id
    TICKET_CHANNEL_ID = ticket_channel.id
    save_config()
    
    embed = discord.Embed(
        title="✅ Channels Set Successfully!",
        description="Bot configuration updated:",
        color=discord.Color.green()
    )
    embed.add_field(
        name="🛒 Shop Channel",
        value=f"{shop_channel.mention}",
        inline=False
    )
    embed.add_field(
        name="🎫 Ticket Channel",
        value=f"{ticket_channel.mention}",
        inline=False
    )
    embed.add_field(
        name="📝 Next Step",
        value=f"Go to {shop_channel.mention} and use `/shop` to display the shop menu",
        inline=False
    )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="refresh", description="Refresh bot's channel cache and sync commands")
@app_commands.checks.has_permissions(administrator=True)
async def refresh(interaction: discord.Interaction):
    """Refresh the bot to see new channels"""
    
    await interaction.response.defer(ephemeral=True)
    
    try:
        # Sync slash commands
        await tree.sync()
        
        # Count channels
        channel_count = len(interaction.guild.text_channels)
        
        embed = discord.Embed(
            title="🔄 Bot Refreshed!",
            description="Successfully refreshed bot cache and synced commands.",
            color=discord.Color.green()
        )
        embed.add_field(
            name="📊 Channels Detected",
            value=f"**{channel_count}** text channels",
            inline=False
        )
        embed.add_field(
            name="✅ What was refreshed",
            value="• Channel cache\n• Slash commands\n• Server data",
            inline=False
        )
        embed.set_footer(text="You can now use /setup with new channels")
        
        await interaction.followup.send(embed=embed, ephemeral=True)
        
        print(f"🔄 Bot refreshed by {interaction.user} | {channel_count} channels detected")
        
    except Exception as e:
        await interaction.followup.send(
            f"❌ Error refreshing bot: {str(e)}",
            ephemeral=True
        )
        print(f"❌ Refresh error: {e}")

@client.event
async def on_ready():
    # Load saved config
    load_config()
    
    await tree.sync()
    print(f'✅ Bot is ready! Logged in as {client.user}')
    print(f'📊 Rate: ${RATE} per 1,000 Robux')
    if SHOP_CHANNEL_ID:
        print(f'🛒 Shop Channel ID: {SHOP_CHANNEL_ID}')
    else:
        print('⚠️  Shop channel not set.')
    if TICKET_CHANNEL_ID:
        print(f'🎫 Ticket Channel ID: {TICKET_CHANNEL_ID}')
    else:
        print('⚠️  Ticket channel not set.')
    if not SHOP_CHANNEL_ID or not TICKET_CHANNEL_ID:
        print('Use /setup to configure both channels.')

# Start web server to keep bot alive
keep_alive()

# Run bot
TOKEN = os.environ.get('DISCORD_TOKEN')
if TOKEN:
    client.run(TOKEN)
else:
    print("❌ ERROR: DISCORD_TOKEN not found in environment variables!")
    print("Please add your bot token to Render environment variables")
