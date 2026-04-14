# FarmTech Solutions - Sistema Inteligente de Fertirrigação 🌾

Este projeto faz parte da **Fase 2** do curso de Inteligência Artificial da **FIAP**. A solução consiste em um sistema de monitoramento e controle automatizado para culturas agrícolas (foco em Soja), utilizando IoT para gerir umidade, pH e nutrientes (NPK), integrado com dados climáticos externos.

## 📋 Sumário

- [Visão Geral](#visão-geral)
- [Arquitetura do Sistema](#arquitetura-do-sistema)
- [Funcionalidades](#funcionalidades)
- [Itens Ir Além](#itens-ir-além)
- [Como Executar](#como-executar)
- [Links do Projeto](#links-do-projeto)

## 🔍 Visão Geral

O sistema utiliza um **ESP32** para monitorar sensores de solo. A decisão de acionamento da bomba de irrigação (Relé) baseia-se em uma lógica de múltiplas variáveis: se a umidade estiver baixa, se o pH estiver fora da faixa ideal (6.0 - 6.5) ou se houver falta de nutrientes (N, P ou K), a irrigação é ativada.

## 🏗️ Arquitetura do Sistema

O projeto foi dividido em duas camadas principais:

1. **Hardware (Edge):** ESP32 programado em C++ controlando Sensores (DHT22, LDR, Switches) e Atuador (Relé).
2. **Integração (Python):** Script que consome a API OpenWeather para fornecer dados em tempo real sobre

## 🚀 Funcionalidades

- **Monitoramento de Umidade:** Leitura via sensor DHT22.
- **Controle de pH:** Simulação via sensor LDR (mapeado de 0 a 14).
- **Gestão de Nutrientes:** Monitoramento de Nitrogênio, Fósforo e Potássio via chaves seletoras.
- **Automação de Irrigação:** Acionamento inteligente do Relé.

## 🌟 Itens Ir Além

### 1. Integração com API Externa (Python)

Desenvolvemos um script em Python que monitora o clima local. Caso a API detecte previsão de chuva, o sistema suspende a irrigação automaticamente para economizar recursos hídricos, mesmo que o solo esteja seco.

## 🛠️ Como Executar

### 1. Hardware (Wokwi)

- Acesse o link do projeto no Wokwi.
- Clique em "Play" para iniciar a simulação.
- Acompanhe as leituras no **Serial Monitor**.

### 2. API de Clima (Python)

- Instale as dependências: `pip install requests`
- Execute o script: `python python/appid.py`
- Siga as instruções no terminal para interagir com o simulador.

## 🔗 Links do Projeto

- **Vídeo de Demonstração:** [INSIRA O SEU LINK DO YOUTUBE/DRIVE AQUI]
- **Simulador Wokwi:** [https://wokwi.com/projects/461289392904235009]
- **Repositório GitHub:** [Link deste repositório]

## Imagens do Projeto

## 👥 Integrantes

Grupo Fiap
Leandro Tenorio:
RM: RM572083
E-mail: tenorioleandro22@gmail.com

---

Nicolas:
RM: 570336
E-mail: nicxaviercosta04@gmail.com

---

Diego:
RM572085
E-mail: dhinobrega@hotmail.com.br

---

Pedro: RM573999
E-mail: pedrohenriquelimaschneider082@gmail.com

---

João:
RM: 570160
E-mail: jpbessa2007@gmail.com

---

_FarmTech Solutions - Tecnologia a serviço do campo._
