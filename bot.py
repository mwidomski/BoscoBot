import logging
import re
import asteval
import traceback
import discord
from discord.ext import commands
from discord.ext.commands import cooldown

PREFIX = '.bosco '
RYTHM = '!'

m_tkrole = re.compile("[-+*/=]([0-9]+$)")
m_rythmprefix = re.compile(RYTHM+"[\w]")

aeval = asteval.Interpreter()


channel_hold_list = dict()


logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='/home/pi/BoscoBot/logs/bosco.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

client = discord.Client()
bot = commands.Bot(command_prefix=PREFIX)

#TODO: Expand help command
#TODO: Deletion record for images isn't working

@bot.event
async def on_ready():
    print("Rock and Stone Miners! (Bosco is ready)")


async def lookup_tchannel_server(guild,channel_name):
    print('calling text lookup function for ' + channel_name + ' in ' + guild.name)
    channel = discord.utils.get(guild.text_channels, name = channel_name)
    if channel == None:
        print('Error retrieving channel #' + channel_name + '\n')
        print(guild.text_channels)
        return None
    print('found #' + channel.name + ' in ' + channel.guild.name)
    return channel
    
async def lookup_vchannel_server(guild, channel_name):
    print('calling voice lookup function for ' + channel_name + ' in ' + guild.name)
    channel = discord.utils.get(guild.voice_channels, name = channel_name)
    if channel == None:
        print('Error retrieving channel Voice_' + channel_name + '\n')
        print(guild.text_channels)
        return None
    print('found Voice_' + channel.name + ' in ' + channel.guild.name)
    return channel
    
    

@bot.event
async def on_message(message):
    print("on_message called with: " + message.content)
    #Ignore Rythm prefix everywhere except in dedicated channel
    if m_rythmprefix.match(message.content):
        if message.channel.name != 'music-bot-commands':
            music_commands = await lookup_tchannel_server(message.guild, 'music-bot-commands')
            if music_commands is not None:
                await message.delete()
                await message.author.send("Use Rythm commands (!<command>) only in <#" + str(music_commands.id)+ ">")
            else:
                print("Error! Could not find channel #music-bot-commands")
    
    #Other cases go here
    
    #####Have to make sure the command is processed if the message was a command#####
    await bot.process_commands(message)

@bot.event
async def on_raw_message_delete(rawevent):
    print("on_raw_message_delete was called")
    payload_channel = bot.get_channel(rawevent.channel_id)
    if payload_channel.name == 'bosco-audit-log':
        print("deletion in #bosco-audit-log , skipping...")
        return None
    print(payload_channel.guild)
    audit_channel = await lookup_tchannel_server(payload_channel.guild,'bosco-audit-log')
    if audit_channel == None:
        print("Could not find audit log channel")
        return None
    else:
        if rawevent.cached_message == None:
            print("Message <"+str(rawevent.message_id)+"> in channel <"+str(rawevent.channel_id)+"> not cached. Attempting to retrieve...")
            try:
                ret_message = await payload_channel.fetch_message(rawevent.message_id)
                await audit_channel.send("Deleted message by *" + ret_message.author.name +"* at " + ret_message.created_at.strftime("%m/%d/%Y, %H:%M:%S") + " in channel __#" + rawevent.cached_message.channel.name + "__ :\n " + ret_message.content)
            except Exception as e:
                print(traceback.format_exc())
                await audit_channel.send("An exception occured while trying to retrieve message <" + str(rawevent.message_id) + "> from channel __#" + bot.get_channel(rawevent.channel_id).name + "__.")
            
        else:
            if rawevent.cached_message.content[0:7] == PREFIX:
                print("deleted message is a bot command, skipping...")
                return None
            elif rawevent.cached_message.content[0] == RYTHM:
                print("deleted message is a Rythm command, skipping...")
                return None
            else:
                await audit_channel.send("Deleted message by *" + rawevent.cached_message.author.name +"* at " +rawevent.cached_message.created_at.strftime("%m/%d/%Y, %H:%M:%S") + " in channel __#" + rawevent.cached_message.channel.name + "__ :\n " + rawevent.cached_message.content)

@bot.event
async def on_message_edit(before,after):
    print("on_message_edit was called")
    if before.channel.name == 'bosco-audit-log':
        print("edit in #bosco-audit-log , skipping...")
        return None
    elif before.channel.name == 'music-bot-commands':
        if before.author.name == 'Rythm':
            print("message from Rythm bot after command, skipping...")
            return None
    elif 'http' in after.content:
        print("message is a link, skipping...")
        return None
    #TODO: use bot.prefix()
    elif after.content[0:7] == PREFIX:
        print("message is a prefix, skipping...")
        return None
    elif after.pinned:
        print("message is pinned, skipping...")
        return None
    else:
        audit_channel = await lookup_tchannel_server(before.guild,'bosco-audit-log')
        if audit_channel is None:
            print("Failed to lookup #bosco-audit-log channel")
            return None
        else:
            await audit_channel.send("Message edited by *" + after.author.name + "* in __#" + after.channel.name + "__ :\n **BEFORE** : " + before.content + "\n** AFTER** : " + after.content)
                    

@bot.event
async def on_voice_state_update(member,before,after):
    #Keep member in channel if was moved
    if member.id in channel_hold_list:
        voice_channel = channel_hold_list[member.id]
        if before.channel == voice_channel:
            if after.channel is None:
                print("Member left voice, removing channel hold")
                channel_hold_list.pop(member.id)
                await member.send("Removed hold on __" + str(voice_channel) + "__")
            elif before.channel != after.channel:
                await member.move_to(voice_channel, reason="Bosco set channel hold")   
            else:
                return None
    else:
        return None
            

### Set a new number of team kills for members with the team kill role
### REQUIRES: manage_roles, manage_messages
@bot.command()
async def teamkills(ctx, member: discord.Member, command: str):
  if m_tkrole.match(command):
    #evaluate command string
    #interpret command
    operand = command[0]
    r_op = command[1:]
    for rl in member.roles:
      if "Team Kills" in rl.name:
        #get existing number
        l_op = rl.name.rsplit(" ",1)[1]
        #evaluate expression
        if operand != "=":
          result = aeval(l_op+operand+r_op)
        else:
          #WARN: calling aeval is technically unnecessary here
          result = int(aeval(r_op))
        #edit existing role
        await rl.edit(name="Team Kills: " + str(result))
        
        m = "Set new team kill count for " + member.name + " from " + str(l_op) + " to " + str(result)
        #TODO: Use server name instead of global name
        await ctx.message.author.send(m)
        break
    else:
      #TODO: create new role
      m = "Team kill role is not assigned to this member, cannot edit"
      await ctx.message.author.send(m)
      
    
  else:
    m = "Invalid command. Format: .bosco teamkills @<User> [+-*/=]<number>"
    print(m)
    await ctx.message.author.send(m)
    
  #Remove bot command from the channel.
  await ctx.message.delete()
  

#TODO: Override for pin by message id
### Pin message to channel command was invoked in
### REQUIRES: manage_roles
@bot.command()
async def pin(ctx, message: str):
    message = await ctx.channel.send(message)
    await message.pin()
    print("pinned '"+ message.content + "' to #" + ctx.channel.name)
    await ctx.message.delete()
    

@bot.command()
async def joinvoice(ctx):
    channel = ctx.author.voice.channel
    await channel.connect()
    await ctx.message.delete()

@bot.command()
async def leavevoice(ctx):
    await ctx.voice_client.disconnect()
    await ctx.message.delete()
    
@bot.command()
async def keepvoice(ctx):
    user = ctx.message.author
    voice_channel = ctx.message.author.voice.channel
    if voice_channel is None:
        await ctx.message.author.send("You are not in a voice channel!")
    else:
        channel_hold_list[user.id] = voice_channel
        await ctx.message.author.send("Will keep you in __" + str(voice_channel) + "__ until you leave voice")
    await ctx.message.delete()
        
@bot.command()
async def movevoice(ctx, move_from, move_to):
    print("movevoice called")
    voice_channel_to = await lookup_vchannel_server(ctx.message.guild, move_to)
    voice_channel_from = await lookup_vchannel_server(ctx.message.guild, move_from)
    if voice_channel_to and voice_channel_from: 
        print("Attempting to move...")
        for user in voice_channel_from.members:
            await user.move_to(voice_channel_to,reason="Mass channel move by " + ctx.message.author.name)
    
    else:
        message = "The following channels could not be found: "
        if voice_channel_to is None:
            message += "__" + move_to + "__ "
        if voice_channel_from is None:
            message += "__" + move_from + "__ "
        await ctx.message.author.send(message)
    await ctx.message.delete()

@teamkills.error
#@npregister.error
async def member_error(ctx, error):
    print(error)
    if isinstance(error, discord.ext.commands.BadArgument):
        await ctx.message.author.send(error)
  
####################RUNNER####################
f = open('/home/pi/BoscoBot/token.txt','r')
token = f.read()
f.close()
bot.run(token)
