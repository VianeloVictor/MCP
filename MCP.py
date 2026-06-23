"""Script MCP para testar integração ERP + CRM com Claude AI.

Caso de uso da Ana Lima (gestora financeira) procurando
clientes com saldo alto e sem contato há muito tempo.

Usa Claude (Anthropic) como agente de IA real para interpretar perguntas em linguagem natural.
Requer chave de API: export ANTHROPIC_API_KEY='sua-chave'
"""

import re
import os
import json
import requests
from anthropic import Anthropic
from dotenv import load_dotenv

# carrega variáveis de ambiente do .env
load_dotenv()

# dados do ERP (contas a receber)
ERP_CONTAS_A_RECEBER = [
    {"cliente_id": "C001", "nome": "Construtora Horizonte", "valor_aberto": 187400.00, "cidade": "Sao Paulo"},
    {"cliente_id": "C002", "nome": "Mercado Bom Preço", "valor_aberto": 52300.00, "cidade": "Rio de Janeiro"},
    {"cliente_id": "C003", "nome": "Distribuidora Aurora",   "valor_aberto": 31250.00, "cidade": "Belo Horizonte"},
    {"cliente_id": "C004", "nome": "Tech Supplies Ltda",     "valor_aberto": 8900.00, "cidade": "New York"},
    {"cliente_id": "C005", "nome": "Indústria Vale Verde",   "valor_aberto": 64800.00, "cidade": "Brasilia"},
    {"cliente_id": "C006", "nome": "Comércio Estrela",       "valor_aberto": 35600.00, "cidade": "Lisbon"},
    {"cliente_id": "C007", "nome": "Atacado Nova Era",       "valor_aberto": 41200.00, "cidade": "Curitiba"},
]

# histórico de contatos do CRM
CRM_ULTIMO_CONTATO = {
    "C001": {"dias_sem_contato": 62, "responsavel": "João Silva"},
    "C002": {"dias_sem_contato": 10, "responsavel": "Marcos Souza"},
    "C003": {"dias_sem_contato": 51, "responsavel": "Beatriz Lima"},
    "C004": {"dias_sem_contato": 5,  "responsavel": "João Silva"},
    "C005": {"dias_sem_contato": 47, "responsavel": "Marcos Souza"},
    "C006": {"dias_sem_contato": 12, "responsavel": "Beatriz Lima"},
    "C007": {"dias_sem_contato": 58, "responsavel": "João Silva"},
}

# simulando os MCP servers
class MCPServerERP:
    @staticmethod
    def consultar_contas_a_receber(valor_minimo: float) -> list:
        print(f"  [MCP Server ERP] Autenticação validada. "
              f"Consultando contas a receber >= R$ {valor_minimo:,.2f}")
        resultado = [c for c in ERP_CONTAS_A_RECEBER if c["valor_aberto"] >= valor_minimo]
        print(f"  [MCP Server ERP] Retornando {len(resultado)} cliente(s).")
        return resultado


class MCPServerCRM:
    @staticmethod
    def consultar_ultimo_contato(cliente_ids: list, dias_minimo_sem_contato: int) -> list:
        print(f"  [MCP Server CRM] Autenticação validada. "
              f"Filtrando clientes sem contato há >= {dias_minimo_sem_contato} dias")
        resultado = []
        for cid in cliente_ids:
            info = CRM_ULTIMO_CONTATO.get(cid)
            if info and info["dias_sem_contato"] >= dias_minimo_sem_contato:
                resultado.append({"cliente_id": cid, **info})
        print(f"  [MCP Server CRM] Retornando {len(resultado)} cliente(s) que atendem ao critério.")
        return resultado


class MCPServerPúblicoAPI:
    """MCP Server que consulta API pública real - Open-Meteo Geocoding"""
    
    @staticmethod
    def consultar_localizacao(cidade: str) -> dict:
        """Consulta coordenadas e informações da cidade via API pública (Open-Meteo)"""
        print(f"  [MCP Server Público] Consultando API: https://geocoding-api.open-meteo.com/")
        try:
            response = requests.get(
                f"https://geocoding-api.open-meteo.com/v1/search?name={cidade}&count=1&language=en", 
                timeout=10
            )
            if response.status_code == 200:
                resultado = response.json()
                if resultado.get('results'):
                    cidade_data = resultado['results'][0]
                    return {
                        "cidade": cidade_data.get("name", cidade),
                        "pais": cidade_data.get("country", "N/A"),
                        "latitude": cidade_data.get("latitude", "N/A"),
                        "longitude": cidade_data.get("longitude", "N/A"),
                        "regiao": cidade_data.get("admin1", "N/A"),
                        "timezone": cidade_data.get("timezone", "N/A")
                    }
                else:
                    return {"cidade": cidade, "status": "Nao encontrado"}
            else:
                return {"cidade": cidade, "status": "API error"}
        except Exception as e:
            print(f"    [Erro na API] {str(e)}")
            return {"cidade": cidade, "status": "Conexao falhou"}
def mcp_client_dispatch(tool_name: str, tool_input: dict) -> dict:
    print(f"\n[MCP Client] Encaminhando: '{tool_name}'")
    print(f"[MCP Client] Parâmetros: {tool_input}")

    if tool_name == "consultar_contas_a_receber":
        dados = MCPServerERP.consultar_contas_a_receber(
            valor_minimo=tool_input["valor_minimo"]
        )
        return {"clientes": dados}

    if tool_name == "consultar_ultimo_contato":
        dados = MCPServerCRM.consultar_ultimo_contato(
            cliente_ids=tool_input["cliente_ids"],
            dias_minimo_sem_contato=tool_input["dias_minimo_sem_contato"],
        )
        return {"contatos": dados}

    if tool_name == "consultar_localizacao_api":
        dados = MCPServerPúblicoAPI.consultar_localizacao(
            cidade=tool_input["cidade"]
        )
        return {"localizacao": dados}

    raise ValueError(f"Ferramenta desconhecida: {tool_name}")

# inicializa cliente Claude
def get_claude_client():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or api_key == "":
        print("[AVISO] ANTHROPIC_API_KEY não definida. Usando modo DEMO (simulado).")
        return None
    return Anthropic(api_key=api_key)


# função que usa Claude para interpretar a pergunta
def interpretar_pergunta(pergunta: str) -> dict:
    print(f"\n[Claude AI] Interpretando: \"{pergunta}\"")

    client = get_claude_client()
    
    # Se não tiver chave, usa simulação
    if client is None:
        print("[Claude AI - DEMO] Simulando interpretação (sem API real)...")
        # Tenta extrair com regex como fallback
        match_valor = re.search(r"(\d+)\s*mil", pergunta)
        if match_valor:
            valor_minimo = float(match_valor.group(1)) * 1000
        else:
            match_valor = re.search(r"R?\$?\s*([\d.,]+)", pergunta)
            valor_minimo = float(match_valor.group(1).replace(".", "").replace(",", ".")) if match_valor else 0

        match_dias = re.search(r"(\d+)\s*dias", pergunta)
        dias_sem_contato = int(match_dias.group(1)) if match_dias else 30
        
        resultado = {"valor_minimo": int(valor_minimo), "dias_sem_contato": dias_sem_contato}
    else:
        prompt = f"""Analise a seguinte pergunta em português e extraia os parâmetros solicitados.
    
Pergunta: "{pergunta}"

Retorne APENAS um JSON válido (sem markdown, sem explicações) com estes campos:
- valor_minimo: valor mínimo em reais mencionado na pergunta (número inteiro, ex: 30000)
- dias_sem_contato: número de dias sem contato mencionado (número inteiro, padrão 30 se não especificado)

Exemplo de resposta:
{{"valor_minimo": 30000, "dias_sem_contato": 45}}"""

        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=200,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        resultado_texto = response.content[0].text.strip()
        resultado = json.loads(resultado_texto)
    
    print(f"[Claude AI] Extraído: valor_minimo=R$ {resultado['valor_minimo']:,.2f} | dias={resultado['dias_sem_contato']}")
    
    return resultado

    return {"valor_minimo": valor_minimo, "dias_sem_contato": dias_sem_contato}


def gerar_resposta_final(clientes_filtrados: list) -> str:
    if len(clientes_filtrados) == 0:
        return "Nada encontrado com esses critérios."

    # ordena por valor (maior pra menor)
    clientes_ordenados = sorted(clientes_filtrados, key=lambda c: c["valor_aberto"], reverse=True)
    maior = clientes_ordenados[0]

    linhas = [
        f"Achei {len(clientes_filtrados)} cliente(s).",
        f"Maior: {maior['nome']} - R$ {maior['valor_aberto']:,.2f}, {maior['dias_sem_contato']} dias sem contato (resp: {maior['responsavel']}).",
        "",
        "Todos:",
    ]
    for c in clientes_ordenados:
        info_local = c.get("info_localizacao", {})
        local_str = f" ({info_local.get('cidade', 'N/A')}, {info_local.get('pais', 'N/A')} - {info_local.get('timezone', 'N/A')})" if info_local else ""
        linhas.append(f"  • {c['nome']}: R$ {c['valor_aberto']:,.2f}, "
                     f"{c['dias_sem_contato']} dias (resp: {c['responsavel']}){local_str}")

    return "\n".join(linhas)

# fluxo principal
def executar_fluxo(pergunta_usuario: str) -> str:
    print("-" * 60)
    print(f"Pergunta: {pergunta_usuario}")
    print("-" * 60)

    # parseia a pergunta
    parametros = interpretar_pergunta(pergunta_usuario)

    # consulta o ERP
    res_erp = mcp_client_dispatch(
        "consultar_contas_a_receber",
        {"valor_minimo": parametros["valor_minimo"]},
    )
    clientes_erp = res_erp["clientes"]
    ids = [c["cliente_id"] for c in clientes_erp]

    # consulta o CRM
    res_crm = mcp_client_dispatch(
        "consultar_ultimo_contato",
        {"cliente_ids": ids, "dias_minimo_sem_contato": parametros["dias_sem_contato"]},
    )
    contatos = {c["cliente_id"]: c for c in res_crm["contatos"]}

    # cruza os dados
    print("\n[Claude AI] Cruzando dados do ERP com dados do CRM...")
    resultado = []
    for cliente in clientes_erp:
        info = contatos.get(cliente["cliente_id"])
        if info:
            resultado.append({**cliente, **info})

    # consulta API pública para enriquecer dados
    print("\n[Claude AI] Enriquecendo dados com API pública...")
    cidades_unicas = set(c.get("cidade", "Sao Paulo") for c in resultado)
    cache_localizacoes = {}
    
    for cidade in cidades_unicas:
        res_api = mcp_client_dispatch(
            "consultar_localizacao_api",
            {"cidade": cidade}
        )
        cache_localizacoes[cidade] = res_api["localizacao"]
    
    # adiciona informações de localização aos clientes
    for cliente in resultado:
        cidade = cliente.get("cidade", "Sao Paulo")
        cliente["info_localizacao"] = cache_localizacoes.get(cidade, {})

    return gerar_resposta_final(resultado)

# main
if __name__ == "__main__":
    pergunta = "Quais clientes têm mais de R$ 30 mil em aberto e não tiveram contato há mais de 45 dias?"
    resposta = executar_fluxo(pergunta)
    print("\n" + "-" * 60)
    print("Resultado:")
    print("-" * 60)
    print(resposta)
