import os

from fastapi.templating import Jinja2Templates


def prepare_jinja(templates: Jinja2Templates):
    templates.env.globals['v'] = os.environ.get('VERSION')
    templates.env.globals['crm_name'] = os.environ.get('CRM_NAME')

    templates.env.globals['get_servico'] = get_servico
    templates.env.globals['get_cliente'] = get_cliente
    templates.env.globals['get_profissional'] = get_profissional
    templates.env.globals['get_servicos_string'] = get_servicos_string


def get_servico(service_id: int):
    from app.database import SessionLocal
    from app.models.servico import Servico

    db = SessionLocal()
    try:
        servico = db.query(Servico).filter(Servico.id == service_id).first()
        if servico:
            return servico

        return Servico(
            name='Serviço não encontrado',
            price=0,
            description='Serviço não encontrado',
            minutes=0,
            sexo='Indiferente'
        )
    finally:
        db.close()


def get_servicos_string(service_ids: list[int]):
    from app.database import SessionLocal
    from app.models.servico import Servico

    db = SessionLocal()
    try:
        servicos = db.query(Servico).filter(Servico.id.in_(service_ids)).all()
        if servicos:
            return ', '.join([servico.name for servico in servicos])

        return 'Serviço não encontrado'
    finally:
        db.close()


def get_cliente(cliente_id: int):
    from app.database import SessionLocal
    from app.models.cliente import Cliente

    db = SessionLocal()
    try:
        cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
        if cliente:
            return cliente

        return Cliente(
            name='Cliente não encontrado',
            email='Cliente não encontrado',
            phone='Cliente não encontrado',
        )
    finally:
        db.close()


def get_profissional(profissional_id: int):
    from app.database import SessionLocal
    from app.models.profissional import Profissional

    db = SessionLocal()
    try:
        profissional = db.query(Profissional).filter(Profissional.id == profissional_id).first()
        if profissional:
            return profissional

        return Profissional(
            name='Profissional não encontrado',
        )
    finally:
        db.close()
