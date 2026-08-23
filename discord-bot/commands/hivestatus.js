const { SlashCommandBuilder, PermissionFlagsBits, EmbedBuilder } = require("discord.js");
const { getStatus } = require("../lib/backendClient");

const COLOR = 0x2b6cb0;
const COLOR_ERROR = 0xe53e3e;

module.exports = {
  data: new SlashCommandBuilder()
    .setName("하이브상태")
    .setDescription("[운영자] 현재 Hive 연동 상태와 /인증 동작 방식을 확인합니다.")
    .setDefaultMemberPermissions(PermissionFlagsBits.ManageGuild),

  async execute(interaction) {
    await interaction.deferReply({ ephemeral: true });

    let status;
    try {
      status = await getStatus();
    } catch (err) {
      console.error(err);
      await interaction.editReply({
        embeds: [new EmbedBuilder().setColor(COLOR_ERROR).setTitle("상태를 불러오지 못했습니다")],
      });
      return;
    }

    const embed = new EmbedBuilder()
      .setColor(COLOR)
      .setTitle("Hive 연동 상태")
      .addFields(
        {
          name: "연동 상태",
          value: status.hive_connected ? "✅ 연동됨 (실제 Hive 로그인 사용)" : "❌ 미연동 (규칙 체크만으로 인증)",
        },
        { name: "모킹 모드", value: status.hive_mock_mode ? "켜짐" : "꺼짐", inline: true }
      )
      .setFooter({
        text: status.hive_connected
          ? "/인증 실행 시 Hive 로그인 링크를 제공합니다."
          : "/인증 실행 시 규칙 반응 확인만으로 즉시 인증 완료됩니다.",
      });

    await interaction.editReply({ embeds: [embed] });
  },
};
