from typing import Generic, List, Optional, Type, TypeVar

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.db.models import STATUS_ATIVO, STATUS_INATIVO

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """
    Operações comuns a todos os cadastros.
    Regra de negócio: nenhum registro é excluído fisicamente; "excluir" = INATIVAR.
    Os repositórios fazem apenas flush; o commit fica a cargo de quem chama
    (rota ou service), permitindo agrupar várias operações em uma transação.
    """

    model: Type[T]

    def __init__(self, db: Session):
        self.db = db

    def obter(self, id_: int) -> Optional[T]:
        return self.db.get(self.model, id_)

    def _filtrar_status(self, stmt: Select, status: Optional[str]) -> Select:
        # status: "ATIVO" (padrão), "INATIVO" ou "TODOS"
        status = (status or STATUS_ATIVO).upper()
        if status in (STATUS_ATIVO, STATUS_INATIVO):
            stmt = stmt.where(self.model.status == status)
        return stmt

    def _listar(self, stmt: Select) -> List[T]:
        return list(self.db.scalars(stmt.order_by(self.model.id)).unique())

    def adicionar(self, obj: T) -> T:
        self.db.add(obj)
        self.db.flush()
        return obj

    def inativar(self, obj: T) -> T:
        obj.status = STATUS_INATIVO
        self.db.flush()
        return obj

    def reativar(self, obj: T) -> T:
        obj.status = STATUS_ATIVO
        self.db.flush()
        return obj

    def query(self) -> Select:
        return select(self.model)
