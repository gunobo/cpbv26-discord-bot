const { ActionRowBuilder, ButtonBuilder, ButtonStyle } = require("discord.js");
const { createVerifyRequest } = require("../lib/backendClient");

const CUSTOM_ID = "agree_rules";

async function handleAgreeButton(interaction) {
  await interaction.deferReply({ ephemeral: true });

  let verifyUrl;
  try {
    const result = await createVerifyRequest(interaction.user.id, interaction.guildId);
    verifyUrl = result.verify_url;
  } catch (err) {
    console.error(err);
    await interaction.editReply("인증 링크를 만드는 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.");
    return;
  }

  const row = new ActionRowBuilder().addComponents(
    new ButtonBuilder().setLabel("Hive로 인증하기").setStyle(ButtonStyle.Link).setURL(verifyUrl)
  );

  await interaction.editReply({
    content: "아래 버튼을 눌러 Hive 계정으로 로그인해주세요. 링크는 10분간 유효합니다.",
    components: [row],
  });
}

module.exports = { CUSTOM_ID, handleAgreeButton };
