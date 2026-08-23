const { SlashCommandBuilder, EmbedBuilder, ActionRowBuilder, ButtonBuilder, ButtonStyle } = require("discord.js");

const RULES_TEXT = (process.env.SERVER_RULES || "규칙이 아직 설정되지 않았습니다.").replace(/\\n/g, "\n");

module.exports = {
  data: new SlashCommandBuilder()
    .setName("인증")
    .setDescription("서버 규칙에 동의하고 Hive 계정으로 인증합니다."),

  async execute(interaction) {
    const embed = new EmbedBuilder()
      .setTitle("서버 규칙")
      .setDescription(RULES_TEXT)
      .setColor(0x2b6cb0)
      .setFooter({ text: "동의 버튼을 누르면 Hive 로그인 인증이 시작됩니다." });

    const row = new ActionRowBuilder().addComponents(
      new ButtonBuilder()
        .setCustomId("agree_rules")
        .setLabel("규칙에 동의합니다")
        .setStyle(ButtonStyle.Success)
    );

    await interaction.reply({ embeds: [embed], components: [row], ephemeral: true });
  },
};
