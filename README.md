# Trabalho1-ODS1

**Primeiro Trabalho Prático** com o tema **"Sistema de Recomendação com Filtragem Colaborativa"** da disciplina **Oficina de Desenvolvimento de Sistemas 1**.

---
## Objetivo do Sistema 
O objetivo principal deste sistema é ser uma plataforma inteligente de recomendação de mangás. Utilizando o histórico de avaliações de cada usuário, a aplicação constrói um perfil de preferências detalhado. A partir desse perfil, nosso algoritmo analisa o banco de dados e sugere novos títulos com alta probabilidade de agradar ao leitor, garantindo uma descoberta de conteúdo personalizada e eficaz.
---

## Criar e rodar o ambiente virtual

**Versão do Python:** 3.11.9  
Qualquer versão **3.11.x** é compatível.  
Para verificar a versão:

```bash
python --version
```

***Criando o Ambiente Virtual***

```bash
python -m venv venv
```
 
***Ativando o Ambiente Virtual***

Windows: 

```bash
venv\Scripts\activate
```

Linux: 

```bash
source venv/bin/activate
```

Se estiver vendo um (venv), quer dizer que ele está funcionando

***Baixando os requisitos***

```bash
pip install -r requirements.txt
```

***Desativando o Ambiente Virtual***

```bash
deactivate
```

## Execução

**Backend - FastAPI**

***Não é preciso ativar o ambiente virtual***

```bash
cd backend
uvicorn app:app --reload
```

**Frontend - Streamlit**

***Com o ambiente virtual ativado***

```bash
cd frontend
streamlit run app_streamlit.py
```

***Para parar de executar o frontend ou backend, basta apertar CTRL+C no terminal***

## Explicação da Lógica de Recomendação

O sistema utiliza uma abordagem de **Filtragem Colaborativa Item-Item (Item-Based Collaborative Filtering)**. A lógica principal está implementada no arquivo `recommender.py` e segue os seguintes passos:

1.  **Matriz Usuário-Item**: Primeiramente, o sistema constrói uma matriz onde as linhas representam os usuários e as colunas representam os mangás (itens). O valor em cada célula é a nota que um usuário deu a um mangá específico. Células vazias (itens não avaliados) são preenchidas com 0.
2.  **Cálculo de Similaridade entre Itens**: Em seguida, o sistema calcula uma matriz de similaridade entre todos os mangás. Isso é feito para determinar o quão "parecido" um mangá é de outro, com base nas notas que eles receberam de todos os usuários. Se muitos usuários que gostaram de "Naruto" também gostaram de "Bleach", por exemplo, esses dois itens terão uma alta similaridade.
3.  **Geração de Recomendações**: Para gerar recomendações para um usuário específico, o sistema:
    * Identifica os mangás que o usuário ainda **não avaliou**.
    * Para cada mangá não avaliado, ele calcula uma "nota prevista". Essa nota é uma média ponderada das notas que o usuário deu para *outros* mangás. Os pesos nessa média são as similaridades entre o mangá não avaliado e cada mangá que o usuário já avaliou.
    * Por fim, o sistema ordena os mangás não avaliados pela maior nota prevista e retorna os melhores classificados (`top_n`) como recomendação.

## Justificativa da Métrica de Similaridade Usada

A métrica de similaridade implementada é a **Similaridade de Cosseno (Cosine Similarity)**.

* **O que é?** A similaridade de cosseno mede o cosseno do ângulo entre dois vetores. No nosso caso, cada mangá pode ser representado como um vetor contendo todas as notas que recebeu dos usuários. A métrica, então, calcula o quão "próximos" esses vetores estão em termos de direção.
* **Por que foi usada?** Essa é uma das métricas mais tradicionais e eficazes para sistemas de recomendação. Ela é particularmente útil para encontrar itens com padrões de avaliação semelhantes, independentemente da magnitude das notas. Por exemplo, se um grupo de usuários tende a dar notas altas para os mesmos dois mangás, a similaridade de cosseno entre eles será alta. É uma abordagem robusta e computacionalmente eficiente para capturar a relação de gostos entre os itens.

## Cálculo e Análise da Acurácia

A acurácia do modelo é avaliada através de uma simulação para um usuário específico, conforme implementado na função `evaluate_accuracy`.

1.  **Divisão Treino-Teste**: As avaliações de um usuário são divididas aleatoriamente em dois conjuntos: um de **treino** e um de **teste**. Para garantir que o resultado seja sempre o mesmo para um mesmo usuário, a divisão é feita com um estado aleatório fixo (`random_state=42`).
2.  **Simulação**: O sistema "esconde" o conjunto de teste e gera recomendações para o usuário usando apenas os dados do conjunto de treino.
3.  **Verificação (Hits)**: Em seguida, ele verifica quais itens do conjunto de teste foram avaliados positivamente pelo usuário (nota maior ou igual a 4). Estes são considerados os "gabaritos" ou o que o modelo deveria ter acertado.
4.  **Cálculo da Métrica**: A acurácia é calculada como a quantidade de itens que aparecem **tanto** na lista de recomendações **quanto** na lista de "favoritos" do teste (os *hits*), dividida pelo número total de recomendações geradas.

* **Análise**: Essa métrica, similar à **Precisão**, avalia o quão relevantes foram as recomendações. Um resultado de **20%**, por exemplo, significa que 1 a cada 5 itens recomendados era algo que o usuário comprovadamente gostava (com base nos dados de teste).

Ao realizar a primeira avaliação formal do nosso sistema de recomendação, chegamos a uma acurácia geral de 7,37%. Embora este número possa parecer baixo à primeira vista, ele é fundamental como um ponto de partida (baseline) e nos forneceu um diagnóstico muito claro sobre o estado atual do modelo. A nossa análise indica que a principal causa para este resultado é um desafio clássico em sistemas de recomendação: a esparsidade dos dados. Isso significa que, com o número ainda limitado de avaliações por usuário, o algoritmo tem dificuldade em encontrar padrões robustos e identificar outros usuários com gostos similares de forma eficaz. Dessa forma, este número não é visto como uma falha, mas sim como um diagnóstico preciso que nos aponta o caminho para as próximas otimizações. Com base nisso, os próximos passos já estão definidos, começando pela implementação de uma abordagem híbrida que utilizará metadados dos mangás (gênero, autor e tags) para contornar a falta de avaliações. Adicionalmente, planejo explorar algoritmos mais avançados, como os de Fatoração de Matrizes (SVD), que são projetados para lidar com dados esparsos. Estou confiante de que a implementação dessas melhorias resultará em um aumento significativo na acurácia e na qualidade das recomendações futuras.
