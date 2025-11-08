import httpx
from bs4 import BeautifulSoup

def obter_credenciais_camara():
    url = "https://www.camarapoa.rs.gov.br/processos"
    
    # Headers pra simular um navegador real e evitar bloqueios imediatos
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        # 1. Requisição GET (usando Client para manter sessão se necessário futuramente)
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, headers=headers)
            response.raise_for_status() 

            print(f"✅ Conexão estabelecida! Status Code: {response.status_code}")

            # 2. Obter _session_id dos Cookies
            # Gerenciamento de cookies automatico por response.cookies
            session_id = response.cookies.get("_session_id")
            if session_id:
                 print(f"🍪 _session_id encontrado: {session_id[:10]}... (truncado)")
            else:
                 print("❌ _session_id não encontrado nos cookies.")

            # 3. Obter X-CSRF-Token da tag <meta>
            soup = BeautifulSoup(response.text, 'html.parser')
            
            csrf_meta = soup.find('meta', attrs={'name': 'csrf-token'})
            
            csrf_token = None
            if csrf_meta and csrf_meta.has_attr('content'):
                csrf_token = csrf_meta['content']
                print(f"🔑 X-CSRF-Token encontrado: {csrf_token[:10]}... (truncado)")
            else:
                print("❌ Meta tag csrf-token não encontrada.")

            return session_id, csrf_token

    except httpx.RequestError as e:
        print(f"Erro ao conectar na Câmara: {e}")
        return None, None

if __name__ == "__main__":
    sessao, token = obter_credenciais_camara()
    
    if sessao and token:
        print("\n--- Pronto para a próxima etapa ---")
        print("Use estas credenciais nos headers das suas próximas requisições (provavelmente POSTs para pesquisa).")
