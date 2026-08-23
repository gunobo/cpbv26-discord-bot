const {
  SlashCommandBuilder,
  EmbedBuilder,
  ActionRowBuilder,
  ButtonBuilder,
  ButtonStyle,
} = require("discord.js");
const { createVerifyRequest } = require("../lib/backendClient");

const COLOR = 0x2b6cb0;
const COLOR_ERROR = 0xe53e3e;

async function hasAgreedRules(interaction) {
  const channelId = process.env.RULES_CHANNEL_ID;
  const messageId = process.env.RULES_MESSAGE_ID;
  const emoji = process.env.RULES_EMOJI || "✅";
  if (!channelId || !messageId) return false;

  const channel = await interaction.guild.channels.fetch(channelId);
  const message = await channel.messages.fetch(messageId);
  const reaction = message.reactions.cache.find(
    (r) => r.emoji.name === emoji || r.emoji.toString() === emoji
  );
  if (!reaction) return false;

  const users = await reaction.users.fetch();
  return users.has(interaction.user.id);
}

module.exports = {
  data: new SlashCommandBuilder()
    .setName("인증")
    .setDescription("Hive 계정으로 컴프야v26 인증을 진행합니다."),

  async execute(interaction) {
    await interaction.deferReply({ ephemeral: true });

    let agreed;
    try {
      agreed = await hasAgreedRules(interaction);
    } catch (err) {
      console.error(err);
      await interaction.editReply({
        embeds: [
          new EmbedBuilder()
            .setColor(COLOR_ERROR)
            .setTitle("확인 실패")
            .setDescription("규칙 동의 여부를 확인하는 중 오류가 발생했습니다. 관리자에게 문의해주세요."),
        ],
      });
      return;
    }

    if (!agreed) {
      await interaction.editReply({
        embeds: [
          new EmbedBuilder()
            .setColor(COLOR_ERROR)
            .setTitle("규칙 동의가 필요합니다")
            .setDescription("먼저 규칙 메시지에 반응(체크)해주세요. 완료 후 다시 `/인증`을 실행해주세요."),
        ],
      });
      return;
    }

    let result;
    try {
      result = await createVerifyRequest(interaction.user.id, interaction.guildId);
    } catch (err) {
      console.error(err);
      await interaction.editReply({
        embeds: [
          new EmbedBuilder()
            .setColor(COLOR_ERROR)
            .setTitle("인증 처리 실패")
            .setDescription("잠시 후 다시 시도해주세요."),
        ],
      });
      return;
    }

    if (result.mode === "hive") {
      const embed = new EmbedBuilder()
        .setColor(COLOR)
        .setTitle("컴프야v26 인증")
        .setDescription("아래 버튼을 눌러 Hive 계정으로 로그인해주세요.")
        .setFooter({ text: "링크는 10분간 유효합니다." });

      const row = new ActionRowBuilder().addComponents(
        new ButtonBuilder()
          .setLabel("Hive로 인증하기")
          .setStyle(ButtonStyle.Link)
          .setURL(result.verify_url)
      );

      await interaction.editReply({ embeds: [embed], components: [row] });
      return;
    }

    // mode === "rules": Hive 연동 전이라 규칙 체크만으로 인증 완료 처리됨
    const embed = new EmbedBuilder()
      .setColor(result.role_granted ? COLOR : 0xecc94b)
      .setTitle("인증 완료")
      .setDescription(
        "규칙 확인으로 인증이 완료되었습니다.\n(Hive 연동 전이라 팀/오버롤 정보는 `/스탯설정`으로 운영자가 등록해줘야 표시됩니다.)"
      );
    if (!result.role_granted) {
      embed.addFields({ name: "⚠️ 역할 부여 실패", value: "관리자에게 문의해주세요." });
    }

    await interaction.editReply({ embeds: [embed] });
  },
};
