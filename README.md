# MCP Demo - Model Context Protocol

Um exemplo prático de como um agente de IA (Claude) coordena múltiplos **MCP Servers** para integrar e cruzar dados de diferentes sistemas corporativos (ERP + CRM).

## 🎯 O que é MCP?

**Model Context Protocol** é um padrão aberto que permite que um agente de IA chame ferramentas/APIs de múltiplos sistemas de forma estruturada e segura.

Neste projeto, o agente:
1. **Entende** a pergunta em linguagem natural
2. **Decide** quais dados precisa
3. **Chama** os MCP Servers apropriados
4. **Cruza** os dados de diferentes fontes
5. **Retorna** uma resposta consolidada

## 📋 Como funciona?

### Fluxo MCP

```
Pergunta do usuário
    ↓
[Agente] Interpreta (Claude ou Regex)
    ↓
[MCP Client] Roteia chamadas
    ↓
[MCP Server ERP] Consulta contas a receber
[MCP Server CRM] Consulta histórico de contatos
[MCP Server Público] Consulta API pública (geolocalização)
    ↓
[Agente] Cruza dados de todas as fontes
    ↓
Resposta consolidada com dados enriquecidos
```

### Exemplo Real

**Pergunta:** "Quais clientes têm mais de R$ 30 mil em aberto e não tiveram contato há mais de 45 dias?"

**O agente então:**
1. Extrai: `valor_minimo=30000`, `dias=45`
2. Chama Server ERP → Retorna 6 clientes com saldo > R$ 30k
3. Chama Server CRM → Filtra para apenas sem contato > 45 dias
4. Chama API Pública (Open-Meteo) → Obtém dados de geolocalização de cada cidade
5. Cruza os dados → Retorna 4 clientes com informações enriquecidas

## 🚀 Como rodar

### Modo DEMO (sem custo)
```bash
python MCP.py
```

Funciona imediatamente! Usa regex para interpretar perguntas.

### Modo Claude AI (com IA real)

1. **Obtenha chave de API em:** https://console.anthropic.com/
   - Crie conta
   - Gere chave (R$5 crédito grátis/mês)

2. **Edite `.env`:**
   ```
   ANTHROPIC_API_KEY=sk-ant-v1-...
   ```

3. **Rode:**
   ```bash
   python MCP.py
   ```

## 📂 Estrutura

```
MCP.py
├── ERP_CONTAS_A_RECEBER      # Base de dados ERP simulada
├── CRM_ULTIMO_CONTATO        # Base de dados CRM simulada
├── MCPServerERP              # MCP Server do ERP
├── MCPServerCRM              # MCP Server do CRM
├── MCPServerPúblicoAPI       # MCP Server que integra API pública (Open-Meteo)
├── mcp_client_dispatch()     # Cliente que roteia chamadas
├── interpretar_pergunta()    # Agente interpreta (Claude ou regex)
└── executar_fluxo()          # Orquestra o fluxo completo
```

## 💡 Por que MCP?

| Problema | Solução MCP |
|----------|------------|
| Integração manual com N sistemas | Cliente único com interface padronizada |
| Lógica espalhada | Lógica centralizada no agente |
| Difícil de manter | Fácil de escalar novos servers |
| Sem segurança | RBAC e autenticação por server |
| Dados silados | Enriquecimento com APIs públicas |

## 🌐 API Pública Integrada

Este projeto demonstra como MCP integra dados corporativos com APIs públicas reais:

- **API:** Open-Meteo Geocoding (https://geocoding-api.open-meteo.com/)
- **Função:** Enriquece dados de clientes com localização geográfica
- **Dados:** Coordenadas (latitude/longitude), fuso horário, país/região

### Como funciona:

1. Sistema identifica cidades dos clientes
2. Chama API pública para cada cidade
3. Retorna dados de geolocalização (timezone, país, etc.)
4. Consolida com dados ERP/CRM para resposta final

### Benefícios:

- ✅ Demonstra integração com APIs externas reais
- ✅ Sem autenticação necessária (API pública)
- ✅ Dados dinâmicos e sempre atualizados
- ✅ Padrão reutilizável para outras APIs

## 📊 Saída esperada

```
------------------------------------------------------------
Pergunta: Quais clientes têm mais de R$ 30 mil em aberto e não tiveram contato há mais de 45 dias?
------------------------------------------------------------

[Claude AI] Interpretando: "..."
[Claude AI] Extraído: valor_minimo=R$ 30,000.00 | dias=45

[MCP Client] Encaminhando: 'consultar_contas_a_receber'
  [MCP Server ERP] Retornando 6 cliente(s).

[MCP Client] Encaminhando: 'consultar_ultimo_contato'
  [MCP Server CRM] Retornando 4 cliente(s) que atendem ao critério.

[Claude AI] Cruzando dados do ERP com dados do CRM...

[Claude AI] Enriquecendo dados com API pública...

[MCP Client] Encaminhando: 'consultar_localizacao_api'
  [MCP Server Público] Consultando API: https://geocoding-api.open-meteo.com/
  [Resultado] Brasília - Brazil - America/Sao_Paulo

------------------------------------------------------------
Resultado:
------------------------------------------------------------
Achei 4 cliente(s).
Maior: Construtora Horizonte - R$ 187,400.00, 62 dias sem contato

Todos:
  • Construtora Horizonte: R$ 187,400.00, 62 dias (resp: João Silva) (São Paulo, Brazil - America/Sao_Paulo)
  • Indústria Vale Verde: R$ 64,800.00, 47 dias (resp: Marcos Souza) (Brasília, Brazil - America/Sao_Paulo)
  • Atacado Nova Era: R$ 41,200.00, 58 dias (resp: João Silva) (Curitiba, Brazil - America/Sao_Paulo)
  • Distribuidora Aurora: R$ 31,250.00, 51 dias (resp: Beatriz Lima) (Belo Horizonte, Brazil - America/Sao_Paulo)
```

## 🧪 Customizar

Edite a pergunta em `if __name__ == "__main__":`:

```python
pergunta = "Quais clientes têm mais de R$ 50 mil e 60 dias sem contato?"
```

## ⚙️ Requisitos

- Python 3.9+
- `requests` (para chamadas HTTP à API pública)
- `anthropic` (para Claude) - opcional
- `python-dotenv` (para .env) - opcional

## 📝 Notas

- Este é um **exemplo educacional** da arquitetura MCP
- Em produção, os MCP Servers seriam processos reais com autenticação própria
- O "Agente" pode ser Claude, GPT-4, ou outro modelo LLM
- Os dados são simulados apenas para demonstração

## 🔗 Links

- [Documentação MCP](https://modelcontextprotocol.io/)
- [Claude API](https://console.anthropic.com/)

