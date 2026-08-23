const { SlashCommandBuilder, EmbedBuilder } = require("discord.js");
const { getLeaderboard } = require("../lib/backendClient");

const COLOR = 0x2b6cb0;
const COLOR_ERROR = 0xe53e3e;

module.exports = {
  data: new SlashCommandBuilder()
    .setName("리더보드")
    .setDescription("인증된 서버 멤버들의 오버롤 리더보드를 보여줍니다."),

  async execute(interaction) {
    const verifiedRoleId = process.env.VERIFIED_ROLE_ID;
    const hasRole = interaction.member.roles.cache.has(verifiedRoleId);
    if (!hasRole) {
      await interaction.reply({
        embeds: [
          new EmbedBuilder()
            .setColor(COLOR_ERROR)
            .setTitle("인증이 필요합니다")
            .setDescription("먼저 `/인증` 을 진행해주세요."),
        ],
        ephemeral: true,
      });
      return;
    }

    await interaction.deferReply();

    let entries;
    try {
      entries = await getLeaderboard(interaction.guildId);
    } catch (err) {
      console.error(err);
      await interaction.editReply({
        embeds: [new EmbedBuilder().setColor(COLOR_ERROR).setTitle("리더보드를 불러오지 못했습니다")],
      });
      return;
    }

    const ranked = entries.filter((e) => e.overall != null).slice(0, 20);

    if (ranked.length === 0) {
      await interaction.editReply({
        embeds: [
          new EmbedBuilder()
            .setColor(COLOR)
            .setTitle("컴프야v26 리더보드")
            .setDescription("아직 등록된 스탯이 없습니다."),
        ],
      });
      return;
    }

    const lines = ranked.map((e, i) => {
      const rank = i + 1;
      const team = e.team_name ?? "미상";
      return `**${rank}.** <@${e.discord_id}> — ${team} · OVR ${e.overall}`;
    });

    const embed = new EmbedBuilder()
      .setTitle("컴프야v26 리더보드")
      .setDescription(lines.join("\n"))
      .setColor(COLOR);

    await interaction.editReply({ embeds: [embed] });
  },
};
