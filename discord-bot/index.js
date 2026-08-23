require("dotenv").config();
const { Client, Collection, GatewayIntentBits, Events } = require("discord.js");

const client = new Client({ intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildMembers] });

client.commands = new Collection();
for (const file of [
  "verify",
  "leaderboard",
  "setstats",
  "teamrole",
  "myinfo",
  "unverify",
  "hivestatus",
  "events",
  "coupons",
]) {
  const command = require(`./commands/${file}`);
  client.commands.set(command.data.name, command);
}

client.once(Events.ClientReady, (c) => {
  console.log(`로그인됨: ${c.user.tag}`);
});

client.on(Events.InteractionCreate, async (interaction) => {
  try {
    if (interaction.isChatInputCommand()) {
      const command = client.commands.get(interaction.commandName);
      if (!command) return;
      await command.execute(interaction);
      return;
    }
  } catch (err) {
    console.error(err);
    const payload = { content: "처리 중 오류가 발생했습니다.", ephemeral: true };
    if (interaction.deferred || interaction.replied) {
      await interaction.editReply(payload).catch(() => {});
    } else {
      await interaction.reply(payload).catch(() => {});
    }
  }
});

client.login(process.env.DISCORD_TOKEN);
