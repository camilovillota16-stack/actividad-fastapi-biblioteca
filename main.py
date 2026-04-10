from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List
from datetime import datetime

app = FastAPI(title="API Biblioteca UAO")

ANIO_ACTUAL = datetime.now().year


# =========================
# MODELOS
# =========================

class LibroBase(BaseModel):
    titulo: str = Field(..., min_length=1, description="Título del libro")
    autor: str = Field(..., min_length=1, description="Autor del libro")
    categoria: str = Field(..., min_length=1, description="Categoría del libro")
    anio_publicacion: int = Field(..., description="Año de publicación")
    total_ejemplares: int = Field(..., gt=0, description="Total de ejemplares")
    ejemplares_disponibles: int = Field(..., ge=0, description="Ejemplares disponibles")

    @field_validator("titulo", "autor", "categoria")
    @classmethod
    def validar_texto_no_vacio(cls, value: str):
        if not value.strip():
            raise ValueError("Este campo no puede estar vacío")
        return value

    @field_validator("anio_publicacion")
    @classmethod
    def validar_anio_publicacion(cls, value: int):
        if value > ANIO_ACTUAL:
            raise ValueError("El año de publicación no puede ser mayor al año actual")
        return value

    @model_validator(mode="after")
    def validar_ejemplares(self):
        if self.ejemplares_disponibles > self.total_ejemplares:
            raise ValueError("Los ejemplares disponibles no pueden ser mayores al total de ejemplares")
        return self


class LibroCrear(LibroBase):
    pass


class LibroActualizar(LibroBase):
    pass


class Libro(LibroBase):
    id: int


class LeyendoEntrada(BaseModel):
    persona: str = Field(..., min_length=1, description="Nombre de la persona")
    libros_ids: List[int] = Field(..., description="IDs de los libros que está leyendo")

    @field_validator("persona")
    @classmethod
    def validar_persona(cls, value: str):
        if not value.strip():
            raise ValueError("El nombre de la persona no puede estar vacío")
        return value


class LeyendoRespuesta(BaseModel):
    persona: str
    libros: List[Libro]


# =========================
# "BASE DE DATOS" EN MEMORIA
# =========================

libros: List[Libro] = []
leyendo_registros: List[LeyendoRespuesta] = []


# =========================
# FUNCIONES AUXILIARES
# =========================

def buscar_libro_por_id(libro_id: int) -> Libro:
    for libro in libros:
        if libro.id == libro_id:
            return libro
    raise HTTPException(status_code=404, detail="Libro no encontrado")


# =========================
# ENDPOINTS
# =========================

@app.get("/")
def inicio():
    return {"mensaje": "API Biblioteca UAO funcionando"}


# 1) POST /libros
@app.post("/libros", response_model=Libro, status_code=201)
def crear_libro(libro: LibroCrear):
    nuevo_id = len(libros) + 1

    nuevo_libro = Libro(
        id=nuevo_id,
        titulo=libro.titulo,
        autor=libro.autor,
        categoria=libro.categoria,
        anio_publicacion=libro.anio_publicacion,
        total_ejemplares=libro.total_ejemplares,
        ejemplares_disponibles=libro.ejemplares_disponibles,
    )

    libros.append(nuevo_libro)
    return nuevo_libro


# 2) GET /libros
@app.get("/libros", response_model=List[Libro])
def listar_libros():
    return libros


# 3) GET /libros/{id}
@app.get("/libros/{id}", response_model=Libro)
def obtener_libro(id: int):
    return buscar_libro_por_id(id)


# 4) PUT /libros/{id}
@app.put("/libros/{id}", response_model=Libro)
def actualizar_libro(id: int, datos_actualizados: LibroActualizar):
    libro_existente = buscar_libro_por_id(id)

    libro_existente.titulo = datos_actualizados.titulo
    libro_existente.autor = datos_actualizados.autor
    libro_existente.categoria = datos_actualizados.categoria
    libro_existente.anio_publicacion = datos_actualizados.anio_publicacion
    libro_existente.total_ejemplares = datos_actualizados.total_ejemplares
    libro_existente.ejemplares_disponibles = datos_actualizados.ejemplares_disponibles

    return libro_existente


# 5) DELETE /libros/{id}
@app.delete("/libros/{id}")
def eliminar_libro(id: int):
    libro_existente = buscar_libro_por_id(id)
    libros.remove(libro_existente)
    return {"mensaje": "Libro eliminado correctamente"}


# 6) POST /libros/{id}/prestar
@app.post("/libros/{id}/prestar", response_model=Libro)
def prestar_libro(id: int):
    libro = buscar_libro_por_id(id)

    if libro.ejemplares_disponibles <= 0:
        raise HTTPException(
            status_code=400,
            detail="No hay ejemplares disponibles para préstamo"
        )

    libro.ejemplares_disponibles -= 1
    return libro


# 7) ENDPOINT OBLIGATORIO EXTRA: LEYENDO
@app.post("/leyendo", response_model=LeyendoRespuesta, status_code=201)
def registrar_leyendo(data: LeyendoEntrada):
    libros_encontrados: List[Libro] = []

    for libro_id in data.libros_ids:
        libro = buscar_libro_por_id(libro_id)
        libros_encontrados.append(libro)

    registro = LeyendoRespuesta(
        persona=data.persona,
        libros=libros_encontrados
    )

    leyendo_registros.append(registro)
    return registro


# OPCIONAL: ver registros de leyendo
@app.get("/leyendo", response_model=List[LeyendoRespuesta])
def listar_leyendo():
    return leyendo_registros