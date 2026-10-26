from typing import List, Optional

from sqlalchemy import func

from app.db.models import Classificacao
from app.repositories.base import BaseRepository


def normalizar_descricao(descricao: str) -> str:
    return " ".join((descricao or "").split()).upper()


class ClassificacaoRepository(BaseRepository[Classificacao]):
    model = Classificacao

    def listar(
        self,
        busca: Optional[str] = None,
        tipo: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Classificacao]:
        stmt = self._filtrar_status(self.query(), status)
        if tipo:
            stmt = stmt.where(Classificacao.tipo == tipo.upper())
        if busca and busca.strip():
            stmt = stmt.where(func.lower(Classificacao.descricao).like(f"%{busca.strip().lower()}%"))
        return self._listar(stmt)

    def buscar_por_descricao(self, descricao: str, tipo: str) -> Optional[Classificacao]:
        # As descrições são gravadas sempre normalizadas (maiúsculas, espaços simples)
        stmt = self.query().where(
            Classificacao.descricao == normalizar_descricao(descricao), Classificacao.tipo == tipo
        )
        return self.db.scalars(stmt.order_by(Classificacao.id)).first()

    def listar_por_ids(self, ids: List[int]) -> List[Classificacao]:
        if not ids:
            return []
        return list(self.db.scalars(self.query().where(Classificacao.id.in_(ids))))
