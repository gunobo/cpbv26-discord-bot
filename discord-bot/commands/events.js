const { SlashCommandBuilder, EmbedBuilder } = require("discord.js");
const { getEvents } = require("../lib/backendClient");

const COLOR = 0x2b6cb0;
const COLOR_ERROR = 0xe53e3e;

module.exports = {
  data: new SlashCommandBuilder()
    .setName("진행이벤트")
    .setDescription("컴프야v26 공식 커뮤니티의 진행 중 이벤트 목록을 보여줍니다."),

  async execute(interaction) {
    await interaction.deferReply();

    let events;
    try {
      events = await getEvents();
    } catch (err) {
      console.error(err);
      await interaction.editReply({
        embeds: [
          new EmbedBuilder()
            .setColor(COLOR_ERROR)
            .setTitle("이벤트 목록을 불러오지 못했습니다")
            .setDescription("공식 커뮤니티 접속이 원활하지 않을 수 있습니다. 잠시 후 다시 시도해주세요."),
        ],
      });
      return;
    }

    if (events.length === 0) {
      await interaction.editReply({
        embeds: [
          new EmbedBuilder().setColor(COLOR).setTitle("진행 중 이벤트").setDescription("진행 중인 이벤트가 없습니다."),
        ],
      });
      return;
    }

    const lines = events.map((e) => `**[${e.title}](${e.url})**\n${e.regdate}`);

    const embed = new EmbedBuilder()
      .setColor(COLOR)
      .setTitle("컴프야v26 진행 중 이벤트")
      .setDescription(lines.join("\n\n"))
      .setFooter({ text: "출처: 컴프야v26 공식 커뮤니티" });

    await interaction.editReply({ embeds: [embed] });
  },
};
