const { SlashCommandBuilder, PermissionFlagsBits, EmbedBuilder } = require("discord.js");
const { setTeamRole, listTeamRoles } = require("../lib/backendClient");

const COLOR = 0x2b6cb0;
const COLOR_ERROR = 0xe53e3e;

module.exports = {
  data: new SlashCommandBuilder()
    .setName("구단역할")
    .setDescription("[운영자] 컴프야v26 구단별 디스코드 역할을 관리합니다.")
    .setDefaultMemberPermissions(PermissionFlagsBits.ManageGuild)
    .addSubcommand((sub) =>
      sub
        .setName("설정")
        .setDescription("구단명과 디스코드 역할을 매핑합니다.")
        .addStringOption((opt) => opt.setName("구단").setDescription("구단 이름").setRequired(true))
        .addRoleOption((opt) =>
          opt.setName("역할").setDescription("부여할 디스코드 역할").setRequired(true)
        )
    )
    .addSubcommand((sub) => sub.setName("목록").setDescription("현재 설정된 구단-역할 매핑을 봅니다.")),

  async execute(interaction) {
    const sub = interaction.options.getSubcommand();

    if (sub === "설정") {
      const team = interaction.options.getString("구단", true);
      const role = interaction.options.getRole("역할", true);
      await interaction.deferReply({ ephemeral: true });
      try {
        await setTeamRole(interaction.guildId, team, role.id);
      } catch (err) {
        console.error(err);
        await interaction.editReply({
          embeds: [new EmbedBuilder().setColor(COLOR_ERROR).setTitle("매핑 저장 실패")],
        });
        return;
      }
      await interaction.editReply({
        embeds: [
          new EmbedBuilder()
            .setColor(COLOR)
            .setTitle("구단 역할 설정 완료")
            .setDescription(`**${team}** → <@&${role.id}>`),
        ],
      });
      return;
    }

    if (sub === "목록") {
      await interaction.deferReply({ ephemeral: true });
      let entries;
      try {
        entries = await listTeamRoles(interaction.guildId);
      } catch (err) {
        console.error(err);
        await interaction.editReply({
          embeds: [new EmbedBuilder().setColor(COLOR_ERROR).setTitle("목록을 불러오지 못했습니다")],
        });
        return;
      }

      const embed = new EmbedBuilder().setColor(COLOR).setTitle("구단-역할 매핑 목록");
      if (entries.length === 0) {
        embed.setDescription("아직 설정된 매핑이 없습니다. `/구단역할 설정`으로 등록해주세요.");
      } else {
        embed.setDescription(entries.map((e) => `${e.team_name} → <@&${e.role_id}>`).join("\n"));
      }
      await interaction.editReply({ embeds: [embed] });
    }
  },
};
