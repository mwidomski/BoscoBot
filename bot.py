import logging
import re
import asteval
import discord
from discord.ext import commands

m_tkrole = re.compile("[-+*/=]([0-9]+$)")
aeval = asteval.Interpreter()

logging.basicConfig(level=logging.INFO)

PREFIX = '.bosco '

client = discord.Client()
bot = commands.Bot(command_prefix=PREFIX)

#TODO: Get Michael to create custom channel for logging bot output
#TODO: Custom error message for invalid commands

###private call to populate nowplaying array
###FORMAT: <Discord User to PM>:<Comma separated list of discord Users to pm for on status change>
def __updateNowPlaying():
  nplist = []
  f = open("Resources/nowplaying.txt","r")
  lst1 = []
  for line in f:
    lst0 = line.split(":")
    lst1.append(lst0[0])
    for elem in lst0[1].split(","):
      lst1.append(elem)
  nplist.append(lst1)
  print(*nplist, sep=', ')
  f.close()
  
### Get nowplaying registrations
nplist = []
__updateNowPlaying()

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

#TODO: Get mike troll pic from Michael
#TODO: Maybe just paste the image, don't use Embed
### When called, paste a picture of mike troll in the calling channel
#@bot.command()
#async def mike(ctx):
#  __embed = discord.Embed()
#  #__embed.set("url to image")
#  ctx.channel.send(embed=_embed)


#PM opted in users whenever another user is playing a game
#TODO: Replace txt file with mongo or something. Periodic automatic checks.
#@client.event()
#async def on_member_update():
#  return
  
  
@bot.command()
##TODO: specify multiple members per command
##TODO: Potential for race condition here with simultaenous read/writes from different command calls
async def npregister(ctx, member: discord.Member = None):
  found = False
  print("Starting command npregister...")
  m = "Added " + member.name + " to PM alerts"
  f = open("Resources/nowplaying.txt", "r+")
  print("Opened file nowplaying...")
  lines = f.readlines()
  f.seek(0) #rewrite the file
  for line in lines:
    if line.split(":")[0] == ctx.message.author.name:
      found = True
      if not member.name in line.split(":")[1]:
        line = line.strip("\n") + "," + member.name + "\n"
    f.write(line)
  if found == False:
    f.write(ctx.message.author.name + ":" + member.name + "\n")
  f.close()
  __updateNowPlaying()
  await ctx.message.author.send(m)
  await ctx.message.delete()
  
  

@teamkills.error
@npregister.error
async def member_error(ctx, error):
    print(error)
    if isinstance(error, discord.ext.commands.BadArgument):
        await ctx.message.author.send(error)
  
####################RUNNER####################
f = open('token.txt','r')
token = f.read()
f.close()
bot.run(token)