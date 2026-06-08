VERMELHO = True
PRETO = False

class NoLivro:
    def __init__(self, livro: dict):
        self.numeracao = int(livro["numeracao"])
        self.dados = dict(livro)
        self.esq = None
        self.dir = None
        self.pai = None
        self.cor = VERMELHO


class RBTBiblioteca:
    def __init__(self):
        self._nil = NoLivro({"numeracao": "0"})
        self._nil.cor = PRETO
        self._nil.esq = self._nil
        self._nil.dir = self._nil
        self._nil.pai = self._nil

        self.raiz = self._nil
        self.comparacoes = 0

    def _rotacao_esquerda(self, x: NoLivro):
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

    def _rotacao_direita(self, y: NoLivro):
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

    def inserir(self, livro: dict):
        if not livro:
            return

        numeracao = int(livro["numeracao"])

        pai = self._nil
        atual = self.raiz
        while atual is not self._nil:
            pai = atual
            if numeracao < atual.numeracao:
                atual = atual.esq
            elif numeracao > atual.numeracao:
                atual = atual.dir
            else:
                atual.dados = dict(livro)
                return

        novo = NoLivro(livro)
        novo.pai = pai
        novo.esq = self._nil
        novo.dir = self._nil
        novo.cor = VERMELHO

        if pai is self._nil:
            self.raiz = novo
        elif numeracao < pai.numeracao:
            pai.esq = novo
        else:
            pai.dir = novo

        self._corrigir_insercao(novo)

    def _corrigir_insercao(self, z: NoLivro):
        while z.pai.cor == VERMELHO:
            if z.pai is z.pai.pai.esq:
                tio = z.pai.pai.dir

                if tio.cor == VERMELHO:
                    z.pai.cor = PRETO
                    tio.cor = PRETO
                    z.pai.pai.cor = VERMELHO
                    z = z.pai.pai
                else:
                    if z is z.pai.dir:
                        z = z.pai
                        self._rotacao_esquerda(z)
                    z.pai.cor = PRETO
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

    def buscar(self, numeracao: int) -> dict | None:
        self.comparacoes = 0
        atual = self.raiz

        while atual is not self._nil:
            self.comparacoes += 1
            if numeracao == atual.numeracao:
                return atual.dados
            atual = atual.esq if numeracao < atual.numeracao else atual.dir

        return None

    def buscar_intervalo(self, inicio: int, fim: int) -> list[dict]:
        self.comparacoes = 0
        resultados = []

        def _buscar(no):
            if no is self._nil:
                return
            self.comparacoes += 1
            if no.numeracao > inicio:
                _buscar(no.esq)
            if inicio <= no.numeracao <= fim:
                resultados.append(no.dados)
            if no.numeracao < fim:
                _buscar(no.dir)

        _buscar(self.raiz)
        return resultados

    def remover(self, numeracao: int):
        z = self._buscar_no(numeracao)
        if z is self._nil:
            return
        self._remover_no(z)

    def _buscar_no(self, numeracao: int) -> NoLivro:
        atual = self.raiz
        while atual is not self._nil:
            if numeracao == atual.numeracao:
                return atual
            atual = atual.esq if numeracao < atual.numeracao else atual.dir
        return self._nil

    def _minimo(self, no: NoLivro) -> NoLivro:
        while no.esq is not self._nil:
            no = no.esq
        return no

    def _transplantar(self, u: NoLivro, v: NoLivro):
        if u.pai is self._nil:
            self.raiz = v
        elif u is u.pai.esq:
            u.pai.esq = v
        else:
            u.pai.dir = v
        v.pai = u.pai

    def _remover_no(self, z: NoLivro):
        y = z
        y_cor_original = y.cor
        x: NoLivro

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

        if y_cor_original == PRETO:
            self._corrigir_remocao(x)

    def _corrigir_remocao(self, x: NoLivro):
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

    def em_ordem(self) -> list[dict]:
        resultados = []

        def _em_ordem(no):
            if no is self._nil:
                return
            _em_ordem(no.esq)
            resultados.append(no.dados)
            _em_ordem(no.dir)

        _em_ordem(self.raiz)
        return resultados

    def construir_de_lista(self, livros: list[dict]):
        for livro in livros:
            self.inserir(livro)


if __name__ == "__main__":
    livros_teste = [
        {"numeracao": "0001", "titulo": "Livro A"},
        {"numeracao": "0002", "titulo": "Livro B"},
        {"numeracao": "0003", "titulo": "Livro C"},
        {"numeracao": "0004", "titulo": "Livro D"},
        {"numeracao": "0005", "titulo": "Livro E"},
    ]

    rbt = RBTBiblioteca()
    rbt.construir_de_lista(livros_teste)

    print("=== Inserção em ordem crescente (pior caso da BST) ===")
    print("Em ordem:", [l["titulo"] for l in rbt.em_ordem()])

    print("\n=== Busca exata: 3 ===")
    r = rbt.buscar(3)
    print(f"  Encontrado: {r['titulo'] if r else 'não encontrado'}, comparações: {rbt.comparacoes}")

    print("\n=== Busca intervalo 2-4 ===")
    rs = rbt.buscar_intervalo(2, 4)
    print(f"  {len(rs)} livros: {[l['titulo'] for l in rs]}")

    print("\n=== Remover 3 ===")
    rbt.remover(3)
    print("Em ordem após remoção:", [l["titulo"] for l in rbt.em_ordem()])