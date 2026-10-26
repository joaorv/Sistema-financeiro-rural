from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies import exigir_usuario
from app.schemas.analise import AnaliseResponse, LancamentoResponse
from app.schemas.invoice import ExtracaoNotaFiscalResponse
from app.services.lancamento_service import analisar_nota, lancar_nota

router = APIRouter(prefix="/api", tags=["Análise e Lançamento"], dependencies=[Depends(exigir_usuario)])


@router.post(
    "/analisar",
    response_model=AnaliseResponse,
    summary="Consulta no banco se Fornecedor, Faturado e Despesa da nota extraída já existem",
)
def analisar(nota: ExtracaoNotaFiscalResponse, db: Session = Depends(get_db)):
    return analisar_nota(db, nota)


@router.post(
    "/lancar",
    response_model=LancamentoResponse,
    status_code=201,
    summary="Cria o que não existe e lança o movimento de contas a pagar com suas parcelas",
)
def lancar(nota: ExtracaoNotaFiscalResponse, db: Session = Depends(get_db)):
    resultado = lancar_nota(db, nota)
    db.commit()  # tudo ou nada: em caso de erro antes daqui, a sessão é descartada sem gravar
    return resultado
