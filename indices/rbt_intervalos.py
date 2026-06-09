from datetime import date

VERMELHO = True
PRETO = False


class NoIntervalo:
    

    def __init__(self, inicio: date, fim: date, dados: dict):
        self.inicio = inicio
        self.fim = fim
        self.max_fim = fim      # começa valendo o próprio fim
        self.dados = dict(dados)
        self.cor = VERMELHO
        self.pai = None
        self.esq = None
        self.dir = None


class RBTIntervalos:
    

    def __init__(self):
        # Sentinela NIL compartilhado por toda a árvore
        self._nil = NoIntervalo(date.min, date.min, {})
        self._nil.cor = PRETO
        self._nil.max_fim = date.min
        self._nil.esq = self._nil
        self._nil.dir = self._nil
        self._nil.pai = self._nil

        self.raiz = self._nil

   

    def _atualizar_max_fim(self, no: NoIntervalo):
        
        no.max_fim = max(
            no.fim,
            no.esq.max_fim,
            no.dir.max_fim,
        )

    
    #  Rotações                   

    def _rotacao_esquerda(self, x: NoIntervalo):
        y = x.dir
        x.dir = y.esq

        if y.esq is not self._nil:
            y.esq.pai = x

        y.pai = x.pai

        if x.pai is self._nil:
            self.raiz = y
        elif x is x.pai.esq:
            x.pai.esq = y
        else:
            x.pai.dir = y

        y.esq = x
        x.pai = y

        
        self._atualizar_max_fim(x)
        self._atualizar_max_fim(y)

    def _rotacao_direita(self, y: NoIntervalo):
        x = y.esq
        y.esq = x.dir

        if x.dir is not self._nil:
            x.dir.pai = y

        x.pai = y.pai

        if y.pai is self._nil:
            self.raiz = x
        elif y is y.pai.dir:
            y.pai.dir = x
        else:
            y.pai.esq = x

        x.dir = y
        y.pai = x

        self._atualizar_max_fim(y)
        self._atualizar_max_fim(x)

    
    #  Inserção                                                       

    def inserir(self, inicio: date, fim: date, dados: dict):
       
        novo = NoIntervalo(inicio, fim, dados)
        novo.esq = self._nil
        novo.dir = self._nil
        novo.pai = self._nil

        pai = self._nil
        atual = self.raiz

        while atual is not self._nil:
            pai = atual
            if inicio < atual.inicio:
                atual = atual.esq
            else:
                atual = atual.dir

        novo.pai = pai

        if pai is self._nil:
            self.raiz = novo
        elif inicio < pai.inicio:
            pai.esq = novo
        else:
            pai.dir = novo

        self._propagar_max_fim(novo.pai)
        self._corrigir_insercao(novo)

    def _propagar_max_fim(self, no: NoIntervalo):
        
        while no is not self._nil:
            self._atualizar_max_fim(no)
            no = no.pai

    def _corrigir_insercao(self, z: NoIntervalo):
        
        while z.pai.cor == VERMELHO:
            if z.pai is z.pai.pai.esq:
                tio = z.pai.pai.dir
                if tio.cor == VERMELHO:             # Caso 1
                    z.pai.cor = PRETO
                    tio.cor = PRETO
                    z.pai.pai.cor = VERMELHO
                    z = z.pai.pai
                else:
                    if z is z.pai.dir:              # Caso 2
                        z = z.pai
                        self._rotacao_esquerda(z)
                    z.pai.cor = PRETO               # Caso 3
                    z.pai.pai.cor = VERMELHO
                    self._rotacao_direita(z.pai.pai)
            else:
                tio = z.pai.pai.esq
                if tio.cor == VERMELHO:
                    z.pai.cor = PRETO
                    tio.cor = PRETO
                    z.pai.pai.cor = VERMELHO
                    z = z.pai.pai
                else:
                    if z is z.pai.esq:
                        z = z.pai
                        self._rotacao_direita(z)
                    z.pai.cor = PRETO
                    z.pai.pai.cor = VERMELHO
                    self._rotacao_esquerda(z.pai.pai)

        self.raiz.cor = PRETO


    def buscar_sobreposicao(
        self, inicio: date, fim: date
    ) -> dict | None:
        
        return self._buscar(self.raiz, inicio, fim)

    def _sobrepoe(self, no: NoIntervalo, inicio: date, fim: date) -> bool:
        return no.inicio <= fim and inicio <= no.fim

    def _buscar(
        self, no: NoIntervalo, inicio: date, fim: date
    ) -> dict | None:
        while no is not self._nil:
            if self._sobrepoe(no, inicio, fim):
                return no.dados          # conflito encontrado

            
            if no.esq is not self._nil and no.esq.max_fim >= inicio:
                no = no.esq
            else:
                no = no.dir

        return None


    def remover_por_chave(self, chave: str):
      
        alvo = self._encontrar_por_chave(self.raiz, chave)
        if alvo is not None:
            self._remover_no(alvo)

    def _encontrar_por_chave(
        self, no: NoIntervalo, chave: str
    ) -> NoIntervalo | None:
        if no is self._nil:
            return None
        if no.dados.get("chave") == chave:
            return no
        esq = self._encontrar_por_chave(no.esq, chave)
        return esq if esq else self._encontrar_por_chave(no.dir, chave)

    def _minimo(self, no: NoIntervalo) -> NoIntervalo:
        while no.esq is not self._nil:
            no = no.esq
        return no

    def _transplantar(self, u: NoIntervalo, v: NoIntervalo):
        if u.pai is self._nil:
            self.raiz = v
        elif u is u.pai.esq:
            u.pai.esq = v
        else:
            u.pai.dir = v
        v.pai = u.pai

    def _remover_no(self, z: NoIntervalo):
        y = z
        y_cor_original = y.cor

        if z.esq is self._nil:
            x = z.dir
            self._transplantar(z, z.dir)
        elif z.dir is self._nil:
            x = z.esq
            self._transplantar(z, z.esq)
        else:
            y = self._minimo(z.dir)
            y_cor_original = y.cor
            x = y.dir
            if y.pai is z:
                x.pai = y
            else:
                self._transplantar(y, y.dir)
                y.dir = z.dir
                y.dir.pai = y
            self._transplantar(z, y)
            y.esq = z.esq
            y.esq.pai = y
            y.cor = z.cor

        
        self._propagar_max_fim(x.pai)

        if y_cor_original == PRETO:
            self._corrigir_remocao(x)

    def _corrigir_remocao(self, x: NoIntervalo):
        while x is not self.raiz and x.cor == PRETO:
            if x is x.pai.esq:
                w = x.pai.dir
                if w.cor == VERMELHO:
                    w.cor = PRETO
                    x.pai.cor = VERMELHO
                    self._rotacao_esquerda(x.pai)
                    w = x.pai.dir
                if w.esq.cor == PRETO and w.dir.cor == PRETO:
                    w.cor = VERMELHO
                    x = x.pai
                else:
                    if w.dir.cor == PRETO:
                        w.esq.cor = PRETO
                        w.cor = VERMELHO
                        self._rotacao_direita(w)
                        w = x.pai.dir
                    w.cor = x.pai.cor
                    x.pai.cor = PRETO
                    w.dir.cor = PRETO
                    self._rotacao_esquerda(x.pai)
                    x = self.raiz
            else:
                w = x.pai.esq
                if w.cor == VERMELHO:
                    w.cor = PRETO
                    x.pai.cor = VERMELHO
                    self._rotacao_direita(x.pai)
                    w = x.pai.esq
                if w.dir.cor == PRETO and w.esq.cor == PRETO:
                    w.cor = VERMELHO
                    x = x.pai
                else:
                    if w.esq.cor == PRETO:
                        w.dir.cor = PRETO
                        w.cor = VERMELHO
                        self._rotacao_esquerda(w)
                        w = x.pai.esq
                    w.cor = x.pai.cor
                    x.pai.cor = PRETO
                    w.esq.cor = PRETO
                    self._rotacao_direita(x.pai)
                    x = self.raiz
        x.cor = PRETO


    def buscar_todos_sobrepostos(
        self,
        inicio: "date",
        fim: "date",
    ) -> "tuple[list[dict], int, int]":
       
        resultados = []
        visitados = [0]
        podados   = [0]

        def _busca(no):
            if no is self._nil:
                return

            visitados[0] += 1

            
            if no.max_fim < inicio:
                podados[0] += 1
                return

            # Verifica o nó atual
            if no.inicio <= fim and inicio <= no.fim:
                resultados.append(dict(no.dados))

            
            _busca(no.esq)

            
            if no.inicio <= fim:
                _busca(no.dir)

        _busca(self.raiz)
        return resultados, visitados[0], podados[0]

    

    def construir_de_emprestimos(self, emprestimos: dict):
        
        for chave, emp in emprestimos.items():
            inicio_str = emp.get("inicio")
            fim_str = emp.get("devolucao")
            if not inicio_str or not fim_str:
                continue
            try:
                inicio = date.fromisoformat(inicio_str)
                fim = date.fromisoformat(fim_str)
            except ValueError:
                continue
            dados = dict(emp)
            dados["chave"] = chave
            self.inserir(inicio, fim, dados)



if __name__ == "__main__":
    from datetime import date

    tree = RBTIntervalos()

    emprestimos = [
        (date(2024, 6, 1),  date(2024, 6, 10), {"chave": "001", "livro": "Duna"}),
        (date(2024, 6, 5),  date(2024, 6, 20), {"chave": "002", "livro": "1984"}),
        (date(2024, 6, 15), date(2024, 6, 25), {"chave": "003", "livro": "Hobbit"}),
        (date(2024, 7, 1),  date(2024, 7, 10), {"chave": "004", "livro": "Fundação"}),
    ]

    for ini, fim, d in emprestimos:
        tree.inserir(ini, fim, d)

    print("=== Consulta: 6/12 a 6/16 (deve conflitar) ===")
    c = tree.buscar_sobreposicao(date(2024, 6, 12), date(2024, 6, 16))
    print(f"  Conflito: {c['livro'] if c else 'nenhum'}")

    print("=== Consulta: 6/26 a 6/30 (sem conflito) ===")
    c = tree.buscar_sobreposicao(date(2024, 6, 26), date(2024, 6, 30))
    print(f"  Conflito: {c['livro'] if c else 'nenhum'}")

    print("=== Remover empréstimo 002 e checar 6/5 a 6/20 ===")
    tree.remover_por_chave("002")
    c = tree.buscar_sobreposicao(date(2024, 6, 5), date(2024, 6, 20))
    print(f"  Conflito após remoção: {c['livro'] if c else 'nenhum'}")
