const { SlashCommandBuilder, PermissionFlagsBits, EmbedBuilder } = require("discord.js");
const { deleteUser } = require("../lib/backendClient");

const COLOR = 0x2b6cb0;
const COLOR_ERROR = 0xe53e3e;

module.exports = {
  data: new SlashCommandBuilder()
    .setName("인증해제")
    .setDescription("[운영자] 유저의 인증 기록을 삭제하고 관련 역할을 회수합니다.")
    .setDefaultMemberPermissions(PermissionFlagsBits.ManageGuild)
    .addUserOption((opt) => opt.setName("유저").setDescription("대상 유저").setRequired(true)),

  async execute(interaction) {
    const target = interaction.options.getUser("유저", true);
    await interaction.deferReply({ ephemeral: true });

    let result;
    try {
      result = await deleteUser(target.id);
    } catch (err) {
      console.error(err);
      await interaction.editReply({
        embeds: [new EmbedBuilder().setColor(COLOR_ERROR).setTitle("인증 해제에 실패했습니다")],
      });
      return;
    }

    if (!result) {
      await interaction.editReply({
        embeds: [
          new EmbedBuilder()
            .setColor(COLOR_ERROR)
            .setTitle("인증 기록이 없습니다")
            .setDescription(`<@${target.id}> 는 인증한 적이 없습니다.`),
        ],
      });
      return;
    }

    await interaction.editReply({
      embeds: [
        new EmbedBuilder()
          .setColor(COLOR)
          .setTitle("인증 해제 완료")
          .setDescription(`<@${target.id}> 의 인증 기록과 역할을 제거했습니다.`),
      ],
    });
  },
};
