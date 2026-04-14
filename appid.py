import requests
import time

# --- CONFIGURAÇÕES ---
API_KEY = "6bbe01d6e68c62d80afc9638b575e68d"  # Coloque sua chave da OpenWeatherMap
CIDADE = "Sao Paulo"
URL = f"http://api.openweathermap.org/data/2.5/weather?q={CIDADE}&appid={API_KEY}&units=metric&lang=pt_br"

def consultar_clima():
    print(f"\nConsultando clima para: {CIDADE}...")
    try:
        resposta = requests.get(URL)
        dados = resposta.json()

        if resposta.status_code == 200:
            temp = dados['main']['temp']
            clima = dados['weather'][0]['description'].upper()
            clima_principal = dados['weather'][0]['main'] # Rain, Clear, Clouds, etc.

            print(f"SUCESSO! | Temperatura: {temp}°C | {clima}")

            # Lógica de Decisão para enviar ao Wokwi
            if clima_principal == "Rain":
                print(">> [ALERTA] Chuva detectada! Digite 'C' no Wokwi.")
            else:
                print(">> [INFO] Sem chuva. Digite 'S' no Wokwi.")
        else:
            print(f"ERRO na API: {dados.get('message', 'Erro desconhecido')}")
            
    except Exception as e:
        print(f"Falha na conexão: {e}")

# Loop de verificação (a cada 30 segundos)
if __name__ == "__main__":
    print("--- FarmTech Solutions: Integrador de Clima ---")
    while True:
        consultar_clima()
        print("\nPróxima verificação em 30 segundos... (Ctrl+C para parar)")
        time.sleep(30)