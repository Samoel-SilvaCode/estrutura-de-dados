# Backend Python do Contadinho

Este pacote é o ponto de partida para separar o projeto em três partes:

- **GitHub Pages:** publica o HTML, CSS, JavaScript, imagens e áudio.
- **Render:** executa a API Python/FastAPI.
- **Supabase:** armazena jogadores, poderes usados, resultados das fases e ranking geral.

> GitHub Pages é hospedagem estática. Ele não executa Python no servidor. Por isso, a API precisa ser publicada em outro serviço.

## Conteúdo

- `api/main.py`: API FastAPI.
- `requirements.txt`: bibliotecas Python.
- `supabase_schema.sql`: estrutura do banco de dados e ranking.
- `.env.example`: modelo das variáveis secretas.
- `frontend_api.js`: chamadas JavaScript para conversar com a API.

## 1. Criar o banco Supabase

1. Crie um projeto em https://supabase.com/dashboard.
2. Abra **SQL Editor**.
3. Crie uma nova query.
4. Cole e execute `supabase_schema.sql`.
5. Em **Project Settings / API** (ou **API Keys**, dependendo da interface), copie a Project URL e crie/copiei uma **Secret key** para uso no backend.
6. Não coloque a Secret key no HTML, no GitHub Pages nem no `frontend_api.js`.

O identificador `ABC-123` é apenas um apelido público, não uma autenticação. Sem login/PIN, outra pessoa pode se passar por um jogador. Para proteger a identidade e o progresso, adicione autenticação antes de usar com dados reais de funcionários.

## 2. Rodar a API localmente (Windows PowerShell)

Abra o terminal dentro da pasta `contadinho_backend` e execute:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Abra o arquivo `.env` e preencha:

```env
SUPABASE_URL=https://SEU-PROJETO.supabase.co
SUPABASE_SECRET_KEY=sb_secret_SUA_CHAVE_SECRETA
FRONTEND_ORIGINS=http://127.0.0.1:5500,http://localhost:5500,https://SEU_USUARIO.github.io
```

Inicie:

```powershell
uvicorn api.main:app --reload
```

Teste no navegador:

- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/docs`

Se o Python não encontrar o módulo, confirme que o terminal está na pasta `contadinho_backend`.

## 3. Publicar a API no Render

1. Envie a pasta `contadinho_backend` para um repositório GitHub separado (ou use essa pasta como raiz de um repositório próprio).
2. Crie uma conta em https://dashboard.render.com.
3. Escolha **New > Web Service** e conecte o repositório do backend.
4. Configure:
   - Runtime: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
5. Em **Environment**, adicione `SUPABASE_URL`, `SUPABASE_SECRET_KEY` e `FRONTEND_ORIGINS`.
6. Em `FRONTEND_ORIGINS`, coloque a origem do GitHub Pages, por exemplo `https://SEU_USUARIO.github.io` (sem `/nome-do-repositorio`).
7. Faça o deploy.
8. Teste `https://SUA-API.onrender.com/health` e `https://SUA-API.onrender.com/docs`.

## 4. Preparar o HTML

1. Copie `frontend_api.js` para a mesma pasta de `index.html`.
2. Abra `frontend_api.js` e troque `https://SUA-API.onrender.com` pela URL real da API.
3. Adicione `<script src="frontend_api.js"></script>` antes do script principal do jogo.
4. O frontend pode usar `window.ContadinhoAPI`:

```javascript
// Registrar o jogador depois de formar o identificador, por exemplo SAM-456:
const progresso = await ContadinhoAPI.registerPlayer("SAM-456");

// Buscar progresso e poderes que já foram usados:
const progressoAtual = await ContadinhoAPI.getProgress("SAM-456");

// Marcar um poder como usado (o servidor impede o segundo uso):
await ContadinhoAPI.usePower("SAM-456", "peek");

// Registrar o encerramento de uma fase (fase começa em 1 na API):
await ContadinhoAPI.finishPhase("SAM-456", 1, {
  score: 320,
  elapsed_seconds: 42,
  moves: 8,
  won: true
});

// Carregar o ranking geral:
const dadosRanking = await ContadinhoAPI.getRanking();
console.log(dadosRanking.ranking);
```

## 5. Publicar o jogo no GitHub Pages

O repositório do frontend deve conter `index.html`, imagens, `contadinho.aac`, favicon e `frontend_api.js`. Não envie `.env` nem chaves secretas.

No GitHub: **Settings > Pages > Deploy from a branch > main > /(root) > Save**.

## Endpoints disponíveis

| Método | Rota | Finalidade |
|---|---|---|
| GET | `/health` | Verificar API |
| POST | `/api/players` | Registrar/obter jogador |
| GET | `/api/players/{identifier}/progress` | Consultar progresso e poderes usados |
| POST | `/api/players/{identifier}/powers/{power_key}/use` | Consumir poder uma única vez |
| POST | `/api/players/{identifier}/phases/{phase}/finish` | Registrar a fase uma única vez |
| GET | `/api/ranking` | Ranking geral |

## Observações importantes antes de lançar

- O backend impede registrar novamente o mesmo poder e a mesma fase para o mesmo identificador.
- A API exige que a fase anterior esteja registrada antes de aceitar a seguinte.
- O identificador `ABC-123` não prova quem é a pessoa. Para evitar que alguém use a matrícula abreviada de outra pessoa, implemente Supabase Auth ou PIN individual validado no servidor.
- Nesta primeira versão, o navegador envia pontuação, tempo e movimentos. Uma pessoa tecnicamente experiente poderia falsificar esses valores. Para um ranking competitivo confiável, a API precisa controlar a sessão e validar as ações da partida no servidor.
- O pacote é um início de integração; o HTML atual ainda precisa trocar os salvamentos locais (`localStorage`) pelas chamadas `ContadinhoAPI` nos momentos de cadastro, uso do poder, fim de fase, carregamento do progresso e abertura do ranking.
