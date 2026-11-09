# RAMTable

RAMTable es una biblioteca pequeña y sin dependencias externas para crear y
manipular tablas tipadas en memoria. Define un esquema de columnas, valida las
filas en tiempo de ejecución y ofrece operaciones para insertar, consultar,
actualizar y eliminar registros.

> RAMTable mantiene los datos únicamente en memoria: no implementa persistencia
> en disco ni consultas SQL.

## Requisitos

- Python 3.10 o posterior.

## Instalación

Desde una copia local del repositorio:

```bash
python -m pip install .
```

Para desarrollar en el repositorio y que los cambios se reflejen sin reinstalar:

```bash
python -m pip install --editable .
```

## Inicio rápido

```python
from ramtable import Table

people = Table(
    name="people",
    columns={
        "id": int,
        "name": str,
        "age": int,
    },
)

people.rows.insert({"id": 1, "name": "Ada", "age": 36})
people.rows.insert({"id": 2, "name": "Linus", "age": 28})

print(people.rows.get_column("name"))
# ['Ada', 'Linus']

updated = people.rows.update(
    where={"id": 1},
    values={"name": "Ada Lovelace"},
)
print(updated)
# 1

print(people.rows.get_one(0))
# {'id': 1, 'name': 'Ada Lovelace', 'age': 36}
```

Cada fila debe ser un diccionario con exactamente los nombres de columna del
esquema. `insert` valida la estructura y los tipos antes de almacenar una copia
superficial del diccionario.

## Tipos de columna

Se aceptan clases de Python (por ejemplo, `int` y `str`), `Any`, `None`,
`Annotated`, uniones (`str | None` o `Union[...]`), `Literal`, y las
anotaciones parametrizadas de listas, conjuntos, diccionarios, secuencias,
conjuntos abstractos y tuplas. También se aceptan `type[T]` y tuplas de tamaño
fijo o variable. `TypeValidator` implementa y expone la validación de estas
anotaciones en tiempo de ejecución.

La comprobación de clases simples usa `isinstance`; por ello, `bool` también
se considera compatible con `int`, siguiendo el comportamiento de Python. Las
anotaciones `Literal` comparan tanto el valor como su tipo exacto.

## Operaciones

### Tabla

- `Table(name, columns)`: crea una tabla con nombre no vacío y al menos una
  columna.
- `table.clear()`: elimina todas las filas y conserva el esquema.
- `len(table)`: devuelve la cantidad de filas.

El esquema y las filas se gestionan mediante `table.columns` y `table.rows`.

### Columnas (`table.columns`)

- `add(name, column_type, default=...)`: agrega una columna. Si ya hay filas,
  exige un valor predeterminado compatible y crea una copia profunda del
  predeterminado para cada fila. No se puede agregar un nombre duplicado.
- `remove(name)`: elimina la columna y su valor de todas las filas. No permite
  eliminar la última columna.
- `update(name, new_type)`: cambia la anotación si todos los valores existentes
  son compatibles; no convierte los datos.
- `get(name)`: devuelve el tipo de una columna.
- `get_all()`: devuelve una copia del diccionario del esquema.
- `name in table.columns` y `len(table.columns)`: consultan pertenencia y
  cantidad de columnas.

### Filas (`table.rows`)

- `insert(row)`: valida e inserta una fila.
- `remove(row)`: valida y elimina la primera fila igual a la indicada.
- `update(where, values)`: actualiza todos los registros que coinciden con las
  condiciones de igualdad y devuelve la cantidad modificada. Los valores que
  se asignan se validan contra el esquema; los valores de condición no.
- `get()`: devuelve todas las filas; `get(index, ...)` devuelve las filas en
  los índices solicitados.
- `get_one(index)`: devuelve una fila por índice.
- `get_all()`: devuelve todas las filas.
- `get_columns(*names)`: devuelve las columnas seleccionadas como listas; sin
  argumentos, incluye todas las columnas.
- `get_column(name)`: devuelve los valores de una columna.
- `clear()`: elimina todas las filas.
- `len(table.rows)` e iterar `table.rows`: consultan la cantidad e iteran sobre
  las filas.

Los índices aceptan valores negativos como las listas de Python, pero no
aceptan `bool`.

## Copias y mutabilidad

Las operaciones que devuelven filas crean nuevos diccionarios, pero las copias
son superficiales. Las listas y los diccionarios devueltos para columnas
también son nuevos, aunque sus valores no se copian. Por lo tanto, si una celda
contiene un objeto mutable, ese objeto puede seguir compartido entre la tabla y
el código que lo obtuvo.

## Errores

RAMTable informa los usos inválidos mediante excepciones estándar:

- `ValueError` para nombres, columnas o estructuras inexistentes/no válidos.
- `TypeError` para tipos de anotación, filas o valores incompatibles.
- `IndexError` para índices de fila fuera de rango.

## API pública

El paquete exporta `Table`, `Columns` y `Rows` desde `ramtable`. La clase
`TypeValidator` está disponible en `ramtable.types` para inspeccionar el
soporte de anotaciones y comprobar valores. La descripción completa de cada
método y sus excepciones está en los docstrings del código fuente.

## Licencia

Este proyecto se distribuye bajo la licencia MIT. Consulta [LICENSE](LICENSE).
# ramtable_py
# ramtable_py
