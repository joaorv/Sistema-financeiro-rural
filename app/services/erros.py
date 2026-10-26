class RegraNegocioError(Exception):
    """Violação de regra de negócio. Convertida em resposta HTTP pelo handler do main.py."""

    def __init__(self, mensagem: str, status_code: int = 400):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.status_code = status_code
