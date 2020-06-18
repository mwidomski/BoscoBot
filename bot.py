import logging
import re
import asteval
import traceback
import discord
from discord.ext import commands
from discord.ext.commands import cooldown

m_tkrole = re.compile("[-+*/=]([0-9]+$)")
aeval = asteval.Interpreter()


logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='/home/pi/BoscoBot/logs/bosco.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

PREFIX = '.bosco '
RYTHM = '!'

client = discord.Client()
bot = commands.Bot(command_prefix=PREFIX)

#TODO: Help command

@bot.event
async def on_ready():
    print("Rock and Stone Miners! (Bosco is ready)")


async def lookup_channel_server(guild,channel_name):
    print('calling lookup function for ' + channel_name + ' in ' + guild.name)
    channel = discord.utils.get(guild.text_channels, name = channel_name)
    if channel == None:
        print('Error retrieving channel #' + channel_name + '\n')
        print(guild.text_channels)
        return None
    print('found __#' + channel.name + '__ in **' + channel.guild.name + '**')
    return channel
    
    

@bot.event
async def on_raw_message_delete(rawevent):
    print("on_raw_message_delete was called")
    payload_channel = bot.get_channel(rawevent.channel_id)
    if payload_channel.name == 'bosco-audit-log':
        print("deletion in #bosco-audit-log , skipping...")
        return None
    print(payload_channel.guild)
    audit_channel = await lookup_channel_server(payload_channel.guild,'bosco-audit-log')
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
            #TODO: Use bot.prefix()
            if rawevent.cached_message.content[0:6] == '.bosco':
                print("deleted message is a bot command, skipping...")
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
    elif after.content[0:6] == '.bosco':
        print("message is a prefix, skipping...")
        return None
    elif after.pinned:
        print("message is pinned, skipping...")
        return None
    else:
        audit_channel = await lookup_channel_server(before.guild,'bosco-audit-log')
        if audit_channel is None:
            print("Failed to lookup __#bosco-audit-log__ channel")
            return None
        else:
            await audit_channel.send("Message edited by *" + after.author.name + "* in __#" + after.channel.name + "__ :\n **BEFORE** : " + before.content + "\n** AFTER** : " + after.content)
                    
            

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
async def join_voice(ctx):
    channel = ctx.author.voice.channel
    await channel.connect()

@bot.command()
async def leave_voice(ctx):
    await ctx.voice_client.disconnect()

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
