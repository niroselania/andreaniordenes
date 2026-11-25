# Planilla de órdenes

App web que recibe el export de órdenes (.xlsx), elimina las filas que no hay que preparar, guarda el resultado y lo muestra a cualquiera que abra la página, con botón para descargarlo en el mismo formato. Cada reporte nuevo reemplaza al anterior.

El último reporte se guarda en el volumen Docker `planilla-data` (`/data`), así que sobrevive a reinicios y redeploys.

## Reglas
| Columna | Se conserva solo si |
|---|---|
| EO `Line: Type` | es "Line Item" o "Shipping Line" |
| N `Cancelled At` | está vacía |
| CB `Payment: Status` | es "paid" |
| CC `Order Fulfillment Status` | no contiene "on hold" |
| FP `Line: Gift Card` | no es VERDADERO/TRUE |

Las columnas se buscan por encabezado; si no se encuentra, se usa la letra.

## Deploy en Portainer
Stacks → Add stack → Repository → URL del repo, compose path `docker-compose.yml` → Deploy.
Abrir `http://<servidor>:8085`.
