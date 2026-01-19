import discord
from discord import app_commands
from discord.ui import Button, View
import os
from flask import Flask
from threading import Thread

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
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# Configuration
RATE = 7  # $7 per 1000 Robux
TICKET_CHANNEL = "〘🎟〙𝗧𝗜𝗖𝗞𝗘𝗧𝗦"  # Your ticket channel name

# Storage for user states
user_states = {}

class GiftableView(View):
    def __init__(self, user_id):
        super().__init__(timeout=180)
        self.user_id = user_id
    
    @discord.ui.button(label="✅ Yes, Giftable", style=discord.ButtonStyle.green)
    async def giftable_yes(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This button is not for you!", ephemeral=True)
            return
        
        user_states[self.user_id] = "awaiting_amount"
        
        embed = discord.Embed(
            title="💰 Enter Gamepass Price",
            description="Please type the **Robux amount** of your gamepass.\n\nExample: `1000` or `5000`",
            color=discord.Color.blue()
        )
        embed.set_footer(text="Type the amount in chat")
        
        await interaction.response.edit_message(embed=embed, view=None)
    
    @discord.ui.button(label="❌ No, Not Giftable", style=discord.ButtonStyle.red)
    async def giftable_no(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This button is not for you!", ephemeral=True)
            return
        
        # Ask if they want to buy giftable gamepass
        embed = discord.Embed(
            title="⚠️ Service Unavailable",
            description="**Non-giftable gamepasses are currently unavailable.**\n\nWould you like to purchase a **giftable gamepass** instead?",
            color=discord.Color.orange()
        )
        
        view = BuyGiftableView(self.user_id)
        await interaction.response.edit_message(embed=embed, view=view)

class BuyGiftableView(View):
    def __init__(self, user_id):
        super().__init__(timeout=180)
        self.user_id = user_id
    
    @discord.ui.button(label="✅ Yes, Buy Giftable", style=discord.ButtonStyle.green)
    async def buy_yes(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This button is not for you!", ephemeral=True)
            return
        
        # Ask again if their gamepass is giftable
        embed = discord.Embed(
            title="🎁 Giftable Gamepass Purchase",
            description="**Is YOUR gamepass giftable?**\n\nA giftable gamepass allows us to transfer it to you.",
            color=discord.Color.blue()
        )
        
        view = GiftableView(self.user_id)
        await interaction.response.edit_message(embed=embed, view=view)
    
    @discord.ui.button(label="❌ No Thanks", style=discord.ButtonStyle.red)
    async def buy_no(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This button is not for you!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="👋 See You Later!",
            description=f"No problem! If you change your mind, use `/calculate` again.\n\nFor questions, visit #{TICKET_CHANNEL}",
            color=discord.Color.blue()
        )
        
        await interaction.response.edit_message(embed=embed, view=None)

@tree.command(name="calculate", description="Calculate gamepass price in USD")
async def calculate(interaction: discord.Interaction):
    """Calculate how much a gamepass costs in real money"""
    
    embed = discord.Embed(
        title="🎮 Gamepass Price Calculator",
        description="**Is your gamepass giftable?**\n\nGiftable gamepasses can be transferred between accounts.",
        color=discord.Color.green()
    )
    embed.add_field(
        name="📊 Current Rate",
        value=f"**${RATE} per 1,000 Robux**",
        inline=False
    )
    embed.set_footer(text="Select an option below")
    
    view = GiftableView(interaction.user.id)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=False)

@client.event
async def on_message(message):
    # Ignore bot messages
    if message.author.bot:
        return
    
    # Check if user is awaiting amount
    user_id = message.author.id
    if user_id in user_states and user_states[user_id] == "awaiting_amount":
        try:
            # Parse robux amount
            robux = int(message.content.replace(",", ""))
            
            if robux <= 0:
                await message.reply("❌ Please enter a valid positive number!")
                return
            
            # Calculate USD price
            usd_price = (robux / 1000) * RATE
            
            # Create result embed
            embed = discord.Embed(
                title="💵 Price Calculation",
                description=f"**Gamepass Price:** {robux:,} Robux",
                color=discord.Color.gold()
            )
            embed.add_field(
                name="💰 USD Cost",
                value=f"**${usd_price:.2f}**",
                inline=False
            )
            embed.add_field(
                name="📊 Calculation",
                value=f"{robux:,} ÷ 1,000 × ${RATE} = **${usd_price:.2f}**",
                inline=False
            )
            embed.add_field(
                name="🎫 Next Step",
                value=f"To purchase, create a ticket in #{TICKET_CHANNEL}",
                inline=False
            )
            embed.set_footer(text=f"Requested by {message.author.name}")
            
            await message.reply(embed=embed)
            
            # Clear user state
            del user_states[user_id]
            
        except ValueError:
            await message.reply("❌ Invalid number! Please enter a valid Robux amount (example: `1000`)")

@client.event
async def on_ready():
    await tree.sync()
    print(f'✅ Bot is ready! Logged in as {client.user}')
    print(f'📊 Rate: ${RATE} per 1,000 Robux')
    print(f'🎫 Ticket Channel: #{TICKET_CHANNEL}')

# Start web server to keep bot alive
keep_alive()

# Run bot
TOKEN = os.environ.get('DISCORD_TOKEN')
if TOKEN:
    client.run(TOKEN)
else:
    print("❌ ERROR: DISCORD_TOKEN not found in environment variables!")
    print("Please add your bot token to Render environment variables")
