const BACKEND_URL = process.env.BACKEND_URL;
const INTERNAL_API_KEY = process.env.INTERNAL_API_KEY;

async function backendFetch(path, options = {}) {
  const res = await fetch(`${BACKEND_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-Internal-Key": INTERNAL_API_KEY,
      ...(options.headers || {}),
    },
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`backend ${path} 실패 (${res.status}): ${body}`);
  }
  return res.status === 204 ? null : res.json();
}

function createVerifyRequest(discordId, guildId) {
  return backendFetch("/internal/verify-requests", {
    method: "POST",
    body: JSON.stringify({ discord_id: discordId, guild_id: guildId }),
  });
}

function getLeaderboard(guildId) {
  return backendFetch(`/internal/leaderboard?guild_id=${encodeURIComponent(guildId)}`);
}

function updateUserStats(discordId, teamName, overall) {
  return backendFetch(`/internal/users/${encodeURIComponent(discordId)}`, {
    method: "PATCH",
    body: JSON.stringify({ team_name: teamName, overall }),
  });
}

module.exports = { createVerifyRequest, getLeaderboard, updateUserStats };
