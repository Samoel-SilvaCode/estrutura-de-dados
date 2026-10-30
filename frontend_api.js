/*
  Integração inicial do HTML com a API Python.
  1) Altere API_BASE_URL para a URL que o Render fornecer.
  2) Inclua este arquivo no HTML ANTES do script principal do jogo:
     <script src="frontend_api.js"></script>
  3) Use window.ContadinhoAPI nas funções do jogo.

  Este arquivo contém somente a URL pública da API. Nunca coloque aqui
  SUPABASE_SECRET_KEY ou service_role.
*/
const API_BASE_URL = "https://estrutura-de-dados-1.onrender.com";

async function apiRequest(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    }
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || `Erro HTTP ${response.status}`);
  }
  return data;
}

window.ContadinhoAPI = {
  registerPlayer(identifier) {
    return apiRequest("/api/players", {
      method: "POST",
      body: JSON.stringify({ identifier })
    });
  },

  getProgress(identifier) {
    return apiRequest(`/api/players/${encodeURIComponent(identifier)}/progress`);
  },

  usePower(identifier, powerKey) {
    return apiRequest(
      `/api/players/${encodeURIComponent(identifier)}/powers/${encodeURIComponent(powerKey)}/use`,
      { method: "POST", body: "{}" }
    );
  },

  finishPhase(identifier, phaseNumber, result) {
    return apiRequest(
      `/api/players/${encodeURIComponent(identifier)}/phases/${phaseNumber}/finish`,
      { method: "POST", body: JSON.stringify(result) }
    );
  },

  getRanking() {
    return apiRequest("/api/ranking");
  }
};
