import os
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st


CSV_PADRAO = "dados_sensores.csv"
ARQUIVO_ENV = Path(".env")
UMIDADE_MINIMA = 60.0
PH_MIN = 6.0
PH_MAX = 6.5


COLUNAS_ESPERADAS = [
    "data_hora",
    "timestamp_ms",
    "umidade",
    "ph",
    "n_ok",
    "p_ok",
    "k_ok",
    "chuva_prevista",
    "bomba",
]


def formatar_numero(valor, casas=1, sufixo=""):
    if pd.isna(valor):
        return "Sem dado"
    return f"{float(valor):.{casas}f}{sufixo}"


def valor_binario(valor, padrao=0):
    if pd.isna(valor):
        return padrao
    try:
        return 1 if int(valor) == 1 else 0
    except (TypeError, ValueError):
        return padrao


def status_ok(valor):
    if pd.isna(valor):
        return "Sem dado"
    return "OK" if valor_binario(valor) == 1 else "Baixo"


def classe_irrigacao(valor):
    texto = str(valor).strip().upper()
    if texto == "LIGADA":
        return "LIGADA"
    if texto == "DESLIGADA":
        return "DESLIGADA"
    return "DESCONHECIDA"


def ler_dados(caminho_csv):
    caminho = Path(caminho_csv)
    if not caminho.exists():
        return pd.DataFrame(columns=COLUNAS_ESPERADAS), f"Arquivo nao encontrado: {caminho}"

    try:
        dados = pd.read_csv(caminho)
    except Exception as erro:
        return pd.DataFrame(columns=COLUNAS_ESPERADAS), f"Falha ao ler CSV: {erro}"

    colunas_faltando = [coluna for coluna in COLUNAS_ESPERADAS if coluna not in dados.columns]
    if colunas_faltando:
        return (
            pd.DataFrame(columns=COLUNAS_ESPERADAS),
            "Colunas ausentes no CSV: " + ", ".join(colunas_faltando),
        )

    if dados.empty:
        return pd.DataFrame(columns=COLUNAS_ESPERADAS), "CSV sem registros."

    dados = dados[COLUNAS_ESPERADAS].copy()
    dados["data_hora"] = pd.to_datetime(dados["data_hora"], errors="coerce")

    for coluna in ["timestamp_ms", "umidade", "ph", "n_ok", "p_ok", "k_ok", "chuva_prevista"]:
        dados[coluna] = pd.to_numeric(dados[coluna], errors="coerce")

    dados["bomba"] = dados["bomba"].fillna("DESCONHECIDA").astype(str).str.upper()
    dados["tempo_s"] = dados["timestamp_ms"] / 1000

    if dados["data_hora"].nunique(dropna=True) > 1:
        dados["eixo_tempo"] = dados["data_hora"]
        titulo_eixo = "Horario"
    else:
        dados["eixo_tempo"] = dados["tempo_s"]
        titulo_eixo = "Tempo de simulacao (s)"

    return dados, titulo_eixo


def limpar_valor_env(valor):
    return valor.strip().strip('"').strip("'")


def ler_chave_dotenv(caminho=ARQUIVO_ENV):
    if not caminho.exists():
        return ""

    for linha in caminho.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue

        nome, valor = linha.split("=", 1)
        if nome.strip() == "OPENWEATHER_API_KEY":
            return limpar_valor_env(valor)

    return ""


def obter_chave_openweather():
    chave_ambiente = os.environ.get("OPENWEATHER_API_KEY", "").strip()
    if chave_ambiente:
        return chave_ambiente, "variavel de ambiente"

    chave_dotenv = ler_chave_dotenv()
    if chave_dotenv:
        return chave_dotenv, ".env"

    try:
        chave_secrets = st.secrets.get("OPENWEATHER_API_KEY", "").strip()
        if chave_secrets:
            return chave_secrets, "Streamlit secrets"
    except Exception:
        pass

    return "", ""


@st.cache_data(ttl=600)
def consultar_clima(cidade, api_key):
    if not cidade or not api_key:
        return None

    resposta = requests.get(
        "https://api.openweathermap.org/data/2.5/weather",
        params={
            "q": cidade,
            "appid": api_key,
            "units": "metric",
            "lang": "pt_br",
        },
        timeout=10,
    )
    resposta.raise_for_status()
    payload = resposta.json()
    clima = payload["weather"][0]
    clima_principal = clima.get("main", "")
    descricao = clima.get("description", "").capitalize()
    chuva_detectada = clima_principal in {"Rain", "Drizzle", "Thunderstorm"} or bool(payload.get("rain"))

    return {
        "cidade": payload.get("name", cidade),
        "temperatura": payload.get("main", {}).get("temp"),
        "umidade_ar": payload.get("main", {}).get("humidity"),
        "clima": clima_principal,
        "descricao": descricao,
        "chuva": chuva_detectada,
    }


def montar_sugestoes(ultima_leitura, clima):
    sugestoes = []
    chuva_sensor = valor_binario(ultima_leitura.get("chuva_prevista", 0)) == 1
    chuva_clima = bool(clima["chuva"]) if clima else None
    chuva_considerada = chuva_clima if chuva_clima is not None else chuva_sensor
    origem_chuva = "OpenWeather" if chuva_clima is not None else "CSV"

    umidade = ultima_leitura.get("umidade")
    ph = ultima_leitura.get("ph")
    p_ok = ultima_leitura.get("p_ok")
    k_ok = ultima_leitura.get("k_ok")
    bomba = classe_irrigacao(ultima_leitura.get("bomba"))

    if chuva_considerada:
        sugestoes.append(
            (
                "warning",
                f"Suspender irrigacao: chuva detectada ou prevista pela origem {origem_chuva}.",
            )
        )
    elif pd.notna(umidade) and umidade < UMIDADE_MINIMA:
        sugestoes.append(
            (
                "error",
                f"Irrigar agora: umidade em {umidade:.1f}%, abaixo do minimo de {UMIDADE_MINIMA:.0f}%.",
            )
        )
    else:
        sugestoes.append(("success", "Manter irrigacao sob monitoramento: umidade dentro do limite."))

    if pd.notna(ph) and not (PH_MIN <= ph <= PH_MAX):
        sugestoes.append(
            (
                "warning",
                f"Ajustar pH do solo: leitura em {ph:.1f}, fora da faixa ideal de {PH_MIN:.1f} a {PH_MAX:.1f}.",
            )
        )

    nutrientes_baixos = []
    if pd.notna(p_ok) and valor_binario(p_ok) == 0:
        nutrientes_baixos.append("P")
    if pd.notna(k_ok) and valor_binario(k_ok) == 0:
        nutrientes_baixos.append("K")

    if nutrientes_baixos:
        sugestoes.append(
            (
                "warning",
                "Repor nutrientes antes da proxima fertirrigacao: " + ", ".join(nutrientes_baixos) + ".",
            )
        )

    if chuva_considerada and bomba == "LIGADA":
        sugestoes.append(("error", "Bomba ligada com chuva prevista: revisar acionamento para evitar desperdicio."))

    return sugestoes


def exibir_sugestoes(sugestoes):
    for tipo, texto in sugestoes:
        if tipo == "success":
            st.success(texto)
        elif tipo == "error":
            st.error(texto)
        else:
            st.warning(texto)


def grafico_umidade(dados, eixo_x, titulo_eixo):
    figura = go.Figure()
    figura.add_trace(
        go.Scatter(
            x=dados[eixo_x],
            y=dados["umidade"],
            mode="lines+markers",
            name="Umidade",
            line={"color": "#1f77b4", "width": 3},
        )
    )
    figura.add_hline(
        y=UMIDADE_MINIMA,
        line_dash="dash",
        line_color="#d62728",
        annotation_text="Minimo",
        annotation_position="top left",
    )
    figura.update_layout(
        title="Umidade do solo",
        xaxis_title=titulo_eixo,
        yaxis_title="Umidade (%)",
        margin={"l": 20, "r": 20, "t": 55, "b": 20},
        height=330,
    )
    return figura


def grafico_ph(dados, eixo_x, titulo_eixo):
    figura = go.Figure()
    figura.add_trace(
        go.Scatter(
            x=dados[eixo_x],
            y=dados["ph"],
            mode="lines+markers",
            name="pH",
            line={"color": "#2ca02c", "width": 3},
        )
    )
    figura.add_hrect(
        y0=PH_MIN,
        y1=PH_MAX,
        fillcolor="#2ca02c",
        opacity=0.16,
        line_width=0,
        annotation_text="Faixa ideal",
        annotation_position="top left",
    )
    figura.update_layout(
        title="pH do solo",
        xaxis_title=titulo_eixo,
        yaxis_title="pH",
        margin={"l": 20, "r": 20, "t": 55, "b": 20},
        height=330,
    )
    return figura


def grafico_irrigacao(dados, eixo_x, titulo_eixo):
    figura = go.Figure()
    figura.add_trace(
        go.Scatter(
            x=dados[eixo_x],
            y=dados["bomba"].eq("LIGADA").astype(int),
            mode="lines",
            name="Bomba ligada",
            line={"shape": "hv", "color": "#d62728", "width": 3},
        )
    )
    figura.add_trace(
        go.Scatter(
            x=dados[eixo_x],
            y=dados["chuva_prevista"].fillna(0),
            mode="lines",
            name="Chuva prevista",
            line={"shape": "hv", "color": "#17becf", "width": 2},
        )
    )
    figura.update_yaxes(
        tickmode="array",
        tickvals=[0, 1],
        ticktext=["Nao", "Sim"],
        range=[-0.15, 1.15],
    )
    figura.update_layout(
        title="Status da irrigacao e chuva",
        xaxis_title=titulo_eixo,
        yaxis_title="Status",
        margin={"l": 20, "r": 20, "t": 55, "b": 20},
        height=330,
    )
    return figura


def grafico_nutrientes(ultima_leitura):
    nutrientes = pd.DataFrame(
        {
            "nutriente": ["N", "P", "K"],
            "status": [
                valor_binario(ultima_leitura.get("n_ok", 0)),
                valor_binario(ultima_leitura.get("p_ok", 0)),
                valor_binario(ultima_leitura.get("k_ok", 0)),
            ],
        }
    )
    figura = go.Figure(
        go.Bar(
            x=nutrientes["nutriente"],
            y=nutrientes["status"],
            marker_color=["#7f7f7f" if valor == 0 else "#2ca02c" for valor in nutrientes["status"]],
            text=["OK" if valor == 1 else "Baixo" for valor in nutrientes["status"]],
            textposition="outside",
        )
    )
    figura.update_yaxes(
        tickmode="array",
        tickvals=[0, 1],
        ticktext=["Baixo", "OK"],
        range=[0, 1.2],
    )
    figura.update_layout(
        title="Nutrientes na ultima leitura",
        xaxis_title="Nutriente",
        yaxis_title="Status",
        margin={"l": 20, "r": 20, "t": 55, "b": 20},
        height=330,
    )
    return figura


def main():
    st.set_page_config(page_title="FarmTech Dashboard", layout="wide")

    st.title("FarmTech - Dashboard de Irrigacao")

    with st.sidebar:
        st.header("Dados")
        caminho_csv = st.text_input("Arquivo CSV", value=CSV_PADRAO)
        cidade = st.text_input("Cidade para clima", value="Sao Paulo")
        api_key, origem_chave = obter_chave_openweather()
        if origem_chave:
            st.caption(f"OpenWeather ativo via {origem_chave}.")
        else:
            st.caption("Configure OPENWEATHER_API_KEY para ativar o clima em tempo real.")
        st.button("Atualizar dados")

    dados, status_csv = ler_dados(caminho_csv)

    if dados.empty:
        st.error(status_csv if isinstance(status_csv, str) else "CSV sem registros.")
        st.stop()

    eixo_x = "eixo_tempo"
    titulo_eixo = status_csv
    ultima = dados.iloc[-1]

    try:
        clima = consultar_clima(cidade, api_key)
    except Exception as erro:
        clima = None
        st.warning(f"Clima indisponivel: {erro}")

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Umidade", formatar_numero(ultima["umidade"], sufixo="%"))
    col2.metric("pH", formatar_numero(ultima["ph"]))
    col3.metric("Fosforo (P)", status_ok(ultima["p_ok"]))
    col4.metric("Potassio (K)", status_ok(ultima["k_ok"]))
    col5.metric("Irrigacao", classe_irrigacao(ultima["bomba"]))

    clima_col, sugestao_col = st.columns([1, 2])

    with clima_col:
        st.subheader("Clima")
        if clima:
            st.metric("Cidade", clima["cidade"])
            st.metric("Temperatura", formatar_numero(clima["temperatura"], sufixo=" C"))
            st.metric("Umidade do ar", formatar_numero(clima["umidade_ar"], casas=0, sufixo="%"))
            st.metric("Condicao", clima["descricao"] or clima["clima"])
        else:
            chuva_csv = "Sim" if valor_binario(ultima.get("chuva_prevista", 0)) == 1 else "Nao"
            st.metric("Chuva prevista no CSV", chuva_csv)
            st.info("Configure OPENWEATHER_API_KEY para consultar o clima atual.")

    with sugestao_col:
        st.subheader("Sugestoes de irrigacao")
        exibir_sugestoes(montar_sugestoes(ultima, clima))

    graf_col1, graf_col2 = st.columns(2)
    graf_col1.plotly_chart(grafico_umidade(dados, eixo_x, titulo_eixo), use_container_width=True)
    graf_col2.plotly_chart(grafico_ph(dados, eixo_x, titulo_eixo), use_container_width=True)

    graf_col3, graf_col4 = st.columns(2)
    graf_col3.plotly_chart(grafico_irrigacao(dados, eixo_x, titulo_eixo), use_container_width=True)
    graf_col4.plotly_chart(grafico_nutrientes(ultima), use_container_width=True)

    st.dataframe(
        dados.sort_index(ascending=False),
        use_container_width=True,
        hide_index=True,
    )


if __name__ == "__main__":
    main()
