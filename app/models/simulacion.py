from datetime import datetime, timezone
from app.extensions import db


class Simulacion(db.Model):
    __tablename__ = "simulaciones"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    caso_id = db.Column(
        db.String(36),
        unique=True,
        nullable=False
    )

    conversation_id = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    escenario = db.Column(
        db.String(100),
        nullable=False
    )

    caso_clinico = db.Column(
        db.JSON,
        nullable=False
    )

    estado = db.Column(
        db.String(30),
        nullable=False,
        default="creada"
    )

    fecha_creacion = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )