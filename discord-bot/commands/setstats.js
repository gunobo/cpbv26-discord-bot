const { SlashCommandBuilder, PermissionFlagsBits, EmbedBuilder } = require("discord.js");
const { updateUserStats } = require("../lib/backendClient");

const COLOR = 0x2b6cb0;
const COLOR_ERROR = 0xe53e3e;

module.exports = {
  data: new SlashCommandBuilder()
    .setName("스탯설정")
    .setDescription("[운영자] 인증된 유저의 팀/오버롤을 수동으로 입력합니다.")
    .setDefaultMemberPermissions(PermissionFlagsBits.ManageGuild)
    .addUserOption((opt) => opt.setName("유저").setDescription("대상 유저").setRequired(true))
    .addStringOption((opt) => opt.setName("팀").setDescription("팀 이름").setRequired(true))
    .addIntegerOption((opt) =>
      opt.setName("오버롤").setDescription("오버롤 수치").setRequired(true)
    ),

  async execute(interaction) {
    const target = interaction.options.getUser("유저", true);
    const team = interaction.options.getString("팀", true);
    const overall = interaction.options.getInteger("오버롤", true);

    await interaction.deferReply({ ephemeral: true });

    let result;
    try {
      result = await updateUserStats(target.id, team, overall);
    } catch (err) {
      console.error(err);
      await interaction.editReply({
        embeds: [
          new EmbedBuilder()
            .setColor(COLOR_ERROR)
            .setTitle("스탯 업데이트 실패")
            .setDescription("대상 유저가 먼저 /인증을 완료했는지 확인해주세요."),
        ],
      });
      return;
    }

    const embed = new EmbedBuilder()
      .setColor(result.role_synced ? COLOR : 0xecc94b)
      .setTitle("스탯 갱신 완료")
      .setDescription(`<@${target.id}> — ${team} · OVR ${overall}`);

    if (!result.role_synced) {
      embed.addFields({
        name: "⚠️ 구단 역할 부여 실패",
        value: `\`/구단역할 설정\`으로 "${team}" 매핑이 되어있는지 확인해주세요.`,
      });
    }

    await interaction.editReply({ embeds: [embed] });
  },
};
