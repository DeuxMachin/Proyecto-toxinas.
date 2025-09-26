# Carpeta `utils`

Utilidades transversales de bajo nivel y sin dependencias de la capa de dominio / casos de uso. Actualmente contiene la función de apoyo a exportaciones Excel.

## Contenido

| Archivo | Descripción |
|---------|-------------|
| `excel_export.py` | Generación estilizada de archivos Excel (múltiples hojas + metadatos) retornando un `BytesIO` listo para enviar vía HTTP. |

## `generate_excel`

```python
def generate_excel(data_dict, filename_prefix, sheet_names=None, metadata=None) -> (io.BytesIO, str)
```

### Parámetros
- `data_dict`: `dict[str, pd.DataFrame]` o directamente un `pd.DataFrame` único.
- `filename_prefix`: Prefijo del nombre de archivo (se agrega timestamp `YYYYMMDD_HHMMSS`).
- `sheet_names`: Lista opcional; si coincide en longitud con `data_dict` se reasignan los nombres.
- `metadata`: Diccionario opcional para generar una hoja adicional `Metadatos`.

### Retorno
Tuple `(buffer, filename)` donde:
- `buffer`: `io.BytesIO` posicionado al inicio listo para `send_file`.
- `filename`: Nombre final `"{prefix}_{timestamp}.xlsx"` (evita colisiones).

### Lógica Clave
1. Normaliza `data_dict` si es un único DataFrame → `{ "Data": df }`.
2. Sanitiza nombres de hoja (sin `/`, `\`, sólo alfanumérico, `_`, `-`, límite 31 chars Excel).
3. Crea hoja de metadatos (si procede) formateando cabeceras (color, negrita) y ancho de columnas.
4. Para cada hoja de datos ajusta cabecera (font bold blanca + fondo azul), alinea centro y auto-calcula ancho limitado (<= 40).
5. Devuelve buffer rebobinado (`seek(0)`).

### Estilos Aplicados
- Cabeceras: `Font(bold=True, color="FFFFFF")` sobre relleno `PatternFill(color 366092)`.
- Alineación centrada horizontal / vertical.
- Auto width por columna calculado por longitud máxima de las celdas + 2, con techo de 40.


## Razones de Diseño
- Separación para reutilizar el formateo sin duplicar lógica en controladores.
- Independiente de Flask → prueba unitaria aislada (verificar número de hojas, estilos, nombres).
- Timestamp en nombre de archivo facilita caching y auditoría.


## Principio Arquitectónico
`utils` no debe importar nada de `domain`, `application` o `infrastructure` para mantener direccionalidad (solo dependencias hacia librerías externas estándar / de terceros). 

