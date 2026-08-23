const { SlashCommandBuilder, PermissionFlagsBits } = require("discord.js");
const { updateUserStats } = require("../lib/backendClient");

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

    try {
      await updateUserStats(target.id, team, overall);
    } catch (err) {
      console.error(err);
      await interaction.editReply(
        "스탯 업데이트에 실패했습니다. 대상 유저가 먼저 /인증을 완료했는지 확인해주세요."
      );
      return;
    }

    await interaction.editReply(`✅ <@${target.id}> 의 스탯을 갱신했습니다 — ${team} · OVR ${overall}`);
  },
};
