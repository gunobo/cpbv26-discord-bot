const { SlashCommandBuilder, EmbedBuilder } = require("discord.js");
const { getLeaderboard } = require("../lib/backendClient");

module.exports = {
  data: new SlashCommandBuilder()
    .setName("리더보드")
    .setDescription("인증된 서버 멤버들의 오버롤 리더보드를 보여줍니다."),

  async execute(interaction) {
    const verifiedRoleId = process.env.VERIFIED_ROLE_ID;
    const hasRole = interaction.member.roles.cache.has(verifiedRoleId);
    if (!hasRole) {
      await interaction.reply({ content: "먼저 `/인증` 을 진행해주세요.", ephemeral: true });
      return;
    }

    await interaction.deferReply();

    let entries;
    try {
      entries = await getLeaderboard(interaction.guildId);
    } catch (err) {
      console.error(err);
      await interaction.editReply("리더보드를 불러오는 중 오류가 발생했습니다.");
      return;
    }

    const ranked = entries.filter((e) => e.overall != null).slice(0, 20);

    if (ranked.length === 0) {
      await interaction.editReply("아직 등록된 스탯이 없습니다.");
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
      .setColor(0x2b6cb0);

    await interaction.editReply({ embeds: [embed] });
  },
};
