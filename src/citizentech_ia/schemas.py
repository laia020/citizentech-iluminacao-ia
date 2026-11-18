from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False, str_strip_whitespace=True)


class Sensor(Strict):
    tipo: str = Field(min_length=1, max_length=80)
    valor: float
    unidade: str = Field(min_length=1, max_length=40)
    calibrado: bool
    referencia_calibracao: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def calibration(self):
        if self.calibrado and not self.referencia_calibracao:
            raise ValueError("Sensor declarado calibrado exige referência de calibração.")
        return self


class Visual(Strict):
    descricao: str = Field(min_length=1, max_length=500)
    confianca: float | None = Field(default=None, ge=0, le=1)


class Occurrence(Strict):
    ocorrencia_id: str = Field(min_length=1, max_length=128)
    pergunta: str = Field(min_length=1, max_length=2000)
    municipio: str | None = Field(default=None, max_length=120)
    observado_em: datetime | None = None
    simulada: bool
    relato: str = Field(default="", max_length=4000)
    sensores: list[Sensor] = Field(default_factory=list, max_length=20)
    observacoes_visuais: list[Visual] = Field(default_factory=list, max_length=20)

    @field_validator("observado_em")
    @classmethod
    def timezone(cls, value):
        if value and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("Data/hora exige offset explícito.")
        return value

    @model_validator(mode="after")
    def evidence(self):
        if not (self.relato or self.sensores or self.observacoes_visuais):
            raise ValueError("Informe pelo menos uma observação.")
        return self


class Hypothesis(Strict):
    descricao: str = Field(min_length=1, max_length=800)
    evidencias_observadas: list[str] = Field(min_length=1, max_length=20)
    fontes: list[str] = Field(min_length=1, max_length=3)


class Analysis(Strict):
    status: Literal["analise_preliminar", "informacao_insuficiente", "fora_escopo"]
    resumo: str = Field(min_length=1, max_length=2000)
    hipoteses: list[Hypothesis] = Field(max_length=10)
    informacoes_faltantes: list[str] = Field(max_length=20)
    encaminhamento: str = Field(min_length=1, max_length=2000)
    fontes: list[str] = Field(max_length=3)


class Reference(Strict):
    chunk_id: str
    document_id: str
    title: str
    url: str | None = None


class Execution(Strict):
    modo: Literal["base_sem_contexto", "rag_simples", "rag_finetuning"]
    modelo: str
    revisao_modelo: str | None = None
    adaptador: str | None = None
    versao_base: str
    duracao_ms: int = Field(ge=0)


class AnalysisResponse(Strict):
    request_id: str
    ocorrencia_id: str
    analise: Analysis
    referencias: list[Reference]
    execucao: Execution


class ErrorResponse(Strict):
    request_id: str
    codigo: str
    mensagem: str
