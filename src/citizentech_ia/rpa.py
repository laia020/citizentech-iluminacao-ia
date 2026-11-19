"""Consulta das evidências históricas, compartilhada pelas aplicações de nuvem e desenvolvimento."""

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()


@router.get("/rpa", response_class=HTMLResponse, include_in_schema=False)
def rpa_page():
    return (Path(__file__).resolve().parent / "v5/rpa.html").read_text(encoding="utf-8")
