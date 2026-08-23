const { SlashCommandBuilder, EmbedBuilder } = require("discord.js");
const { getUser } = require("../lib/backendClient");

const COLOR = 0x2b6cb0;
const COLOR_ERROR = 0xe53e3e;

module.exports = {
  data: new SlashCommandBuilder()
    .setName("내정보")
    .setDescription("내 컴프야v26 인증 상태와 스탯을 확인합니다."),

  async execute(interaction) {
    await interaction.deferReply({ ephemeral: true });

    let user;
    try {
      user = await getUser(interaction.user.id);
    } catch (err) {
      console.error(err);
      await interaction.editReply({
        embeds: [new EmbedBuilder().setColor(COLOR_ERROR).setTitle("정보를 불러오지 못했습니다")],
      });
      return;
    }

    if (!user) {
      await interaction.editReply({
        embeds: [
          new EmbedBuilder()
            .setColor(COLOR_ERROR)
            .setTitle("아직 인증하지 않았습니다")
            .setDescription("`/인증` 명령어로 먼저 인증을 진행해주세요."),
        ],
      });
      return;
    }

    const verifiedAt = new Date(user.verified_at);
    const embed = new EmbedBuilder()
      .setColor(COLOR)
      .setTitle("내 컴프야v26 정보")
      .addFields(
        { name: "구단", value: user.team_name ?? "미등록", inline: true },
        { name: "오버롤", value: user.overall != null ? String(user.overall) : "미등록", inline: true },
        { name: "인증 일시", value: `<t:${Math.floor(verifiedAt.getTime() / 1000)}:f>` }
      );

    await interaction.editReply({ embeds: [embed] });
  },
};
