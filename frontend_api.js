/*
 * Cliente da API do Contadinho.
 * Este arquivo deve ficar na mesma pasta do index.html.
 * A URL abaixo é a URL pública do serviço FastAPI no Render.
 * Nunca coloque SUPABASE_SECRET_KEY ou service_role no frontend.
 */
const API_BASE_URL = "https://estrutura-de-dados-1.onrender.com";

async function apiRequest(path, options = {}) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {})
      }
    });
  } catch (cause) {
    const error = new Error("Falha de rede ou CORS ao acessar a API. Confira o serviço no Render e FRONTEND_ORIGINS.");
    error.cause = cause;
    throw error;
  }

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(data.detail || `Erro HTTP ${response.status}`);
    error.status = response.status;
    error.data = data;
    throw error;
  }
  return data;
}

window.ContadinhoAPI = Object.freeze({
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
});
