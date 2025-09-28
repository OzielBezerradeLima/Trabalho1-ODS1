# Trabalho1-ODS1
Primeiro Trabalho Prático com o tema "Sistema de Recomendação com Filtragem Colaborativa" da Disciplina de Oficina de Desenvolvimento de Sistemas 1

# Criar e rodar o ambiente virtual

Versão do Python: 3.11.9
Qualquer versão 3.11.x já serve
Para verificar a versão utilize python --version

Criando o Ambiente Virtual
python -m venv venv 

Ativando o Ambiente Virtual
Windows: venv\Scripts\activate
Linux: source venv/bin/activate

Se estiver vendo um (venv), quer dizer que ele está funcionando

Baixando os requisitos
pip install -r requirements.txt

Desativando o Ambiente Virtual
deactivate

# Execução

Backend - FastAPI

(Não é preciso ativar o ambiente virtual)
cd backend
uvicorn app:app --reload

Frontend - Streamlit

(Com o ambiente virtual ativado)
cd frontend
streamlit run app_streamlit.py

Para parar de executar o frontend ou backend, basta apertar CTRL+C no terminal