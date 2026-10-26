from typing import List, Optional

from sqlalchemy import func, or_
from sqlalchemy.orm import joinedload, selectinload

from app.db.models import STATUS_ATIVO, Classificacao, MovimentoContas, Pessoa
from app.repositories.base import BaseRepository
from app.schemas.cadastros import somente_digitos


class MovimentoRepository(BaseRepository[MovimentoContas]):
    model = MovimentoContas

    def query(self):
        return (
            super()
            .query()
            .options(
                joinedload(MovimentoContas.pessoa),
                joinedload(MovimentoContas.faturado),
                selectinload(MovimentoContas.classificacoes),
                selectinload(MovimentoContas.parcelas),
            )
        )

    def obter(self, id_: int) -> Optional[MovimentoContas]:
        return self.db.scalars(self.query().where(MovimentoContas.id == id_)).first()

    def listar(
        self,
        busca: Optional[str] = None,
        tipo: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[MovimentoContas]:
        stmt = self._filtrar_status(self.query(), status)
        if tipo:
            stmt = stmt.where(MovimentoContas.tipo == tipo.upper())
        if busca and busca.strip():
            termo = f"%{busca.strip().lower()}%"
            condicoes = [
                func.lower(MovimentoContas.numero_nota_fiscal).like(termo),
                func.lower(MovimentoContas.descricao).like(termo),
                MovimentoContas.pessoa.has(func.lower(Pessoa.razao_social).like(termo)),
                MovimentoContas.faturado.has(func.lower(Pessoa.razao_social).like(termo)),
                MovimentoContas.classificacoes.any(func.lower(Classificacao.descricao).like(termo)),
            ]
            digitos = somente_digitos(busca)
            if digitos:
                condicoes.append(MovimentoContas.pessoa.has(Pessoa.documento.like(f"%{digitos}%")))
            stmt = stmt.where(or_(*condicoes))
        return self._listar(stmt)

    def buscar_duplicado(self, tipo: str, numero_nota: Optional[str], pessoa_id: int) -> Optional[MovimentoContas]:
        """Movimento ATIVO com o mesmo nº de nota para a mesma pessoa (evita lançamento em dobro)."""
        if not numero_nota or not numero_nota.strip():
            return None
        stmt = self.query().where(
            MovimentoContas.tipo == tipo,
            MovimentoContas.numero_nota_fiscal == numero_nota.strip(),
            MovimentoContas.pessoa_id == pessoa_id,
            MovimentoContas.status == STATUS_ATIVO,
        )
        return self.db.scalars(stmt).first()
