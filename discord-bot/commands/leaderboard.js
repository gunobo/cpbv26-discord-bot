const {
  SlashCommandBuilder,
  EmbedBuilder,
  ActionRowBuilder,
  ButtonBuilder,
  ButtonStyle,
  ComponentType,
} = require("discord.js");
const { getLeaderboard } = require("../lib/backendClient");

const COLOR = 0x2b6cb0;
const COLOR_ERROR = 0xe53e3e;
const PAGE_SIZE = 10;

function buildEmbed(ranked, page, totalPages, team) {
  const start = page * PAGE_SIZE;
  const lines = ranked.slice(start, start + PAGE_SIZE).map((e, i) => {
    const rank = start + i + 1;
    return `**${rank}.** <@${e.discord_id}> — ${e.team_name ?? "미상"} · OVR ${e.overall}`;
  });

  return new EmbedBuilder()
    .setTitle(team ? `컴프야v26 리더보드 — ${team}` : "컴프야v26 리더보드")
    .setDescription(lines.join("\n"))
    .setColor(COLOR)
    .setFooter({ text: `${page + 1} / ${totalPages} 페이지` });
}

function buildRow(page, totalPages) {
  return new ActionRowBuilder().addComponents(
    new ButtonBuilder()
      .setCustomId("prev")
      .setLabel("◀ 이전")
      .setStyle(ButtonStyle.Secondary)
      .setDisabled(page === 0),
    new ButtonBuilder()
      .setCustomId("next")
      .setLabel("다음 ▶")
      .setStyle(ButtonStyle.Secondary)
      .setDisabled(page >= totalPages - 1)
  );
}

module.exports = {
  data: new SlashCommandBuilder()
    .setName("리더보드")
    .setDescription("인증된 서버 멤버들의 오버롤 리더보드를 보여줍니다.")
    .addStringOption((opt) =>
      opt.setName("구단").setDescription("특정 구단만 필터링").setRequired(false)
    ),

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

    const teamFilter = interaction.options.getString("구단");
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

    let ranked = entries.filter((e) => e.overall != null);
    if (teamFilter) {
      ranked = ranked.filter((e) => e.team_name === teamFilter);
    }

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

    const totalPages = Math.ceil(ranked.length / PAGE_SIZE);
    let page = 0;

    const message = await interaction.editReply({
      embeds: [buildEmbed(ranked, page, totalPages, teamFilter)],
      components: totalPages > 1 ? [buildRow(page, totalPages)] : [],
    });

    if (totalPages <= 1) return;

    const collector = message.createMessageComponentCollector({
      componentType: ComponentType.Button,
      time: 120_000,
    });

    collector.on("collect", async (buttonInteraction) => {
      if (buttonInteraction.user.id !== interaction.user.id) {
        await buttonInteraction.reply({ content: "본인만 넘길 수 있습니다.", ephemeral: true });
        return;
      }
      page = buttonInteraction.customId === "next" ? page + 1 : page - 1;
      await buttonInteraction.update({
        embeds: [buildEmbed(ranked, page, totalPages, teamFilter)],
        components: [buildRow(page, totalPages)],
      });
    });

    collector.on("end", async () => {
      await interaction.editReply({ components: [] }).catch(() => {});
    });
  },
};
