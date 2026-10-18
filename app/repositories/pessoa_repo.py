from typing import List, Optional

from sqlalchemy import func, or_

from app.db.models import Pessoa
from app.repositories.base import BaseRepository
from app.schemas.cadastros import somente_digitos


class PessoaRepository(BaseRepository[Pessoa]):
    model = Pessoa

    def listar(
        self,
        busca: Optional[str] = None,
        tipo: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Pessoa]:
        stmt = self._filtrar_status(self.query(), status)
        if tipo:
            stmt = stmt.where(Pessoa.tipo == tipo.upper())
        if busca and busca.strip():
            termo = f"%{busca.strip().lower()}%"
            condicoes = [
                func.lower(Pessoa.razao_social).like(termo),
                func.lower(Pessoa.fantasia).like(termo),
            ]
            digitos = somente_digitos(busca)
            if digitos:
                condicoes.append(Pessoa.documento.like(f"%{digitos}%"))
            stmt = stmt.where(or_(*condicoes))
        return self._listar(stmt)

    def buscar_por_documento(self, documento: Optional[str], tipo: str) -> Optional[Pessoa]:
        documento = somente_digitos(documento)
        if not documento:
            return None
        stmt = self.query().where(Pessoa.documento == documento, Pessoa.tipo == tipo)
        return self.db.scalars(stmt.order_by(Pessoa.id)).first()

    def buscar_por_nome(self, nome: Optional[str], tipo: str) -> Optional[Pessoa]:
        """Usado quando a nota não traz documento (ex.: cupom sem CPF)."""
        if not nome or not nome.strip():
            return None
        stmt = self.query().where(
            func.lower(Pessoa.razao_social) == nome.strip().lower(), Pessoa.tipo == tipo
        )
        return self.db.scalars(stmt.order_by(Pessoa.id)).first()

    def documento_em_uso(self, documento: Optional[str], tipo: str, ignorar_id: Optional[int] = None) -> bool:
        existente = self.buscar_por_documento(documento, tipo)
        return bool(existente and existente.id != ignorar_id)
