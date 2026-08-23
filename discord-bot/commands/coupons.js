const { SlashCommandBuilder, EmbedBuilder } = require("discord.js");
const { getCoupons } = require("../lib/backendClient");

const COLOR = 0x2b6cb0;
const COLOR_ERROR = 0xe53e3e;

function shortPeriod(period) {
  return period.replace(/\s*23:59\s*까지$/, "").trim();
}

function shortReward(reward) {
  const oneLine = reward.replace(/\n/g, ", ");
  return oneLine.length > 26 ? `${oneLine.slice(0, 25)}…` : oneLine;
}

function buildTable(coupons) {
  const codeW = Math.max(...coupons.map((c) => c.code.length), 4);
  const periodW = Math.max(...coupons.map((c) => shortPeriod(c.period).length), 4);

  const header = `${"코드".padEnd(codeW)}  ${"기간".padEnd(periodW)}  보상`;
  const rows = coupons.map(
    (c) => `${c.code.padEnd(codeW)}  ${shortPeriod(c.period).padEnd(periodW)}  ${shortReward(c.reward)}`
  );

  return "```\n" + [header, ...rows].join("\n") + "\n```";
}

module.exports = {
  data: new SlashCommandBuilder()
    .setName("쿠폰목록")
    .setDescription("컴프야v26 공식 커뮤니티에 등록된 사용 가능 쿠폰 목록을 보여줍니다."),

  async execute(interaction) {
    await interaction.deferReply();

    let coupons;
    try {
      coupons = await getCoupons();
    } catch (err) {
      console.error(err);
      await interaction.editReply({
        embeds: [
          new EmbedBuilder()
            .setColor(COLOR_ERROR)
            .setTitle("쿠폰 목록을 불러오지 못했습니다")
            .setDescription("공식 커뮤니티 접속이 원활하지 않을 수 있습니다. 잠시 후 다시 시도해주세요."),
        ],
      });
      return;
    }

    if (coupons.length === 0) {
      await interaction.editReply({
        embeds: [
          new EmbedBuilder().setColor(COLOR).setTitle("사용 가능 쿠폰").setDescription("현재 사용 가능한 쿠폰이 없습니다."),
        ],
      });
      return;
    }

    const links = coupons
      .filter((c) => c.url)
      .map((c) => `[${c.code}](${c.url})`)
      .join(" · ");

    const embed = new EmbedBuilder()
      .setColor(COLOR)
      .setTitle("컴프야v26 사용 가능 쿠폰")
      .setDescription(buildTable(coupons) + (links ? `\n🔗 등록 바로가기: ${links}` : ""))
      .setFooter({ text: "출처: 컴프야v26 공식 커뮤니티 · 계정당 1회만 사용 가능 · 보상이 여러 개면 일부만 표시됨" });

    await interaction.editReply({ embeds: [embed] });
  },
};
