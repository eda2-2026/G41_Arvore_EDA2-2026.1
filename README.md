🇧🇷 **Português** | 🇺🇸 [English](README-eng.md)

<H1> Trabalho de Estruturas de Dados - Sistema de Biblioteca (SB) 📚 </H1>

<p align="center">
  <img src="https://img.shields.io/badge/Status-Concluido-green?style=flat-square" alt="Status">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Árvores-BST%20%7C%20RBT%20%7C%20RBT--Intervalos-orange?style=flat-square" alt="Árvores">
</p>

<p align="center">
  <img src="https://i.postimg.cc/YCsvxJLN/Captura-de-Tela-2026-04-04-a-s-02-39-39.png" width="500">
</p>

---

## 📹 Vídeo explicando o projeto
[Vídeo do YouTube]()

---

## 📝 Descrição

O **Sistema de Biblioteca (SB)** é uma aplicação em Python pensada para ser rápida e fácil de usar. Com uma interface moderna em modo escuro, ele foi projetado para que a navegação e a organização do acervo aconteçam de forma fluida, sem travamentos ou esperas desnecessárias.

Nesta nova versão, o foco principal do sistema é a **estruturação e busca eficiente dos dados por meio de árvores**. Para lidar com diferentes necessidades de consulta, busca por ID, busca textual e detecção de conflitos de datas em empréstimos, o sistema implementa três estruturas de árvore distintas: **BST**, **Árvore Rubro-Negra (RBT)** e **RBT de Intervalos**.

No fim, o sistema consegue indexar, localizar e verificar conflitos em grandes quantidades de livros e empréstimos instantaneamente, mantendo um equilíbrio perfeito entre eficiência algorítmica e uma experiência de uso simples e agradável no dia a dia.

## 💡 Diferenciais Técnicos - Estruturas de Árvore

O grande destaque desta atualização é o Módulo de Índices, que utiliza diferentes estruturas de árvore dependendo da operação realizada no sistema:

- **BST (Árvore Binária de Busca):** Implementada como estrutura base de indexação de livros por numeração (ID). Garante busca exata em O(log n) médio e busca por intervalo de IDs em O(log n + k). Permanece no projeto como referência, sua limitação de O(n) no pior caso (inserções em ordem crescente) justifica e documenta a necessidade da RBT.

- **RBT (Árvore Rubro-Negra):** Substitui a BST como estrutura principal de indexação, garantindo balanceamento automático após toda inserção e remoção. Mantém as três invariantes clássicas (raiz preta, sem filhos vermelhos consecutivos, mesma contagem de nós pretos em todo caminho raiz→folha), altura máxima de 2·log₂(n+1) e custo O(log n) garantido no pior caso, inclusive para inserções em ordem crescente. Utiliza nó sentinela `_nil` compartilhado para evitar verificações de `None` espalhadas no código.

- **RBT de Intervalos:** Extensão da RBT padrão para armazenar períodos de empréstimo `[inicio, fim]`. Cada nó mantém um campo extra `max_fim` a maior data de devolução de toda a sua subárvore que permite descartar ramos inteiros durante a busca por sobreposição. Aplicada para verificar, em O(log n), se um livro já está emprestado no mesmo período antes de registrar um novo empréstimo.

## 🌐 Demonstração

<p align="center">
  <img src="https://i.postimg.cc/SNcGH7Z9/image.png" width="600">
  <br></br>
  <img src="https://i.postimg.cc/3RPgcdmp/image.png" width="600">
  <br></br>
  <img src="https://i.postimg.cc/ncKv3VzW/image.png" width="600">
  <br></br>
  <img src="https://i.postimg.cc/L5tZQvH8/image.png" width="600">
</p>

## 🎯 Funcionalidades

- **Busca por ID:** A RBT indexa todos os livros por numeração e realiza buscas exatas e por intervalo de IDs em O(log n).
- **Detecção de Conflito de Empréstimo:** A RBT de Intervalos verifica em O(log n) se um livro já está emprestado em um determinado período, usando o campo `max_fim` para podar ramos irrelevantes.
- **Gestão de Acervo:** Cadastro detalhado de livros, com título, autor, gênero e estoque.
- **Registro de Alunos:** Controle centralizado de usuários, armazenando matrículas e dados de contato de forma segura.
- **Edição Dinâmica:** Permite alterar informações de livros e alunos já cadastrados, mantendo a base de dados sempre atualizada.
- **Controle de Empréstimos e Popularidade:** Registro ágil de saídas, associando o aluno ao livro e contabilizando automaticamente a quantidade de vezes que a obra foi emprestada.
- **Gestão de Devoluções e Avaliações:** Baixa automática de empréstimos com a funcionalidade integrada para o aluno registrar uma avaliação de 0 a 5 estrelas para a obra devolvida.

---

## 💻 Pré-requisitos

Antes de executar o programa, certifique-se de que você possui os seguintes requisitos instalados:

**1. Python 3.10 ou superior.**

**2. Dependências:**

- PySide6; e
- qdarktheme.

**3. Sistema Operacional: Windows, macOS ou Linux.**

---

## 🚀 Executando

**1. Instalar o Python**

Verifique se você possui o **Python 3.10 ou superior** instalado em seu sistema. Para isso, siga as instruções abaixo:

Abra o Terminal (no Windows, você pode abrir o Prompt de Comando ou PowerShell).

Digite o seguinte comando para verificar a versão do Python:

```bash
python --version
```

**Ou**

```bash
python3 --version
```

Se não tiver o Python 3.10, você pode baixá-lo [aqui](https://www.python.org/downloads/).

**2. Clonar o Repositório**

Primeiro, clone o repositório do projeto para a sua máquina. Para isso, abra o terminal (ou prompt de comando no Windows) e execute o comando abaixo:

```bash
git clone https://github.com/eda2-2026/G41_Ordenacao_EDA2-2026.1.git
```

**3. Instale as dependências:**

No terminal, navegue até o diretório onde o projeto foi baixado e execute o seguinte comando para instalar todas as dependências:

```bash
pip install -r requirements.txt
```

Se o arquivo **requirements.txt** não existir, você pode instalar as dependências manualmente.

- **Instalar o Pyside6**

```bash
pip install pyside6
```

- **Instalar o qdarktheme**

```bash
pip install qdarktheme
```

**4. Executar o programa**

Com o ambiente configurado e as dependências instaladas, agora você pode rodar o sistema.

```bash
python biblioteca.py
```

Ou

```bash
python3 biblioteca.py
```

**⚠️ Observação:**
Caso o código apresente algum erro durante a execução, verifique se todos os arquivos necessários estão presentes (principalmente os arquivos .json no diretório db_files).

---

## 🫂 Colaboradores

| [Camila Cavalcante - 232013944](https://github.com/CamilaSilvaC) | [Luísa Ferreira - 232014807](https://github.com/luisa12ll) |
| :---: | :---: |
| <div align="center"><img src="https://github.com/CamilaSilvaC.png" alt="camila" width="400"></div> | <div align="center"><img src="https://github.com/luisa12ll.png" alt="luisa" width="400"></div> |