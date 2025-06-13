pip install gTTS
# Oi! Vamos começar importando as ferramentas (bibliotecas) que a gente vai precisar.
# O 'graphviz' pra desenhar nosso autômato.
# O 'gradio' pra criar a interface web super fácil.
# O 'gtts' (Google Text-to-Speech) pra fazer a mágica da voz.
# E o 'os', que é uma biblioteca padrão do Python, útil para interagir com o sistema operacional.
import graphviz
import gradio as gr
from gtts import gTTS
import os

#------------------------------------------------------------------------------------
# ESTRUTURA DO AUTÔMATO
#------------------------------------------------------------------------------------

# Essa classe aqui é como se fosse um "tijolinho" do nosso autômato.
# Cada 'Estado' é uma bolinha no nosso desenho.
# Ele tem um 'id' único pra gente não se perder e um dicionário de 'transicoes'
# pra saber pra onde ele pode ir com cada símbolo.
class Estado:
    _id_counter = 0

    def __init__(self):
        self.id = Estado._id_counter
        Estado._id_counter += 1
        self.transicoes = {}

    def adicionar_transicao(self, simbolo, estado):
        if simbolo not in self.transicoes:
            self.transicoes[simbolo] = []
        self.transicoes[simbolo].append(estado)

# Pensa nisso aqui como um "mini-autômato" ou um "pedaço de construção".
# É um bloco que tem um estado de 'inicio' e um de 'fim' bem definidos.
# A gente vai usar isso pra montar o autômato final, como se fosse um Lego.
class Fragmento:
    def __init__(self, inicio, fim):
        self.inicio = inicio
        self.fim = fim

#------------------------------------------------------------------------------------
# LÓGICA DE CONVERSÃO E CONSTRUÇÃO
#------------------------------------------------------------------------------------

# Essa função é um pouco mais teórica, mas a ideia é simples:
# ela pega a expressão que a gente escreve (ex: "(a|b)*abb") e a reorganiza
# para um formato que o computador consegue processar de forma mais lógica,
# chamado de notação "pós-fixa".
# Ela também é super esperta e adiciona o operador de concatenação (o ".")
# automaticamente onde ele está implícito (ex: "ab" vira "a.b").
def para_posfixa(expressao):
    precedencia = {'*': 3, '.': 2, '|': 1}
    saida = []
    pilha = []
    anterior = None

    def eh_literal(c):
        return c not in {'*', '|', '.', '(', ')'}

    for c in expressao:
        if eh_literal(c):
            if anterior and (eh_literal(anterior) or anterior in {')', '*'}):
                while pilha and precedencia.get('.', 0) <= precedencia.get(pilha[-1], 0):
                    saida.append(pilha.pop())
                pilha.append('.')
            saida.append(c)
        elif c == '(':
            if anterior and (eh_literal(anterior) or anterior in {')', '*'}):
                while pilha and precedencia.get('.', 0) <= precedencia.get(pilha[-1], 0):
                    saida.append(pilha.pop())
                pilha.append('.')
            pilha.append(c)
        elif c == ')':
            while pilha and pilha[-1] != '(':
                saida.append(pilha.pop())
            pilha.pop()
        else:
            while pilha and precedencia.get(c, 0) <= precedencia.get(pilha[-1], 0):
                saida.append(pilha.pop())
            pilha.append(c)
        anterior = c

    while pilha:
        saida.append(pilha.pop())
    return saida

# Aqui é onde a mágica principal acontece! 🧠
# Essa é a implementação do famoso Algoritmo de Thompson.
# A gente lê a expressão já em pós-fixo e, para cada letra ou operador,
# a gente constrói um pedacinho do autômato usando nossos 'Fragmentos'.
# É como montar uma maquete, peça por peça.
def thompson(posfixa):
    pilha = []
    passos = [] # Aqui a gente guarda o passo a passo pra mostrar pro usuário.
    for token in posfixa:
        if token == '*': # Se for o asterisco (fecho de Kleene)
            frag = pilha.pop()
            inicio, fim = Estado(), Estado()
            inicio.adicionar_transicao('ε', frag.inicio)
            inicio.adicionar_transicao('ε', fim)
            frag.fim.adicionar_transicao('ε', frag.inicio)
            frag.fim.adicionar_transicao('ε', fim)
            pilha.append(Fragmento(inicio, fim))
            passos.append(f"Operador '*': Criado laço com início {inicio.id} e fim {fim.id}.")
        elif token == '.': # Se for o ponto (concatenação)
            frag2, frag1 = pilha.pop(), pilha.pop()
            frag1.fim.adicionar_transicao('ε', frag2.inicio)
            pilha.append(Fragmento(frag1.inicio, frag2.fim))
            passos.append(f"Operador '.': Concatenado fim {frag1.fim.id} com início {frag2.inicio.id}.")
        elif token == '|': # Se for a barra (união/ou)
            frag2, frag1 = pilha.pop(), pilha.pop()
            inicio, fim = Estado(), Estado()
            inicio.adicionar_transicao('ε', frag1.inicio)
            inicio.adicionar_transicao('ε', frag2.inicio)
            frag1.fim.adicionar_transicao('ε', fim)
            frag2.fim.adicionar_transicao('ε', fim)
            pilha.append(Fragmento(inicio, fim))
            passos.append(f"Operador '|': União com novo início {inicio.id} e fim {fim.id}.")
        else: # Se for uma letra ou número (literal)
            inicio, fim = Estado(), Estado()
            inicio.adicionar_transicao(token, fim)
            pilha.append(Fragmento(inicio, fim))
            passos.append(f"Símbolo '{token}': Transição direta de {inicio.id} -> {fim.id}.")
    return pilha.pop(), passos

# Depois que o autômato está pronto, essa função entra em ação pra desenhar ele
# bonitinho pra gente usando o Graphviz. 🎨
# Ela visita cada estado, desenha as bolinhas e as setas, e marca o estado inicial
# com uma seta e o final com um círculo duplo.
def desenhar_afn(estado_inicial, estado_final):
    dot = graphviz.Digraph(format='png')
    visitados = set()
    def visitar(estado):
        if estado.id in visitados: return
        visitados.add(estado.id)
        forma = 'doublecircle' if estado == estado_final else 'circle'
        dot.node(str(estado.id), shape=forma)
        for simbolo, estados in estado.transicoes.items():
            for s in estados:
                dot.edge(str(estado.id), str(s.id), label=simbolo)
                visitar(s)
    dot.node('', shape='point')
    dot.edge('', str(estado_inicial.id))
    visitar(estado_inicial)
    return dot.render('nfa_thompson', view=False)

# Essa função é o nosso "testador". Ela pega a palavra que o usuário digitou
# e tenta "caminhar" pelo autômato seguindo as transições. Se ela conseguir
# chegar no estado final depois de ler a palavra toda, a palavra é 'ACEITA'! ✨
def simular_afn(inicio, fim, palavra):
    def dfs(atual, i, visitados):
        if (atual.id, i) in visitados: return False
        visitados.add((atual.id, i))
        if i == len(palavra):
            if atual == fim: return True
            for proximo in atual.transicoes.get('ε', []):
                if dfs(proximo, i, visitados): return True
        else:
            for proximo in atual.transicoes.get(palavra[i], []):
                if dfs(proximo, i + 1, visitados): return True
            for proximo in atual.transicoes.get('ε', []):
                if dfs(proximo, i, visitados): return True
        return False
    return dfs(inicio, 0, set())

#------------------------------------------------------------------------------------
# FUNÇÕES DE INTERFACE (ligação entre a lógica e a tela)
#------------------------------------------------------------------------------------

# Essa é a função "maestra" que rege a orquestra quando a gente clica no botão principal. 🎶
# Ela chama todas as outras funções na ordem certa: converte pra pós-fixo,
# constrói com Thompson, desenha o grafo, simula a palavra e até gera o áudio de anúncio.
def gerar_automato_interface(expressao, palavra):
    if not expressao:
        return "Erro: expressão vazia!", None, [], None

    Estado._id_counter = 0
    try:
        posfixa = para_posfixa(expressao)
        fragmento, passos = thompson(posfixa)
        caminho_imagem = desenhar_afn(fragmento.inicio, fragmento.fim)

        texto_falado = "Gráfico gerado: Autômato Finito Não-determinístico"
        tts = gTTS(text=texto_falado, lang='pt-br')
        caminho_audio = "anuncio_automato.mp3"
        tts.save(caminho_audio)

        if palavra.strip() == "":
            resultado = "Digite uma palavra para testar."
        else:
            aceita = simular_afn(fragmento.inicio, fragmento.fim, palavra)
            resultado = f"Resultado: {'ACEITA' if aceita else 'REJEITA'}"

        return resultado, caminho_imagem, "\n".join(passos), caminho_audio
    except Exception as e:
        return f"Erro: {e}", None, [], None

# Essa é a função que a gente fez pra dar as sugestões pro usuário.
# Ela é chamada quando a gente clica no botão de sugestão.
def dar_sugestoes_por_voz():
    sugestoes = [
        "(a|b)*abb",
        "a*b*c*",
        "(0|1)+",
        "inicio(meio)*fim"
    ]
    texto_falado = "Olá! Aqui estão algumas sugestões para você testar. Tente: "
    texto_falado += ". Ou então: ".join(sugestoes)
    texto_para_exibir = "Experimente uma destas:\n\n" + "\n".join(sugestoes)
    tts = gTTS(text=texto_falado, lang='pt-br')
    caminho_audio_sugestoes = "sugestoes.mp3"
    tts.save(caminho_audio_sugestoes)
    return caminho_audio_sugestoes, texto_para_exibir

#------------------------------------------------------------------------------------
# MONTAGEM DA INTERFACE WEB
#------------------------------------------------------------------------------------

# E finalmente, a parte visual! Aqui a gente usa o `gr.Blocks` do Gradio
# para montar nossa página web, de forma bem estruturada.
with gr.Blocks(theme=gr.themes.Soft()) as interface:
    # Um título e uma descrição pra deixar a página bonita e informativa.
    gr.Markdown(
        """
        # Gerador de Autômatos com o Algoritmo de Thompson
        Digite uma expressão regular, veja o passo a passo da construção e o autômato gerado.
        Teste palavras para ver se são aceitas. Se precisar de ideias, clique no botão de sugestões!
        """
    )

    # A gente organiza os elementos em linhas e colunas para o layout ficar legal.
    with gr.Row():
        with gr.Column(scale=1):
            # O botão de sugestão e seus componentes de saída (áudio e texto).
            sugestao_btn = gr.Button("💡 Me dê sugestões!")
            audio_sugestoes = gr.Audio(label="Sugestões por Voz", autoplay=True)
            sugestao_texto = gr.Textbox(label="Sugestão Escrita", lines=6)

    gr.Markdown("---") # Uma linha pra separar as seções.

    with gr.Row():
        # A coluna da esquerda com as entradas e os resultados em texto.
        with gr.Column(scale=2):
            expressao_input = gr.Textbox(label="Expressão Regular (ex: (a|b)*abb)")
            palavra_input = gr.Textbox(label="Palavra para Testar")
            gerar_btn = gr.Button("Gerar Autômato e Testar Palavra")
            resultado_output = gr.Textbox(label="Resultado")
            passos_output = gr.Textbox(label="Passo a Passo da Construção", lines=10)

        # A coluna da direita com as saídas visuais e de áudio.
        with gr.Column(scale=3):
            imagem_output = gr.Image(type="filepath", label="Autômato Finito Não-determinístico (AFN)")
            audio_anuncio = gr.Audio(label="Anúncio do Gráfico", autoplay=True)

    # Agora a gente conecta os botões com as funções. É o que dá vida à interface!
    # Quando o botão 'gerar_btn' for clicado...
    gerar_btn.click(
        fn=gerar_automato_interface, # ...execute esta função...
        inputs=[expressao_input, palavra_input], # ...usando estas entradas...
        outputs=[resultado_output, imagem_output, passos_output, audio_anuncio] # ...e atualize estas saídas.
    )

    # E o mesmo para o botão de sugestão.
    sugestao_btn.click(
        fn=dar_sugestoes_por_voz,
        inputs=[],
        outputs=[audio_sugestoes, sugestao_texto]
    )

# Com tudo pronto, a gente manda o Gradio iniciar a aplicação web.
# O 'share=True' cria um link público temporário pra gente poder mostrar pra outras pessoas. Show!
interface.launch(share=True)
