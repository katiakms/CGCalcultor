# CG Calculator

Aplicativo feito em **Python + Kivy** para calcular o Centro de Gravidade (CG) de planadores/aeromodelos, cadastrar diferentes planadores com seus parâmetros de referência e manter um histórico de medições.

## ✈️ Funcionalidades

- **Cadastro de planadores**: crie, edite e exclua planadores, cada um com seus parâmetros de referência (`x`, `c`, `x 1/4`, `PN`).
- **Cálculo de CG**: informe o peso da frente (`P_frente`), o peso da traseira (`P_tras`) e a distância de medição (`L`) para obter:
  - Peso total (`P_total`)
  - Posição do CG (`x_cg`)
  - CG relativo à referência (`x_bar_cg`)
  - CMA % (posição do CG em relação à corda média aerodinâmica)
  - Margem estática (`SM`)
- **Comentários**: adicione uma observação livre sobre cada medição calculada.
- **Armazenamento de medições**: guarde os resultados de cada cálculo (com data e comentário) no histórico do planador.
- **Histórico por planador**: consulte todas as medições já salvas de um planador específico, com opção de exclusão individual (com confirmação).

## 📋 Requisitos

- Python 3
- [Kivy](https://kivy.org/)

Instalação das dependências (ambiente de desenvolvimento):

```bash
pip install kivy
```

## ▶️ Executando no computador

```bash
python3 main.py
```

Os dados são salvos automaticamente em dois arquivos JSON, criados na mesma pasta do app:

| Arquivo             | Conteúdo                                            |
|---------------------|------------------------------------------------------|
| `planadores.json`   | Planadores cadastrados e seus parâmetros de referência |
| `medicoes.json`      | Histórico de medições calculadas e armazenadas       |

## 📱 Gerando o APK (Android)

O app é empacotado para Android usando o [Buildozer](https://buildozer.readthedocs.io/).

1. Instale o Buildozer:
   ```bash
   pip install --user buildozer cython
   ```
2. Dentro da pasta do projeto (onde estão `main.py` e `buildozer.spec`), rode:
   ```bash
   buildozer -v android debug
   ```
3. O APK gerado fica em `bin/`.
4. Transfira o `.apk` para o celular e instale (é necessário permitir "instalar de fontes desconhecidas" no Android).

> A primeira build baixa o Android SDK/NDK automaticamente e pode demorar bastante — as próximas execuções são bem mais rápidas.

## 🗂️ Estrutura do projeto

```
.
├── main.py            # Código-fonte do app (interface + lógica)
├── buildozer.spec      # Configuração de build para Android
├── planadores.json     # Gerado automaticamente ao rodar o app
└── medicoes.json        # Gerado automaticamente ao armazenar medições
```

## 🧮 Fórmulas utilizadas

```
Xcg      = (P_tras * L) / (P_frente + P_tras) + Dfix
Xcg_bar  = Xcg - x
CMA %    = Xcg_bar / c
SM       = Xcg_bar - PN
P_total  = P_frente + P_tras
```

Onde `x`, `c`, `x_1_4` e `PN` são os parâmetros de referência cadastrados para cada planador, e `Dfix` é uma constante de ajuste (17).
